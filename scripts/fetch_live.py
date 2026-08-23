#!/usr/bin/env python3
"""Fetch daily live telemetry for the static GitHub Pages pilot.

Public BOM observations are used for recency/meteorological context. Risk-model
percentiles are only populated when a normalized partner feed supplies them.
Optional WaterNSW/DPI/IMOS endpoints are configured through repository secrets.
No missing value is converted to a low-risk value.
"""
from __future__ import annotations
import json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'live_state.json'
BEACHES = ['palm-beach','north-steyne','bondi','coogee','cronulla','balmoral']
BOM = {
  'observatory-hill': 'https://www.bom.gov.au/fwo/IDN60901/IDN60901.94768.json',
  'sydney-airport': 'https://www.bom.gov.au/fwo/IDN60901/IDN60901.94767.json'
}
BOM_ASSIGN = {
  'palm-beach':'observatory-hill','north-steyne':'observatory-hill','bondi':'observatory-hill',
  'coogee':'sydney-airport','cronulla':'sydney-airport','balmoral':'observatory-hill'
}

def get_json(url, headers=None):
    req=urllib.request.Request(url,headers={'User-Agent':'4NICO-pilot/0.4',**(headers or {})})
    with urllib.request.urlopen(req,timeout=45) as r:return json.loads(r.read().decode('utf-8'))

def latest_bom(url):
    data=get_json(url).get('observations',{}).get('data',[])
    if not data:return None
    row=data[0]
    return {
      'station': row.get('name'), 'timestampUtc': row.get('aifstime_utc'),
      'rainSince9amMm': row.get('rain_trace'), 'airTempC': row.get('air_temp'),
      'windKmh': row.get('wind_spd_kmh'), 'windDirection': row.get('wind_dir')
    }

def optional_json(env_name, headers=None):
    url=os.getenv(env_name)
    if not url:return None, {'state':'NOT_CONFIGURED'}
    try:return get_json(url,headers), {'state':'LOADED','url':url}
    except Exception as e:return None, {'state':'ERROR','error':str(e)}

def main():
    bom_data={}; source={'bom':{}}
    for key,url in BOM.items():
        try:bom_data[key]=latest_bom(url);source['bom'][key]={'state':'LOADED','url':url}
        except Exception as e:bom_data[key]=None;source['bom'][key]={'state':'ERROR','error':str(e)}
    water_headers={}
    if os.getenv('WATERNSW_SUBSCRIPTION_KEY'):water_headers['Ocp-Apim-Subscription-Key']=os.environ['WATERNSW_SUBSCRIPTION_KEY']
    water, source['waternsw']=optional_json('WATERNSW_LIVE_URL',water_headers)
    dpi, source['dpi']=optional_json('DPI_LIVE_URL')
    marine, source['marine']=optional_json('IMOS_LIVE_URL')
    beaches={}
    for bid in BEACHES:
        partner=((water or {}).get('beaches') or {}).get(bid,{})
        shark=((dpi or {}).get('beaches') or {}).get(bid,{})
        sea=((marine or {}).get('beaches') or {}).get(bid,{})
        env={
          'rainPct':partner.get('rainPct'), 'rain72hMm':partner.get('rain72hMm'),
          'turbidityPct':partner.get('turbidityPct'), 'turbidityNtu':partner.get('turbidityNtu'),
          'sstAnomaly':sea.get('sstAnomaly'), 'upwellingAnomaly':sea.get('upwellingAnomaly'),
          'acousticDensityPct':shark.get('acousticDensityPct'),
          'recentTagDetected':bool(shark.get('recentTagDetected',False))
        }
        surveillance={
          'droneActive':bool(shark.get('droneActive',False)),
          'lifeguardActive':bool(shark.get('lifeguardActive',False)),
          'turbidityDataOk':env['turbidityPct'] is not None
        }
        core_available=sum(env[k] is not None for k in ('rainPct','turbidityPct','sstAnomaly'))
        beaches[bid]={
          'env':env,'surveillance':surveillance,'bomContext':bom_data.get(BOM_ASSIGN[bid]),
          'dataCompleteness':{'coreFieldsAvailable':core_available,'coreFieldsExpected':3,
            'evaluationReady':core_available>=2 or env['recentTagDetected']}
        }
    payload={'schemaVersion':'0.4.0','generatedAt':datetime.now(timezone.utc).isoformat(),
      'qualityRule':'Missing normalized model inputs never imply low risk.', 'sources':source,'beaches':beaches}
    OUT.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(OUT),'generatedAt':payload['generatedAt']},indent=2))
if __name__=='__main__':main()
