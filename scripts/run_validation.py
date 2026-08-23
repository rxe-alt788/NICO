#!/usr/bin/env python3
"""Generate data/validation_report.md from empirical_18m_series.json.

This mirrors the browser rule thresholds for audit/report purposes. Incomplete hours are
excluded from classification and counted as coverage gaps; they are never GREEN by default.
"""
from __future__ import annotations
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/empirical_18m_series.json'
OUT=ROOT/'data/validation_report.md'
RANK={'GREEN':0,'ORANGE':1,'RED':2}
HOLD_HOURS=24


def finite(v):
    try: return v is not None and float(v)==float(v)
    except (TypeError,ValueError): return False


def evaluate(p, experimental=False):
    missing=[k for k in ('rainPct','turbidityPct','sstAnomaly') if not finite(p.get(k))]
    if missing: return {'flag':'INSUFFICIENT_ENV_DATA','score':None,'missing':missing}
    rain,turb,sst=float(p['rainPct']),float(p['turbidityPct']),float(p['sstAnomaly']); score=0
    if rain>=.90: score+=2
    elif rain>=.75: score+=1
    if turb>=.80: score+=2
    elif turb>=.50: score+=1
    if sst>=1.5: score+=1
    if p.get('recentTagDetected'): score+=3
    if experimental:
        up=p.get('upwellingAnomaly',p.get('upwellingIndex'))
        ac=p.get('acousticDensityPct',p.get('seasonalAcousticDensityPct'))
        if finite(up) and abs(float(up))>=1.5: score+=1
        if finite(ac) and float(ac)>=.90: score+=1
    flag='RED' if score>=3 or p.get('recentTagDetected') else 'ORANGE' if score>=2 else 'GREEN'
    return {'flag':flag,'score':score,'missing':[]}


def stabilise(rows):
    stable=None; lower=None; lower_since=None; out=[]
    for row in rows:
        cand=row['flag']; ts=datetime.fromisoformat(row['timestamp'].replace('Z','+00:00'))
        if cand not in RANK: continue
        if stable is None: stable=cand
        elif RANK[cand]>=RANK[stable]: stable=cand; lower=None; lower_since=None
        else:
            if lower!=cand: lower=cand; lower_since=ts
            if ts-lower_since>=timedelta(hours=HOLD_HOURS): stable=cand; lower=None; lower_since=None
        out.append({**row,'stable':stable})
    return out


def metrics(points, incidents, experimental=False):
    classified=[]; incomplete=0
    for p in sorted(points,key=lambda x:x['timestamp']):
        e=evaluate(p,experimental)
        if e['flag']=='INSUFFICIENT_ENV_DATA': incomplete+=1; continue
        classified.append({'timestamp':p['timestamp'],'flag':e['flag']})
    if not classified: return {'classified':0,'incomplete':incomplete}
    stable=stabilise(classified); counts=defaultdict(int); raw_trans=0; stable_trans=0; pr=ps=None
    for r,s in zip(classified,stable):
        counts[s['stable']]+=1
        if pr is not None and pr!=r['flag']: raw_trans+=1
        if ps is not None and ps!=s['stable']: stable_trans+=1
        pr,ps=r['flag'],s['stable']
    days={}
    for s in stable:
        day=s['timestamp'][:10]
        if day not in days or RANK[s['stable']]>RANK[days[day]]: days[day]=s['stable']
    incident_days={i['timestamp'][:10] for i in incidents if i.get('timestamp')}
    fp=tn=0
    for day,flag in days.items():
        if day in incident_days: continue
        if flag=='GREEN': tn+=1
        else: fp+=1
    leads=[]
    for i in incidents:
        if not i.get('timestamp'): continue
        event=datetime.fromisoformat(i['timestamp'].replace('Z','+00:00'))
        pre=[]
        for s in stable:
            ts=datetime.fromisoformat(s['timestamp'].replace('Z','+00:00'))
            if event-timedelta(hours=72)<=ts<=event and s['stable']!='GREEN': pre.append((ts,s['stable']))
        first=pre[0] if pre else None
        leads.append((i.get('location') or i.get('id'),None if not first else round((event-first[0]).total_seconds()/3600,1),None if not first else first[1]))
    n=len(stable); months=18
    return {'classified':len(classified),'incomplete':incomplete,'pct':{k:100*counts[k]/n for k in ('GREEN','ORANGE','RED')},'rawTransitionsPerMonth':raw_trans/months,'stableTransitionsPerMonth':stable_trans/months,'falseAlertBurden':None if fp+tn==0 else fp/(fp+tn),'trueNegativeRate':None if fp+tn==0 else tn/(fp+tn),'leads':leads}


