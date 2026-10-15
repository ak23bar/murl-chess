"""Construct and check explicit strategies covering EVERY defensive reply.

Certificates prove the selected key wins; the exhaustive oracle separately
excludes other keys and shorter mates. The checker does no evaluation/search.
"""
import json
import time
from pathlib import Path
import chess
from .positions import positions

def check(b, node, attacker, left):
    if node.get('mate'):
        assert b.is_checkmate() and b.turn!=attacker
        return []
    assert left>0 and b.outcome(claim_draw=False) is None
    moves=node['moves']
    legal={m.uci() for m in b.legal_moves}
    assert set(moves)<=legal
    assert len(moves)==1 if b.turn==attacker else set(moves)==legal
    assert moves
    lines=[]
    for uci,child in moves.items():
        b.push_uci(uci)
        try: lines.append([uci]+check(b,child,attacker,left-1))
        finally: b.pop()
    return max(lines,key=len)

def create(b,attacker,left,deadline):
    if time.perf_counter()>deadline: raise TimeoutError('certificate budget exceeded')
    if b.is_checkmate(): return {'mate':True} if b.turn!=attacker else None
    if left==0 or b.outcome(claim_draw=False) is not None: return None
    attack=b.turn==attacker
    children={}
    for m in list(b.legal_moves):
        b.push(m)
        try: child=create(b,attacker,left-1,deadline)
        finally: b.pop()
        if attack and child is not None: return {'moves':{m.uci():child}}
        if not attack:
            if child is None: return None
            children[m.uci()]=child
    return {'moves':children} if not attack and children else None

def main():
    root=Path('deliverables/october14/results')
    raw=[json.loads(l) for l in (root/'run1/raw.jsonl').read_text().splitlines()]
    certs=[]
    for p in positions():
        expected=next(r for r in raw if r['id']==p['id'] and r['algorithm']=='oracle' and r['plies']==5)
        assert expected['completed'] and len(expected['winning_moves'])==1
        key=expected['winning_moves'][0]
        b=chess.Board(p['fen']); attacker=b.turn
        b.push_uci(key)
        child=create(b,attacker,4,time.perf_counter()+120)
        assert child is not None
        b.pop()
        proof={'moves':{key:child}}
        line=check(b,proof,attacker,5)
        assert len(line)==5
        san=[]
        for uci in line:
            move=chess.Move.from_uci(uci);san.append(b.san(move));b.push(move)
        certs.append(dict(id=p['id'],fen=p['fen'],proof=proof,longest_example_uci=line,longest_example_san=san))
    (root/'mate_certificates.json').write_text(json.dumps(certs,indent=2))
    print('20 strategy certificates checked: every defensive reply covered, each longest line is five plies.')

if __name__=='__main__':main()
