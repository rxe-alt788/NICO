(function () {
  'use strict';

  const MONTHS_IN_WINDOW = 18;
  const DAY_MS = 86400000;

  function hash(text) { let h = 2166136261; for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rand(seed) { let x = seed >>> 0; return function () { x += 0x6D2B79F5; let t = x; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  function generateDemoSeries(beach, experimentalSecondaryCues) {
    const cfg = window.FourNICOConfig.analytics;
    const stepMs = cfg.demoStepHours * 3600000;
    const start = new Date(cfg.evaluationStart).getTime(); const end = new Date(cfg.evaluationEnd).getTime();
    const r = rand(hash(beach.id)); const series = []; let rainPulse = 0; let turbidityPulse = 0;
    for (let ts = start; ts <= end; ts += stepMs) {
      const d = new Date(ts); const doy = Math.floor((ts - Date.UTC(d.getUTCFullYear(), 0, 0)) / DAY_MS);
      const seasonal = 0.5 + 0.5 * Math.sin((doy / 365) * Math.PI * 2 - 0.8);
      if (r() > 0.975) rainPulse = 0.72 + r() * 0.27; else rainPulse *= 0.94;
      if (rainPulse > 0.55) turbidityPulse = Math.max(turbidityPulse, rainPulse * (0.76 + r() * 0.18)); else turbidityPulse *= 0.92;
      const env = {
        rainPct: Math.min(0.99, 0.18 + seasonal * 0.13 + rainPulse),
        turbidityPct: Math.min(0.99, 0.18 + turbidityPulse),
        sstAnomaly: Math.max(-0.5, Math.min(2.2, -0.1 + seasonal * 0.8 + (r() > 0.985 ? 1.2 : 0))),
        recentTagDetected: r() > 0.9985,
        upwellingAnomaly: (r() - 0.5) * 3.2,
        acousticDensityPct: r()
      };
      const blackout = r() > 0.992; const partial = !blackout && r() > 0.96;
      const surveillance = blackout ? { droneActive:false, lifeguardActive:false,turbidityDataOk:r()>0.5 } : partial ? { droneActive:false,lifeguardActive:true,turbidityDataOk:true } : { droneActive:true,lifeguardActive:true,turbidityDataOk:true };
      const raw = window.FourNICO.evaluateBeachStatus(env, surveillance, { experimentalSecondaryCues });
      series.push({ timestamp:new Date(ts).toISOString(), ...raw });
    }
    return series;
  }

  function analyseSeries(series, holdHours) {
    if (!series.length) return null;
    const stable = window.FourNICO.stabilizeTimeline(series, holdHours);
    const counts = { GREEN:0, ORANGE:0, RED:0, RED_BLACK:0, OTHER_BLACK:0 };
    let transitions = 0, previous = null;
    stable.forEach(s => {
      const composite = s.obsState === 'BLACKOUT' ? `${s.stableEnvFlag}_BLACK` : s.stableEnvFlag;
      if (composite === 'RED_BLACK') counts.RED_BLACK++; else if (s.obsState === 'BLACKOUT') counts.OTHER_BLACK++; else counts[s.stableEnvFlag]++;
      if (previous !== null && previous !== composite) transitions++; previous = composite;
    });
    const n = stable.length;
    const pct = Object.fromEntries(Object.entries(counts).map(([k,v]) => [k,(v/n)*100]));
    return { stable, counts, pct, transitions, transitionsPerMonth: transitions / MONTHS_IN_WINDOW };
  }

  function empiricalSeriesForBeach(empirical, beachId, experimentalSecondaryCues) {
    const points = empirical?.beaches?.[beachId] || [];
    return points.flatMap(p => {
      const hasAnyCore = [p.rainPct, p.turbidityPct, p.sstAnomaly].some(v => Number.isFinite(Number(v)));
      if (!hasAnyCore) return [];
      const env = {
        rainPct: Number.isFinite(Number(p.rainPct)) ? Number(p.rainPct) : 0,
        turbidityPct: Number.isFinite(Number(p.turbidityPct)) ? Number(p.turbidityPct) : 0,
        sstAnomaly: Number.isFinite(Number(p.sstAnomaly)) ? Number(p.sstAnomaly) : 0,
        recentTagDetected: Boolean(p.recentTagDetected),
        upwellingAnomaly: Number(p.upwellingAnomaly ?? p.upwellingIndex ?? 0),
        acousticDensityPct: Number(p.acousticDensityPct ?? 0)
      };
      const surveillance = {
        droneActive: Boolean(p.droneActive),
        lifeguardActive: Boolean(p.lifeguardActive),
        turbidityDataOk: Number.isFinite(Number(p.turbidityPct))
      };
      const result = window.FourNICO.evaluateBeachStatus(env, surveillance, { experimentalSecondaryCues });
      return [{ timestamp:p.timestamp, ...result, sourcePoint:p }];
    });
  }

  function incidentDays(empirical, beachId) {
    const set = new Set();
    (empirical?.incidents || []).filter(i => i.beachId === beachId && i.timestamp).forEach(i => set.add(new Date(i.timestamp).toISOString().slice(0,10)));
    return set;
  }

  function falseAlertMetrics(series, empirical, beachId, holdHours) {
    if (!series.length) return null;
    const stable = window.FourNICO.stabilizeTimeline(series, holdHours);
    const byDay = new Map();
    const rank = { GREEN:0, ORANGE:1, RED:2 };
    stable.forEach(s => {
      const day = new Date(s.timestamp).toISOString().slice(0,10); const prev = byDay.get(day);
      if (!prev || rank[s.stableEnvFlag] > rank[prev.stableEnvFlag]) byDay.set(day, s);
    });
    const incidents = incidentDays(empirical, beachId);
    let tn=0, fp=0, incidentFlagged=0, incidentTotal=0;
    byDay.forEach((s, day) => {
      const flagged = s.stableEnvFlag !== 'GREEN'; const incident = incidents.has(day);
      if (incident) { incidentTotal++; if (flagged) incidentFlagged++; }
      else if (flagged) fp++; else tn++;
    });
    const nonIncident = tn + fp;
    return {
      trueNegativeRate: nonIncident ? tn/nonIncident : null,
      falseAlertBurden: nonIncident ? fp/nonIncident : null,
      incidentDaySensitivity: incidentTotal ? incidentFlagged/incidentTotal : null,
      evaluatedDays: byDay.size,
      incidentDaysObserved: incidentTotal
    };
  }

  function empiricalLeadTimes(empirical, beachId, series, holdHours) {
    const stable = window.FourNICO.stabilizeTimeline(series, holdHours);
    return (empirical?.incidents || []).filter(i => i.beachId === beachId && i.timestamp).map(incident => {
      const eventMs = new Date(incident.timestamp).getTime();
      const pre = stable.filter(s => { const t=new Date(s.timestamp).getTime(); return t <= eventMs && t >= eventMs - 72*3600000; });
      const first = pre.find(s => s.stableEnvFlag !== 'GREEN');
      return { incidentId:incident.id, location:incident.location, leadHours:first ? Math.round((eventMs-new Date(first.timestamp).getTime())/360000)/10 : null, state:first?.stableEnvFlag || null };
    });
  }

  function incidentStats(incident) {
    const rows = incident.profile.map(p => ({ ...p, result:window.FourNICO.evaluateBeachStatus(p,p.surveillance) }));
    const advisory=rows.find(r=>r.result.envFlag!=='GREEN'||r.result.obsState==='BLACKOUT'); const firstOrange=rows.find(r=>r.result.envFlag==='ORANGE'||r.result.envFlag==='RED'); const firstRed=rows.find(r=>r.result.envFlag==='RED'); const firstBlack=rows.find(r=>r.result.obsState==='BLACKOUT'); const at=h=>rows.find(r=>r.hoursToEvent===h)||null;
    return { incident, rows, lead:{ firstAdvisoryHours:advisory?Math.abs(advisory.hoursToEvent):null, orangeHours:firstOrange?Math.abs(firstOrange.hoursToEvent):null, redHours:firstRed?Math.abs(firstRed.hoursToEvent):null, blackoutHours:firstBlack?Math.abs(firstBlack.hoursToEvent):null }, checkpoints:[-24,-12,0].map(h=>({hours:h,row:at(h)})) };
  }

  function fmtPct(v) { return v == null ? '—' : `${(v*100).toFixed(1)}%`; }
  function fmtDistribution(v) { return v == null ? '—' : `${v.toFixed(1)}%`; }

  function renderAnalytics(beaches, empirical, sourceMode, experimentalSecondaryCues) {
    const body=document.getElementById('analytics-body'); if(!body)return;
    const hold=Number(document.getElementById('hold-hours')?.value||window.FourNICOConfig.hysteresis.holdHours);
    const empiricalMode=sourceMode==='empirical';
    body.innerHTML=beaches.map(beach=>{
      const series=empiricalMode ? empiricalSeriesForBeach(empirical,beach.id,experimentalSecondaryCues) : generateDemoSeries(beach,experimentalSecondaryCues);
      const a=analyseSeries(series,hold);
      if(!a) return `<tr><td><strong>${beach.name}</strong></td><td colspan="9">INSUFFICIENT EMPIRICAL DATA</td></tr>`;
      const f=empiricalMode?falseAlertMetrics(series,empirical,beach.id,hold):null;
      const lead=empiricalMode?empiricalLeadTimes(empirical,beach.id,series,hold):[];
      const leadText=lead.length?lead.map(x=>`${x.location}: ${x.leadHours==null?'no warning':`${x.state} T-${x.leadHours}h`}`).join('<br>'):'—';
      return `<tr><td><strong>${beach.name}</strong></td><td>${fmtDistribution(a.pct.GREEN)}</td><td>${fmtDistribution(a.pct.ORANGE)}</td><td>${fmtDistribution(a.pct.RED)}</td><td>${fmtDistribution(a.pct.RED_BLACK)}</td><td>${a.transitionsPerMonth.toFixed(1)}/mo</td><td>${f?fmtPct(f.falseAlertBurden):'demo'}</td><td>${f?fmtPct(f.trueNegativeRate):'demo'}</td><td class="small">${leadText}</td></tr>`;
    }).join('');
    const note=document.getElementById('analytics-provenance');
    if(note) note.textContent=empiricalMode ? `EMPIRICAL MODE · dataset=${empirical?.mode||'unknown'} · ${hold}h de-escalation hold · missing observations are not imputed.` : `SYNTHETIC DEMONSTRATION · ${hold}h de-escalation hold · not measured history.`;
  }

  function renderIncidentMatrix(history) {
    const wrap=document.getElementById('incident-matrix'); if(!wrap)return;
    wrap.innerHTML=history.incidents.map(incident=>{const s=incidentStats(incident);const lead=s.lead.firstAdvisoryHours==null?'No configured pre-event elevation':`First advisory T-${s.lead.firstAdvisoryHours}h`;const cells=s.checkpoints.map(cp=>{if(!cp.row)return'<td>n/a</td>';const r=cp.row.result;return `<td><div class="matrix-baseline">Without 4NICO: no integrated advisory</div><strong>${r.envFlag}${r.obsState==='BLACKOUT'?' [UNMONITORED]':''}</strong><div class="small">Env ${r.envScore} · Obs ${r.confScore}/3</div></td>`;}).join('');return `<tr data-incident-id="${incident.id}" class="incident-row"><td><button class="incident-select" data-incident="${incident.id}">${incident.name}</button><div class="small">${incident.eventClass}</div></td><td><strong>${lead}</strong><div class="small">Orange ${s.lead.orangeHours==null?'—':`T-${s.lead.orangeHours}h`} · Red ${s.lead.redHours==null?'—':`T-${s.lead.redHours}h`} · Blackout ${s.lead.blackoutHours==null?'—':`T-${s.lead.blackoutHours}h`}</div></td>${cells}</tr>`;}).join('');
  }

  window.FourNICOAnalytics=Object.freeze({generateDemoSeries,analyseSeries,empiricalSeriesForBeach,falseAlertMetrics,empiricalLeadTimes,incidentStats,renderAnalytics,renderIncidentMatrix});
})();