def pct(v): return 'n/a' if v is None else f'{100*v:.1f}%'


def main():
    d=json.loads(DATA.read_text(encoding='utf-8')); lines=['# 4NICO Empirical Validation Baseline','',f"Generated from `{DATA.name}`. Dataset mode: **{d.get('mode')}**.",'', '## Source coverage','']
    for name,s in d.get('sourceStatus',{}).items(): lines.append(f"- **{name}**: {s.get('state','UNKNOWN')} — {s.get('note',s.get('source',''))}")
    lines += ['', '## Core empirical results','', '| Beach | Complete classified hours | Incomplete hours | Green | Orange | Red | Raw transitions/mo | 24h-hold transitions/mo | False-alert burden | True-negative rate |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    all_inc=d.get('incidents',[]); results={}
    for bid,points in d.get('beaches',{}).items():
        inc=[i for i in all_inc if i.get('beachId')==bid]; m=metrics(points,inc,False); results[bid]=m
        if not m.get('classified'):
            lines.append(f'| {bid} | 0 | {m.get("incomplete",0)} | n/a | n/a | n/a | n/a | n/a | n/a | n/a |')
        else:
            lines.append(f"| {bid} | {m['classified']} | {m['incomplete']} | {m['pct']['GREEN']:.1f}% | {m['pct']['ORANGE']:.1f}% | {m['pct']['RED']:.1f}% | {m['rawTransitionsPerMonth']:.2f} | {m['stableTransitionsPerMonth']:.2f} | {pct(m['falseAlertBurden'])} | {pct(m['trueNegativeRate'])} |")
    lines += ['', '## Empirical lead time','']
    lead_any=False
    for bid,m in results.items():
        for loc,h,state in m.get('leads',[]): lead_any=True; lines.append(f"- **{loc}**: {'no pre-event Orange/Red signal in available data' if h is None else f'{state} at T-{h}h'}")
    if not lead_any: lines.append('- Not calculable: no incident has a complete 72-hour empirical pre-event series in the hydrated dataset.')
    lines += ['', '## Clear-water secondary-cue comparison','']
    changed=False
    for bid,points in d.get('beaches',{}).items():
        off=metrics(points,[i for i in all_inc if i.get('beachId')==bid],False); on=metrics(points,[i for i in all_inc if i.get('beachId')==bid],True)
        if off.get('classified') and on.get('classified'):
            changed=True; lines.append(f"- **{bid}**: false-alert burden OFF {pct(off.get('falseAlertBurden'))}; ON {pct(on.get('falseAlertBurden'))}. 24h-hold transitions/mo OFF {off['stableTransitionsPerMonth']:.2f}; ON {on['stableTransitionsPerMonth']:.2f}.")
    if not changed: lines.append('- Not calculable until complete core environmental observations plus upwelling/acoustic cue fields are available.')
    lines += ['', '## Validation gate','']
    if not any(m.get('classified') for m in results.values()):
        lines.append('**BLOCKED BY SOURCE COVERAGE.** The pipeline is functioning fail-closed: zero empirical hours are classifiable, so no flag distribution, false-alert, lead-time, or signal-stability claim is made.')
    else:
        lines.append('At least one beach has classifiable empirical hours. Results above remain provisional until source coverage and incident reconciliation are complete.')
    lines += ['', 'Missing observations are never interpreted as GREEN. `INSUFFICIENT_ENV_DATA` is a data-quality state, not a low-risk state.']
    OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(OUT)

if __name__=='__main__': main()
