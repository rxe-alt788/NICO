(function () {
  'use strict';

  const MONTHS_IN_WINDOW = 18;
  const DAY_MS = 86400000;
  const VALID_FLAGS = new Set(['GREEN','ORANGE','RED']);

  function hash(text){let h=2166136261;for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;}
  function rand(seed){let x=seed>>>0;return function(){x+=0x6D2B79F5;let t=x;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}

  function generateDemoSeries(beach, experimentalSecondaryCues){
    const cfg=window.FourNICOConfig.analytics, stepMs=cfg.demoStepHours*3600000;
    const start=new Date(cfg.evaluationStart).getTime(), end=new Date(cfg.evaluationEnd).getTime();
    const r=rand(hash(beach.id)), series=[]; let rainPulse=0,turbidityPulse=0;
    for(let ts=start;ts<=end;ts+=stepMs){
      const d=new Date(ts),doy=Math.floor((ts-Date.UTC(d.getUTCFullYear(),0,0))/DAY_MS),seasonal=.5+.5*Math.sin((doy/365)*Math.PI*2-.8);
      if(r()>.975)rainPulse=.72+r()*.27;else rainPulse*=.94;
      if(rainPulse>.55)turbidityPulse=Math.max(turbidityPulse,rainPulse*(.76+r()*.18));else turbidityPulse*=.92;
      const env={rainPct:Math.min(.99,.18+seasonal*.13+rainPulse),turbidityPct:Math.min(.99,.18+turbidityPulse),sstAnomaly:Math.max(-.5,Math.min(2.2,-.1+seasonal*.8+(r()>.985?1.2:0))),recentTagDetected:r()>.9985,upwellingAnomaly:(r()-.5)*3.2,acousticDensityPct:r()};
      const blackout=r()>.992,partial=!blackout&&r()>.96;
      const surveillance=blackout?{droneActive:false,lifeguardActive:false,turbidityDataOk:r()>.5}:partial?{droneActive:false,lifeguardActive:true,turbidityDataOk:true}:{droneActive:true,lifeguardActive:true,turbidityDataOk:true};
      series.push({timestamp:new Date(ts).toISOString(),...window.FourNICO.evaluateBeachStatus(env,surveillance,{experimentalSecondaryCues})});
    }
    return series;
  }

  function validSeries(series){return series.filter(s=>VALID_FLAGS.has(s.envFlag));}

  function analyseSeries(series,holdHours){
    const valid=validSeries(series); if(!valid.length)return null;
    const stable=window.FourNICO.stabilizeTimeline(valid,holdHours),counts={GREEN:0,ORANGE:0,RED:0,RED_BLACK:0,OTHER_BLACK:0};
    let transitions=0,rawTransitions=0,previous=null,previousRaw=null;
    stable.forEach(s=>{const composite=s.obsState==='BLACKOUT'?`${s.stableEnvFlag}_BLACK`:s.stableEnvFlag;if(composite==='RED_BLACK')counts.RED_BLACK++;else if(s.obsState==='BLACKOUT')counts.OTHER_BLACK++;else counts[s.stableEnvFlag]++;if(previous!==null&&previous!==composite)transitions++;previous=composite;if(previousRaw!==null&&previousRaw!==s.compositeFlag)rawTransitions++;previousRaw=s.compositeFlag;});
    const n=stable.length,pct=Object.fromEntries(Object.entries(counts).map(([k,v])=>[k,(v/n)*100]));
    return{stable,counts,pct,transitions,rawTransitions,transitionsPerMonth:transitions/MONTHS_IN_WINDOW,rawTransitionsPerMonth:rawTransitions/MONTHS_IN_WINDOW};
  }

  function empiricalSeriesForBeach(empirical,beachId,experimentalSecondaryCues){
    const points=empirical?.beaches?.[beachId]||[];
    return points.map(p=>{
      const env={rainPct:p.rainPct,turbidityPct:p.turbidityPct,sstAnomaly:p.sstAnomaly,recentTagDetected:Boolean(p.recentTagDetected),upwellingAnomaly:p.upwellingAnomaly??p.upwellingIndex,acousticDensityPct:p.acousticDensityPct??p.seasonalAcousticDensityPct};
      const surveillance={droneActive:Boolean(p.droneActive),lifeguardActive:Boolean(p.lifeguardActive),turbidityDataOk:Number.isFinite(Number(p.turbidityPct))};
      return{timestamp:p.timestamp,...window.FourNICO.evaluateBeachStatus(env,surveillance,{experimentalSecondaryCues}),sourcePoint:p};
    });
  }

  function incidentDays(empirical,beachId){const set=new Set();(empirical?.incidents||[]).filter(i=>i.beachId===beachId&&i.timestamp).forEach(i=>set.add(new Date(i.timestamp).toISOString().slice(0,10)));return set;}

  function falseAlertMetrics(series,empirical,beachId,holdHours){
    const valid=validSeries(series); if(!valid.length)return null;
    const stable=window.FourNICO.stabilizeTimeline(valid,holdHours),byDay=new Map(),rank={GREEN:0,ORANGE:1,RED:2};
    stable.forEach(s=>{const day=new Date(s.timestamp).toISOString().slice(0,10),prev=byDay.get(day);if(!prev||rank[s.stableEnvFlag]>rank[prev.stableEnvFlag])byDay.set(day,s);});
    const incidents=incidentDays(empirical,beachId);let tn=0,fp=0,incidentFlagged=0,incidentTotal=0;
    byDay.forEach((s,day)=>{const flagged=s.stableEnvFlag!=='GREEN',incident=incidents.has(day);if(incident){incidentTotal++;if(flagged)incidentFlagged++;}else if(flagged)fp++;else tn++;});
    const nonIncident=tn+fp;return{trueNegativeRate:nonIncident?tn/nonIncident:null,falseAlertBurden:nonIncident?fp/nonIncident:null,incidentDaySensitivity:incidentTotal?incidentFlagged/incidentTotal:null,evaluatedDays:byDay.size,incidentDaysObserved:incidentTotal};
  }

  function empiricalLeadTimes(empirical,beachId,series,holdHours){
    const stable=window.FourNICO.stabilizeTimeline(validSeries(series),holdHours);
    return(empirical?.incidents||[]).filter(i=>i.beachId===beachId&&i.timestamp).map(incident=>{const eventMs=new Date(incident.timestamp).getTime(),pre=stable.filter(s=>{const t=new Date(s.timestamp).getTime();return t<=eventMs&&t>=eventMs-72*3600000;}),first=pre.find(s=>s.stableEnvFlag!=='GREEN');return{incidentId:incident.id,location:incident.location,leadHours:first?Math.round((eventMs-new Date(first.timestamp).getTime())/360000)/10:null,state:first?.stableEnvFlag||null};});
  }

  function incidentStats(incident){const rows=(incident.profile||[]).map(p=>({...p,result:window.FourNICO.evaluateBeachStatus(p,p.surveillance)}));const advisory=rows.find(r=>r.result.envFlag!=='GREEN'||r.result.obsState==='BLACKOUT'),firstOrange=rows.find(r=>r.result.envFlag==='ORANGE'||r.result.envFlag==='RED'),firstRed=rows.find(r=>r.result.envFlag==='RED'),firstBlack=rows.find(r=>r.result.obsState==='BLACKOUT'),at=h=>rows.find(r=>r.hoursToEvent===h)||null;return{incident,rows,lead:{firstAdvisoryHours:advisory?Math.abs(advisory.hoursToEvent):null,orangeHours:firstOrange?Math.abs(firstOrange.hoursToEvent):null,redHours:firstRed?Math.abs(firstRed.hoursToEvent):null,blackoutHours:firstBlack?Math.abs(firstBlack.hoursToEvent):null},checkpoints:[-24,-12,0].map(h=>({hours:h,row:at(h)}))};}

  const fmtPct=v=>v==null?'—':`${(v*100).toFixed(1)}%`,fmtDistribution=v=>v==null?'—':`${v.toFixed(1)}%`;

  function renderAnalytics(beaches,empirical,sourceMode,experimentalSecondaryCues){
    const body=document.getElementById('analytics-body');if(!body)return;const hold=Number(document.getElementById('hold-hours')?.value||window.FourNICOConfig.hysteresis.holdHours),empiricalMode=sourceMode==='empirical';
    body.innerHTML=beaches.map(beach=>{const series=empiricalMode?empiricalSeriesForBeach(empirical,beach.id,experimentalSecondaryCues):generateDemoSeries(beach,experimentalSecondaryCues),coverage=series.length?validSeries(series).length/series.length:0,a=analyseSeries(series,hold);if(!a)return`<tr><td><strong>${beach.name}</strong></td><td colspan="10">INSUFFICIENT EMPIRICAL DATA</td></tr>`;const f=empiricalMode?falseAlertMetrics(series,empirical,beach.id,hold):null,lead=empiricalMode?empiricalLeadTimes(empirical,beach.id,series,hold):[],leadText=lead.length?lead.map(x=>`${x.location}: ${x.leadHours==null?'no warning':`${x.state} T-${x.leadHours}h`}`).join('<br>'):'—';return`<tr><td><strong>${beach.name}</strong></td><td>${fmtDistribution(a.pct.GREEN)}</td><td>${fmtDistribution(a.pct.ORANGE)}</td><td>${fmtDistribution(a.pct.RED)}</td><td>${fmtDistribution(a.pct.RED_BLACK)}</td><td>${a.transitionsPerMonth.toFixed(1)}/mo <span class="small">raw ${a.rawTransitionsPerMonth.toFixed(1)}</span></td><td>${f?fmtPct(f.falseAlertBurden):'demo'}</td><td>${f?fmtPct(f.trueNegativeRate):'demo'}</td><td>${(coverage*100).toFixed(1)}%</td><td class="small">${leadText}</td></tr>`;}).join('');
    const note=document.getElementById('analytics-provenance');if(note)note.textContent=empiricalMode?`EMPIRICAL MODE · dataset=${empirical?.mode||'unknown'} · ${hold}h de-escalation hold · incomplete hours excluded, never imputed GREEN.`:`SYNTHETIC DEMONSTRATION · ${hold}h de-escalation hold · not measured history.`;
  }

  function renderIncidentMatrix(history){const wrap=document.getElementById('incident-matrix');if(!wrap)return;wrap.innerHTML=(history.incidents||[]).map(incident=>{const s=incidentStats(incident),lead=s.lead.firstAdvisoryHours==null?'No configured pre-event elevation':`First advisory T-${s.lead.firstAdvisoryHours}h`,cells=s.checkpoints.map(cp=>{if(!cp.row)return'<td>n/a</td>';const r=cp.row.result;return`<td><div class="matrix-baseline">Without 4NICO: no integrated advisory</div><strong>${r.envFlag}${r.obsState==='BLACKOUT'?' [UNMONITORED]':''}</strong><div class="small">Env ${r.envScore??'—'} · Obs ${r.confScore}/3</div></td>`;}).join('');return`<tr data-incident-id="${incident.id}" class="incident-row"><td><button class="incident-select" data-incident="${incident.id}">${incident.name}</button><div class="small">${incident.eventClass}</div></td><td><strong>${lead}</strong></td>${cells}</tr>`;}).join('');}

  window.FourNICOAnalytics=Object.freeze({generateDemoSeries,analyseSeries,empiricalSeriesForBeach,falseAlertMetrics,empiricalLeadTimes,incidentStats,renderAnalytics,renderIncidentMatrix});
})();