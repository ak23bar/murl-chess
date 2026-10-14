"""Manual square-by-square transcription of the rendered corrected PDF.

Uppercase = White; lowercase = Black. No expected moves are supplied here.
Castling and en-passant history are not stated in diagrams: no rights assumed.
Cases 1 and 4 additionally require sensitivity checks for Black kq rights.
"""
import chess

# Read visually from pages 1-4, with files a-h left to right and rank 8 at top.
RAW = [
('Immortal Game', 'Ke2 Qf3 Bd6 Nd5 Nf5 Pa2 Pc2 Pd3 Pe5 Pg4 Ph5', 'ke8 qa1 ra8 rh8 bc8 bg1 na6 ng8 pa7 pb5 pd7 pf7 pg7 ph7'),
('Evergreen Game', 'Kg1 Rd1 Ba3 Bd3 Pa2 Pc3 Pf2 Pf6 Pg2 Ph2', 'kd7 qf3 rb8 rg8 bb7 bb6 ne7 pa7 pc7 pf7 ph7'),
('Game of the Century', 'Kc1 Qb8 Ne5 Pg2 Ph4', 'kg7 ra2 bb4 bb3 ng3 pb5 pc6 pf7 pg6 ph5'),
('Reti Mate', 'Kc1 Qd3 Rd1 Rh1 Bd2 Bf1 Ng1 Pa2 Pb2 Pc2 Pf2 Pg2 Ph2', 'ke8 qe5 ra8 rh8 bc8 bf8 nb8 ne4 pa7 pb7 pc6 pf7 pg7 ph7'),
('Loyd Charles XII', 'Kf5 Rg7 Ne1 Pg2 Ph2', 'kh5 bf2 pg3 ph6'),
('Back-Rank Queen Sacrifices', 'Kg1 Qd7 Ph2', 'kh8 re6 rd2 pg7 ph7'),
('Back-Rank Quiet Knight', 'Kh1 Qd3 Re1 Nh3', 'kh8 rg8 pg7 ph7'),
('Queen Sacrifice Knight Support', 'Kc1 Qf7 Rf2 Nc8', 'kh8 rg8 pg7 ph7'),
('Rook Sacrifice Long Diagonal', 'Kg1 Qh6 Rb8 Nd7', 'kh8 rg8 pg7 ph7'),
('Rook Sacrifice Queen Knight', 'Kb1 Qd6 Re8 Nf5', 'kh7 pc4 pg7 ph2'),
('Anastasia Mate', 'Kg1 Qe5 Rd4 Nc8 Pf2 Pg2', 'kg8 qb4 rb8 pf7 pg7'),
('Arabian Mate', 'Ka1 Qa7 Rf7 Ng8', 'kh7 ng3 pg7'),
('Arabian Rook Lift', 'Ke1 Rd7 Ne4', 'kh8 nc8 nd1 pd6'),
('Smothered Mate', 'Kg1 Qe5 Nb5 Ph6', 'kh8 rg8 bh4 pg7 ph7 pg4'),
('Double-Check Mate', 'Kg1 Qf5 Ra3 Bd8 Pf2 Pg2 Ph2', 'kg8 ra8 pf7 pg7 ph7'),
('Promotion Mate', 'Kg3 Rf1 Pb7', 'kh8 pg6'),
('Double Promotion', 'Kg2 Rf6 Pa7 Pd7', 'kg8 bg5'),
('Under-Promotion Rook', 'Ka1 Rg1 Nd8 Pc7', 'ke8 bg7'),
('Under-Promotion Bishop', 'Kf3 Qc4 Pd6 Ph7', 'kg7 na7'),
('Promotion Sacrifice Queen Pawn', 'Kg3 Ra6 Pc7 Ph6', 'kh8 ba7 nd7'),
]

def positions():
    rows = []
    for i, (name, white, black) in enumerate(RAW, 1):
        board = chess.Board(None)
        for token in (white+' '+black).split():
            sq = chess.parse_square(token[1:])
            assert board.piece_at(sq) is None
            board.set_piece_at(sq, chess.Piece.from_symbol(token[0]))
        board.turn = i != 3
        rows.append(dict(id=i, name=name, page=1 if i<=4 else 2 if i<=10 else 3 if i<=16 else 4,
                         white=white, black=black, fen=board.fen(), valid=board.is_valid(),
                         validity_status=int(board.status())))
    return rows
