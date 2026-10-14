"""Run after timing experiment: rights sensitivity and fixed-seed replay."""
import json
from pathlib import Path
import chess
from .positions import positions
from .oracle import solve
from src.mcts import mcts

def main():
    root=Path('deliverables/october14/results')
    raw=[json.loads(l) for l in (root/'run1/raw.jsonl').read_text().splitlines()]
    out=[]
    for i in (1,4):
        p=positions()[i-1]
        original=next(r for r in raw if r['id']==i and r['algorithm']=='oracle' and r['plies']==5)
        for rights in ('k','q','kq'):
            b=chess.Board(p['fen']); b.set_castling_fen(rights)
            result=solve(b,5,120)
            assert result['completed'] and result['winning_moves']==original['winning_moves']
            out.append(dict(id=i,castling=rights,fen=b.fen(),**result))
    replay=[]
    for i in (1,3,18):
        b=chess.Board(positions()[i-1]['fen'])
        r=mcts(b,1000,seed=0,rollout_plies=40)
        old=next(x for x in raw if x['id']==i and x['algorithm']=='mcts' and x['seed']==0)
        assert old['completed']
        assert (r.move.uci(),r.score,r.nodes,r.iterations,r.rollout_plies)==(old['move'],old['score'],old['nodes'],old['iterations'],old['rollout_plies'])
        assert [dict(move=v.move.uci(),visits=v.visits,mean=v.mean_white_reward) for v in r.root_visits]==old['root_visits']
        replay.append(dict(id=i,seed=0,all_root_statistics_identical=True))
    (root/'extra_validation.json').write_text(json.dumps(dict(castling_sensitivity=out,mcts_replays=replay),indent=2))
    print('All six castling alternatives preserve the unique mate-in-three key; three fixed-seed replays match exactly.')

if __name__=='__main__':main()
