#!/usr/bin/env python3
"""Generate data/validation_report.md from empirical_18m_series.json.

Two lanes are reported:
1. empirical-only: synthetic rows excluded from performance claims;
2. engineering fixture: synthetic rows allowed only to prove pipeline/state behavior.

Primary operational gate:
    Alert Occupancy Rate = (T_ORANGE + T_RED) / T_TOTAL

Incomplete core observations are never classified GREEN. Validation metrics use only
ASID_AUTHORITATIVE and VERIFIED_INTERIM incident records marked validationEligible.
"""
from __future__ import annotations
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/empirical_18m_series.json'
OUT=ROOT/'data/validation_report.md'
RANK={'GREEN':0,'ORANGE':1,'RED':2}
HOLD_HOURS=24
ELIGIBLE_PROVENANCE={'ASID_AUTHORITATIVE','VERIFIED_INTERIM'}


def finite(v):
    try: return v is not None and float(v)==float(v)
    except (TypeError,ValueError): return False


def synthetic_point(p):
    return any(bool(p.get(k)) for k in ('rainSyntheticFlag','waterSyntheticFlag','beachwatchSyntheticFlag','marineSyntheticFlag'))


def eligible_incident(i):
    return bool(i.get('validationEligible')) and i.get('provenanceClass') in ELIGIBLE_PROVENANCE


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
    return {'flag':'RED' if score>=3 or p.get('recentTagDetected') else 'ORANGE' if score>=2 else 'GREEN','score':score,'missing':[]}


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


def metrics(points, incidents, experimental=False, include_synthetic=False):
    classified=[]; incomplete=0; excluded_synthetic=0
    for p in sorted(points,key=lambda x:x['timestamp']):
        if synthetic_point(p) and not include_synthetic:
            excluded_synthetic+=1; continue
        e=evaluate(p,experimental)
        if e['flag']=='INSUFFICIENT_ENV_DATA': incomplete+=1; continue
        classified.append({'timestamp':p['timestamp'],'flag':e['flag']})
    if not classified:
        return {'classified':0,'incomplete':incomplete,'excludedSynthetic':excluded_synthetic,'alertOccupancy':None}

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
    incident_days={str(i['timestamp'])[:10] for i in incidents if eligible_incident(i) and i.get('timestamp')}
    fp=tn=0
    for day,flag in days.items():
        if day in incident_days: continue
        if flag=='GREEN': tn+=1
        else: fp+=1

    leads=[]
    for i in incidents:
        if not eligible_incident(i) or not i.get('timestamp'): continue
        try: event=datetime.fromisoformat(str(i['timestamp']).replace('Z','+00:00'))
        except ValueError: continue
        pre=[]
        for s in stable:
            ts=datetime.fromisoformat(s['timestamp'].replace('Z','+00:00'))
            if event-timedelta(hours=72)<=ts<=event and s['stable']!='GREEN': pre.append((ts,s['stable']))
        first=pre[0] if pre else None
        leads.append((i.get('location') or i.get('id'),None if not first else round((event-first[0]).total_seconds()/3600,1),None if not first else first[1],i.get('provenanceClass')))

    n=len(stable); months=18
    occupancy=(counts['ORANGE']+counts['RED'])/n
    return {
        'classified':len(classified),
        'incomplete':incomplete,
        'excludedSynthetic':excluded_synthetic,
        'pct':{k:100*counts[k]/n for k in ('GREEN','ORANGE','RED')},
        'alertOccupancy':occupancy,
        'rawTransitionsPerMonth':raw_trans/months,
        'stableTransitionsPerMonth':stable_trans/months,
        'falseAlertBurden':None if fp+tn==0 else fp/(fp+tn),
        'trueNegativeRate':None if fp+tn==0 else tn/(fp+tn),
        'leads':leads
    }


def pct(v): return 'n/a' if v is None else f'{100*v:.1f}%'


