"""Behavioral checks for chess rules, signs, budgets, and search accounting."""

from itertools import count
import unittest
from unittest.mock import patch

import chess

from src.evaluation import MATE_SCORE, evaluate, material_reward, material_score
from src.minimax import minimax
from src.mcts import _Node, _uct_value, mcts


MATE_IN_ONE = "7k/8/5KQ1/8/8/8/8/8 w - - 0 1"
CHECKMATE = "7k/6Q1/5K2/8/8/8/8/8 b - - 0 1"
STALEMATE = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"


class SearchTests(unittest.TestCase):
    def test_material_sign_and_bounded_reward(self):
        board = chess.Board(MATE_IN_ONE)
        self.assertEqual(material_score(board), 9.0)
        self.assertEqual(material_score(board.mirror()), -9.0)
        self.assertGreater(material_reward(board), 0.5)
        self.assertLess(material_reward(board), 1.0)
        self.assertAlmostEqual(material_reward(board) + material_reward(board.mirror()), 1.0)

    def test_plain_minimax_exhaustively_counts_starting_tree(self):
        board = chess.Board()
        # Established starting-position perft counts: 20 one-ply, 400 two-ply.
        # The algorithm also counts internal nodes and the root.
        for depth, count in [(1, 21), (2, 421)]:
            result = minimax(board, depth)
            self.assertEqual(result.nodes, count)
            self.assertEqual(result.score, 0.0)
            self.assertTrue(result.completed)
            self.assertIn(result.move, board.legal_moves)

    def test_minimax_finds_mate_for_either_color(self):
        for board, score in [(chess.Board(MATE_IN_ONE), MATE_SCORE),
                             (chess.Board(MATE_IN_ONE).mirror(), -MATE_SCORE)]:
            result = minimax(board, 1)
            self.assertEqual(result.score, score)
            self.assertIn(result.move, board.legal_moves)
            board.push(result.move)
            self.assertTrue(board.is_checkmate())

    def test_terminal_mate_stalemate_insufficient_material_and_75_move(self):
        positions = [
            (CHECKMATE, MATE_SCORE, 1.0),
            (STALEMATE, 0.0, 0.5),
            ("8/8/8/8/8/4k3/8/4K3 w - - 0 1", 0.0, 0.5),
            ("8/8/8/8/8/4k3/8/R3K3 w - - 150 80", 0.0, 0.5),
        ]
        for fen, score, reward in positions:
            with self.subTest(fen=fen):
                board = chess.Board(fen)
                self.assertTrue(board.is_valid())
                self.assertIsNotNone(board.outcome(claim_draw=False))
                result = minimax(board, 2)
                self.assertIsNone(result.move)
                self.assertEqual(result.score, score)
                self.assertEqual(result.nodes, 1)
                self.assertTrue(result.completed)
                simulation = mcts(board, 10)
                self.assertIsNone(simulation.move)
                self.assertEqual(simulation.score, reward)
                self.assertEqual(simulation.iterations, 0)
                self.assertTrue(simulation.completed)
                self.assertEqual(evaluate(board), score)

    def test_optional_draw_claims_are_distinct_from_automatic_draws(self):
        board = chess.Board()
        cycle = ("g1f3", "g8f6", "f3g1", "f6g8")
        for _ in range(2):
            for move in cycle:
                board.push_uci(move)
        self.assertTrue(board.can_claim_threefold_repetition())
        self.assertIsNone(board.outcome(claim_draw=False))
        self.assertIsNotNone(minimax(board, 1).move)
        self.assertIsNotNone(mcts(board, 2, rollout_plies=0).move)
        for _ in range(2):
            for move in cycle:
                board.push_uci(move)
        self.assertTrue(board.is_fivefold_repetition())
        self.assertIsNone(minimax(board, 1).move)
        self.assertIsNone(mcts(board, 2).move)

    def test_searches_preserve_input_board_and_history(self):
        board = chess.Board()
        board.push_uci("e2e4")
        board.push_uci("e7e5")
        before = board.fen(), tuple(board.move_stack)
        minimax(board, 2)
        self.assertEqual((board.fen(), tuple(board.move_stack)), before)
        mcts(board, 30, seed=4, rollout_plies=6)
        self.assertEqual((board.fen(), tuple(board.move_stack)), before)

    def test_mcts_seed_legality_and_accounting(self):
        board = chess.Board()
        first = mcts(board, 45, seed=17, rollout_plies=6)
        second = mcts(board, 45, seed=17, rollout_plies=6)
        self.assertEqual(first, second)
        self.assertIn(first.move, board.legal_moves)
        self.assertEqual(first.iterations, 45)
        self.assertEqual(sum(item.visits for item in first.root_visits), 45)
        self.assertEqual(first.cutoff_rollouts + first.terminal_rollouts, 45)
        self.assertLessEqual(first.rollout_plies, 45 * 6)
        self.assertLessEqual(first.nodes, 46)
        self.assertTrue(first.completed)
        self.assertTrue(0.0 <= first.score <= 1.0)

    def test_uct_opponent_prefers_its_own_reward(self):
        # Equal exploration terms isolate which player maximizes exploitation.
        for turn in (chess.WHITE, chess.BLACK):
            board = chess.Board()
            board.turn = turn
            parent = _Node(board, visits=20)
            good_for_white = _Node(board.copy(), visits=10, reward_sum=8.0)
            good_for_black = _Node(board.copy(), visits=10, reward_sum=2.0)
            white_value = _uct_value(parent, good_for_white)
            black_value = _uct_value(parent, good_for_black)
            if turn == chess.WHITE:
                self.assertGreater(white_value, black_value)
            else:
                self.assertLess(white_value, black_value)

    def test_zero_second_budget_is_legal_and_explicitly_incomplete(self):
        board = chess.Board()
        for result in (minimax(board, 3, max_seconds=0),
                       mcts(board, 40, max_seconds=0)):
            self.assertIn(result.move, board.legal_moves)
            self.assertFalse(result.completed)
        self.assertEqual(mcts(board, 40, max_seconds=0).iterations, 0)

    def test_interrupted_search_preserves_board_and_excludes_partial_rollout(self):
        board = chess.Board()
        before = board.fen(), tuple(board.move_stack)
        # A deterministic fake clock interrupts inside work, not just at root.
        ticks = count(0.0, 0.001)
        with patch("src.minimax.perf_counter", side_effect=lambda: next(ticks)):
            result = minimax(board, 3, max_seconds=0.02)
        self.assertFalse(result.completed)
        self.assertGreater(result.nodes, 1)
        self.assertIn(result.move, board.legal_moves)
        self.assertEqual((board.fen(), tuple(board.move_stack)), before)
        ticks = count(0.0, 0.001)
        with patch("src.mcts.perf_counter", side_effect=lambda: next(ticks)):
            result = mcts(board, 100, rollout_plies=6, max_seconds=0.02)
        self.assertFalse(result.completed)
        self.assertGreater(result.iterations, 0)
        self.assertLess(result.iterations, 100)
        self.assertEqual(sum(item.visits for item in result.root_visits), result.iterations)
        self.assertEqual(result.terminal_rollouts + result.cutoff_rollouts, result.iterations)
        self.assertEqual((board.fen(), tuple(board.move_stack)), before)

    def test_invalid_arguments_fail_clearly(self):
        board = chess.Board()
        for depth in (0, -1, 1.5):
            with self.assertRaises(ValueError):
                minimax(board, depth)
        for budget in (0, -1, 1.5):
            with self.assertRaises(ValueError):
                mcts(board, budget)
        with self.assertRaises(ValueError):
            mcts(board, 10, rollout_plies=-1)
        for function, budget in ((minimax, 1), (mcts, 1)):
            with self.assertRaises(ValueError):
                function(board, budget, max_seconds=-1)
            with self.assertRaises(ValueError):
                function(chess.Board.empty(), budget)


if __name__ == "__main__":
    unittest.main()
