import unittest
import chess
from experiments.october14.positions import positions
from experiments.october14.oracle import solve
from src.minimax import minimax
from src.evaluation import MATE_SCORE
from experiments.october14.certificates import check

class OctoberTests(unittest.TestCase):
    def test_certificate_checker_rejects_missing_defense_and_false_mate(self):
        b=chess.Board()
        with self.assertRaises(AssertionError):
            check(b,{'mate':True},chess.WHITE,5)
        b.push_uci('e2e4')
        with self.assertRaises(AssertionError):
            check(b,{'moves':{'e7e5':{'mate':True}}},chess.WHITE,4)

    def test_transcriptions(self):
        rows = positions()
        self.assertEqual(len(rows),20)
        for p in rows:
            self.assertTrue(p['valid'], p)
            self.assertEqual(chess.Board(p['fen']).turn,p['id']!=3)

    def test_oracle_both_colors_and_input_preserved(self):
        b = chess.Board('7k/8/5KQ1/8/8/8/8/8 w - - 0 1')
        for b in (b,b.mirror()):
            before = b.fen()
            r = solve(b,1)
            self.assertTrue(r['completed'])
            expected=[]
            for m in b.legal_moves:
                c=b.copy(); c.push(m)
                if c.is_checkmate(): expected.append(m.uci())
            self.assertEqual(r['winning_moves'],expected)
            self.assertEqual(b.fen(),before)

    def test_stalemate_and_timeout_are_not_mate_proofs(self):
        b=chess.Board('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
        self.assertEqual(solve(b,3)['winning_moves'],[])
        r=solve(chess.Board(),5,0)
        self.assertFalse(r['completed'])
        self.assertEqual(r['tested_root_moves'],[])

    def test_oracle_matches_full_minimax_at_three_plies(self):
        # Independent score recursion agrees with the AND/OR root existence.
        for p in positions()[4:9]:
            b=chess.Board(p['fen'])
            oracle=solve(b,3)
            result=minimax(b,3)
            self.assertTrue(oracle['completed'])
            self.assertEqual(bool(oracle['winning_moves']),result.score==MATE_SCORE)

if __name__=='__main__': unittest.main()
