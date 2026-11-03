"""Replay the supplied solution pages and archived strategy certificates."""
import argparse
import csv
import json
import re
from pathlib import Path

import chess
from pypdf import PdfReader
from experiments.october14.certificates import check
from experiments.october14.oracle import solve

ROOT = Path("deliverables/october14")
NOV = Path("deliverables/november05")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    booklet = PdfReader(NOV / "sources/Positions2withSolutions.pdf")
    glyphs = json.loads((ROOT / "source/extracted_board_glyphs.json").read_text())
    for page, old in zip(booklet.pages[:4], glyphs, strict=True):
        assert re.findall(r"(?m)^([1-8]) ([A-Za-z0-9]{8})$", page.extract_text()) == [tuple(row) for row in old]
    lines = {}
    for page in booklet.pages[4:]:
        for line in page.extract_text().splitlines():
            match = re.match(r"^(\d+)\..*?\.1\.(?:\.\.)?\s*(.*#)", line)
            if match:
                lines[int(match[1])] = re.sub(r"\d+\.", "", match[2]).split()
    assert set(lines) == set(range(1, 21))
    summary = list(csv.DictReader((ROOT / "results/summary.csv").open()))
    certs = json.loads((ROOT / "results/mate_certificates.json").read_text())
    verified = []
    for p, cert in zip(summary, certs, strict=True):
        board = chess.Board(p["fen"])
        assert cert["fen"] == p["fen"] and cert["id"] == int(p["id"])
        assert len(check(board, cert["proof"], board.turn, 5)) == 5
        line = lines[cert["id"]]
        assert len(line) == 5 and board.parse_san(line[0]).uci() == p["expected_uci"]
        for move in line:
            assert board.san(board.parse_san(move)) == move
            board.push_san(move)
        assert board.is_checkmate()
        record = dict(id=cert["id"], fen=p["fen"], reference=line, sample=cert["longest_example_san"])
        if cert["id"] == 18:
            board.pop()
            outcomes = {}
            for piece in "qrbn":
                board.push_uci("c7c8" + piece)
                outcomes[piece] = dict(checkmate=board.is_checkmate(), stalemate=board.is_stalemate())
                board.pop()
            record["promotion_outcomes"] = outcomes
        verified.append(record)
    (out / "solutions.json").write_text(json.dumps(verified, indent=2))
    examples = []
    for number, field in [(6, "mcts_seed0_move"), (13, "minimax_3_move"), (16, "minimax_3_move")]:
        p = summary[number - 1]
        board = chess.Board(p["fen"])
        wrong = p[field]
        board.push_san(wrong)
        for reply in list(board.legal_moves):
            defense = board.san(reply)
            board.push(reply)
            remaining = solve(chess.Board(board.fen()), 3)
            board.pop()
            assert remaining["completed"]
            if not remaining["winning_moves"]:
                examples.append(dict(id=number, fen=p["fen"], source=field, returned=wrong,
                                     defense=defense, key=p["expected_san"], correct=lines[number],
                                     remaining_attacker_plies=3, winning_moves=[]))
                break
        else:
            raise AssertionError("Missing defensive witness")
    (out / "defenses.json").write_text(json.dumps(examples, indent=2))


if __name__ == "__main__":
    main()
