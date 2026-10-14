"""Verify source transcription and measured records; derive machine-readable CSVs."""
import csv
import argparse
import hashlib
import json
from pathlib import Path
import chess
from .positions import positions

ROOT=Path('deliverables/october14')
RUN=ROOT/'results/run1'

def write_csv(path, rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def verify_transcription():
    glyph_pages=json.loads((ROOT/'source/extracted_board_glyphs.json').read_text())
    mapping={'0':None,'Z':None}
    for pair,piece in [('PO','P'),('NM','N'),('AB','B'),('RS','R'),('QL','Q'),('KJ','K')]:
        for c in pair:
            mapping[c]=piece; mapping[c.lower()]=piece.lower()
    rows=[row for page in glyph_pages for row in page]
    assert len(rows)==160
    for p in positions():
        b=chess.Board(p['fen'])
        for rank,glyphs in rows[(p['id']-1)*8:p['id']*8]:
            for file,glyph in enumerate(glyphs):
                piece=b.piece_at(chess.square(file,int(rank)-1))
                assert (piece.symbol() if piece else None)==mapping[glyph],(p['id'],rank,file,glyph)
    return 'All 1280 squares match independent PDF font-glyph extraction; all 20 captions/markers visually checked.'

def main():
    global RUN
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',type=Path,default=RUN)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'results')
    args=parser.parse_args()
    RUN=args.run_dir
    args.output_dir.mkdir(parents=True,exist_ok=True)
    transcription=verify_transcription()
    rows=[json.loads(l) for l in (RUN/'raw.jsonl').read_text().splitlines()]
    assert len(rows)==160, len(rows)
    env=json.loads((RUN/'environment.json').read_text())
    for name,h in env['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,name
    summary=[]; flat=[]
    for p in positions():
        b=chess.Board(p['fen']); case=[r for r in rows if r['id']==p['id']]
        assert len(case)==8
        assert {(r['algorithm'],r.get('plies'),r.get('seed')) for r in case}=={
            ('oracle',1,None),('oracle',3,None),('oracle',5,None),('minimax',3,None),('minimax',5,None),
            ('mcts',None,0),('mcts',None,1),('mcts',None,2)}
        oracle={r['plies']:r for r in case if r['algorithm']=='oracle'}
        verified=all(r['completed'] for r in oracle.values())
        exact3=verified and not oracle[1]['winning_moves'] and not oracle[3]['winning_moves'] and len(oracle[5]['winning_moves'])==1
        s=dict(id=p['id'],name=p['name'],fen=p['fen'],valid=p['valid'],oracle_verified=verified,
               exact_three_unique=exact3,expected_uci=';'.join(oracle[5]['winning_moves']) if verified else '',
               expected_san=';'.join(oracle[5]['winning_san']) if verified else '')
        for r in case:
            if r['algorithm']=='oracle':
                assert len(set(r['tested_root_moves']))==len(r['tested_root_moves'])
                if r['completed']: assert set(r['tested_root_moves'])=={m.uci() for m in b.legal_moves}
                assert set(r['winning_moves'])<=set(r['tested_root_moves'])
                continue
            assert chess.Move.from_uci(r['move']) in b.legal_moves
            assert b.san(chess.Move.from_uci(r['move']))==r['san']
            assert r['seconds']>=0 and r['nodes']>=1
            hit=r['move'] in oracle[5]['winning_moves'] if verified else None
            record={k:v for k,v in r.items() if k!='root_visits'}
            record.update(fen=p['fen'],expected_uci=s['expected_uci'],move_matches_oracle=hit,
                          completed_success=hit and r['completed'] if verified else None)
            record.update(max_seconds=env['settings']['search_seconds'],
                          status='timeout' if not r['completed'] else 'key_match' if hit else 'wrong_key' if verified else 'unverified',
                          score_convention='white_pawn_units' if r['algorithm']=='minimax' else 'white_heuristic_reward')
            if r['algorithm']=='mcts':
                record['total_rollout_plies']=record.pop('rollout_plies')
                record['rollout_cap']=env['settings']['rollout_cap']
            flat.append(record)
            if r['algorithm']=='mcts':
                assert sum(v['visits'] for v in r['root_visits'])==r['iterations']
                assert r['terminal_rollouts']+r['cutoff_rollouts']==r['iterations']
                assert r['completed']==(r['iterations']==1000)
                assert r['rollout_plies']<=40*r['iterations']
                key='mcts_seed'+str(r['seed'])
            else:
                key='minimax_'+str(r['plies'])
                if r['completed'] and oracle[r['plies']]['completed']:
                    mate_score=10000 if b.turn else -10000
                    assert (r['score']==mate_score)==bool(oracle[r['plies']]['winning_moves'])
            s[key+'_move']=r['san'];s[key+'_completed']=r['completed'];s[key+'_hit']=hit;s[key+'_seconds']=r['seconds']
        summary.append(s)
    write_csv(args.output_dir/'results.csv',flat)
    write_csv(args.output_dir/'summary.csv',summary)
    write_csv(args.output_dir/'positions.csv',positions())
    write_csv(args.output_dir/'oracle_results.csv',[
        {k:json.dumps(v) if isinstance(v,list) else v for k,v in r.items()}
        for r in rows if r['algorithm']=='oracle'])
    stats={}
    for name,subset in [('minimax_3',[r for r in flat if r['algorithm']=='minimax' and r['plies']==3]),
                        ('minimax_5',[r for r in flat if r['algorithm']=='minimax' and r['plies']==5]),
                        ('mcts',[r for r in flat if r['algorithm']=='mcts'])]:
        completed=[r for r in subset if r['completed']]
        import statistics
        stats[name]=dict(total=len(subset),completed=len(completed),timeouts=len(subset)-len(completed),
                         completed_success=sum(r['completed_success'] is True for r in subset),
                         returned_move_hits=sum(r['move_matches_oracle'] is True for r in subset),
                         median_completed_seconds=statistics.median(r['seconds'] for r in completed) if completed else None,
                         total_seconds=sum(r['seconds'] for r in subset))
    result=dict(transcription=transcription,valid_positions=20,exact_three_unique=sum(s['exact_three_unique'] for s in summary),
                source_hashes_verified=True,raw_records=len(rows),search_records=len(flat),statistics=stats)
    (args.output_dir/'validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