def render_table(lines, title, data, include_synthetic):
    lines += ['', title,'', '| Beach | Classified hours | Incomplete | Synthetic excluded | Green | Orange | Red | **Alert occupancy** | Raw transitions/mo | 24h-hold transitions/mo | False-alert burden | True-negative rate |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    results={}; all_inc=data.get('incidents',[])
    for bid,points in data.get('beaches',{}).items():
        inc=[i for i in all_inc if i.get('beachId')==bid and eligible_incident(i)]
        m=metrics(points,inc,False,include_synthetic); results[bid]=m
        if not m.get('classified'):
            lines.append(f'| {bid} | 0 | {m.get("incomplete",0)} | {m.get("excludedSynthetic",0)} | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |')
        else:
            lines.append(f"| {bid} | {m['classified']} | {m['incomplete']} | {m['excludedSynthetic']} | {m['pct']['GREEN']:.1f}% | {m['pct']['ORANGE']:.1f}% | {m['pct']['RED']:.1f}% | **{pct(m['alertOccupancy'])}** | {m['rawTransitionsPerMonth']:.2f} | {m['stableTransitionsPerMonth']:.2f} | {pct(m['falseAlertBurden'])} | {pct(m['trueNegativeRate'])} |")
    return results


def previous_dataset():
    try:
        r=subprocess.run(['git','show','HEAD:data/empirical_18m_series.json'],cwd=ROOT,capture_output=True,text=True,check=True)
        return json.loads(r.stdout)
    except Exception:
        return None


def source_signature(data):
    out={}
    for name,s in data.get('sourceStatus',{}).items():
        out[name]={
            'state':s.get('state','UNKNOWN'),
            'sourceClass':s.get('sourceClass','UNCLASSIFIED'),
            'synthetic':bool(s.get('synthetic'))
        }
    return out


def append_displacement_delta(lines, current, previous):
    lines += ['', '## Serial displacement delta','']
    lines.append('Each source substitution triggers a full 18-month rerun. The first operational comparison is Alert Occupancy Rate before hit-rate or lead-time claims are considered.')
    cur_sig=source_signature(current)
    if previous is None:
        lines.append('- No prior processed dataset is available for comparison in git history.')
    else:
        prev_sig=source_signature(previous)
        changed=[]
        for source in sorted(set(cur_sig)|set(prev_sig)):
            if cur_sig.get(source)!=prev_sig.get(source):
                changed.append(f"- **{source}**: `{prev_sig.get(source)}` → `{cur_sig.get(source)}`")
        if changed: lines.extend(changed)
        else: lines.append('- No source-lineage displacement detected relative to the prior committed processed dataset.')

    synthetic=current.get('syntheticEnvironmentalSources',[])
    if synthetic:
        lines.append(f"- Remaining synthetic environmental sources: **{', '.join(synthetic)}**.")
    else:
        lines.append('- Remaining synthetic environmental sources: **none**.')


def main():
    previous=previous_dataset()
    d=json.loads(DATA.read_text(encoding='utf-8'))
    lines=['# 4NICO Validation Report','',f"Generated from `{DATA.name}`. Dataset mode: **{d.get('mode')}**.",'', '> Synthetic environmental fixtures are engineering test data. They are excluded from empirical performance claims.','', '## Primary operational gate: Alert Occupancy Rate','', '$$\\text{Advisory Burden} = \\frac{T_{Orange}+T_{Red}}{T_{Total}}$$','', 'Alert occupancy is evaluated before incident hit-rate or lead-time. No pass/fail ceiling is hard-coded until DPI agrees an operationally realistic occupancy limit.','', '## Source coverage','']
    for name,s in d.get('sourceStatus',{}).items(): lines.append(f"- **{name}**: {s.get('state','UNKNOWN')} · {s.get('sourceClass','UNCLASSIFIED')} — {s.get('note',s.get('source',''))}")

    provenance_counts=defaultdict(int)
    for i in d.get('incidents',[]): provenance_counts[i.get('provenanceClass','UNCLASSIFIED')]+=1
    lines += ['', '## Incident provenance ledger','']
    for p in ('ASID_AUTHORITATIVE','VERIFIED_INTERIM','UNVERIFIED_SUPPLEMENTARY'):
        lines.append(f'- **{p}**: {provenance_counts[p]} record(s).')
    lines.append('- Validation metrics include only `ASID_AUTHORITATIVE` and `VERIFIED_INTERIM` records with `validationEligible=true`.')

    empirical=render_table(lines,'## Empirical-only results',d,False)
    fixture=render_table(lines,'## Engineering fixture results',d,True)

    lines += ['', '## Empirical lead time','']
    empirical_leads=False
    for m in empirical.values():
        for loc,h,state,provenance in m.get('leads',[]):
            empirical_leads=True
            lines.append(f"- **{loc}** ({provenance}): {'no pre-event Orange/Red signal' if h is None else f'{state} at T-{h}h'}")
    if not empirical_leads: lines.append('- Not calculable from authoritative environmental observations yet.')

    lines += ['', '## Clear-water secondary-cue test','']
    any_fixture=False
    for bid,points in d.get('beaches',{}).items():
        inc=[i for i in d.get('incidents',[]) if i.get('beachId')==bid and eligible_incident(i)]
        off=metrics(points,inc,False,True); on=metrics(points,inc,True,True)
        if off.get('classified') and on.get('classified'):
            any_fixture=True
            lines.append(f"- **{bid} engineering fixture**: alert occupancy OFF {pct(off.get('alertOccupancy'))}; ON {pct(on.get('alertOccupancy'))}. False-alert burden OFF {pct(off.get('falseAlertBurden'))}; ON {pct(on.get('falseAlertBurden'))}. Stable transitions/mo OFF {off['stableTransitionsPerMonth']:.2f}; ON {on['stableTransitionsPerMonth']:.2f}.")
    if not any_fixture: lines.append('- No complete fixture series available for ON/OFF comparison.')

    append_displacement_delta(lines,d,previous)

    lines += ['', '## Validation gate','']
    empirical_occupancies=[m.get('alertOccupancy') for m in empirical.values() if m.get('alertOccupancy') is not None]
    if not empirical_occupancies:
        lines.append('**EMPIRICAL VALIDATION REMAINS BLOCKED.** There is no non-synthetic Alert Occupancy Rate to test against an operational DPI ceiling. Synthetic fixture coverage proves ingestion/rules/hysteresis execution only.')
    else:
        mean_occ=sum(empirical_occupancies)/len(empirical_occupancies)
        lines.append(f'Non-synthetic alert occupancy is now measurable. Mean beach occupancy across classifiable pilot data is **{pct(mean_occ)}**. Utility remains provisional until DPI sets the acceptable operational ceiling and source coverage is complete.')
    lines += ['', 'Missing observations are never interpreted as GREEN. `INSUFFICIENT_ENV_DATA` is a data-quality state, not a low-risk state.']
    OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(OUT)

if __name__=='__main__': main()
