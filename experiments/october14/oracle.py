"""Independent exact bounded AND/OR mate solver; does not import src searches.

Attacker nodes are OR, defender nodes AND. All legal root moves are tested.
Checks are ordered first, but quiet moves and all promotions remain included.
Only checkmate is success: material advantages and stalemate never suffice.
Short-circuiting proves logical truth/falsity; it is not a heuristic cutoff.
Memoization includes placement, turn, rights, ep and halfmove clock. At <=5
plies from a history-free FEN, fivefold repetition cannot occur. The input's
earlier history is intentionally unavailable, as in the benchmark.
"""
import time
import chess

class OracleTimeout(Exception):
    pass

def solve(board, plies=5, max_seconds=120):
    if not board.is_valid():
        raise ValueError('invalid board')
    if not isinstance(plies, int) or plies < 1 or plies > 5:
        raise ValueError('plies must be 1 through 5')
    if board.move_stack:
        raise ValueError('oracle expects a history-free FEN')
    start = time.perf_counter()
    deadline = start + max_seconds
    attacker = board.turn
    b = board.copy()
    memo = {}
    nodes = 0
    def win(left):
        nonlocal nodes
        nodes += 1
        if time.perf_counter() >= deadline:
            raise OracleTimeout()
        if b.is_checkmate():
            return b.turn != attacker
        if left == 0 or b.is_stalemate() or b.is_insufficient_material() or b.is_seventyfive_moves():
            return False
        key = (b._transposition_key(), b.halfmove_clock, left)
        if key in memo:
            return memo[key]
        is_attacker = b.turn == attacker
        moves = list(b.legal_moves)
        if is_attacker:
            moves.sort(key=b.gives_check, reverse=True)
        result = not is_attacker
        for move in moves:
            b.push(move)
            try:
                child = win(left-1)
            finally:
                b.pop()
            if child == is_attacker:
                result = is_attacker
                break
        memo[key] = result
        return result
    winners, tested, complete = [], [], True
    try:
        for move in list(b.legal_moves):
            b.push(move)
            try:
                yes = win(plies-1)
            finally:
                b.pop()
            tested.append(move.uci())
            if yes:
                winners.append(move.uci())
    except OracleTimeout:
        complete = False
    return dict(plies=plies, completed=complete, winning_moves=winners,
                winning_san=[board.san(chess.Move.from_uci(m)) for m in winners],
                tested_root_moves=tested, legal_root_count=board.legal_moves.count(),
                nodes=nodes, seconds=time.perf_counter()-start)
