(function () {
  'use strict';

  const MONTHS_IN_WINDOW = 18;
  const DAY_MS = 86400000;

  function hash(text) {
    let h = 2166136261;
    for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }

  function rand(seed) {
    let x = seed >>> 0;
    return function () { x += 0x6D2B79F5; let t = x; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }

  function generateDemoSeries(beach) {
    const cfg = window.FourNICOConfig.analytics;
    const stepMs = cfg.demoStepHours * 3600000;
    const start = new Date(cfg.evaluationStart).getTime();
    const end = new Date(cfg.evaluationEnd).getTime();
    const r = rand(hash(beach.id));
    const series = [];
    let rainPulse = 0;
    let turbidityPulse = 0;

    for (let ts = start; ts <= end; ts += stepMs) {
      const d = new Date(ts);
      const doy = Math.floor((ts - Date.UTC(d.getUTCFullYear(), 0, 0)) / DAY_MS);
      const seasonal = 0.5 + 0.5 * Math.sin((doy / 365) * Math.PI * 2 - 0.8);
      if (r() > 0.975) rainPulse = 0.72 + r() * 0.27;
      else rainPulse *= 0.94;
      if (rainPulse > 0.55) turbidityPulse = Math.max(turbidityPulse, rainPulse * (0.76 + r() * 0.18));
      else turbidityPulse *= 0.92;
      const rainPct = Math.min(0.99, 0.18 + seasonal * 0.13 + rainPulse);
      const turbidityPct = Math.min(0.99, 0.18 + turbidityPulse);
      const sstAnomaly = Math.max(-0.5, Math.min(2.2, -0.1 + seasonal * 0.8 + (r() > 0.985 ? 1.2 : 0)));
      const recentTagDetected = r() > 0.9985;
      const blackout = r() > 0.992;
      const partial = !blackout && r() > 0.96;
      const surveillance = blackout
        ? { droneActive: false, lifeguardActive: false, turbidityDataOk: r() > 0.5 }
        : partial
          ? { droneActive: false, lifeguardActive: true, turbidityDataOk: true }
          : { droneActive: true, lifeguardActive: true, turbidityDataOk: true };
      const raw = window.FourNICO.evaluateBeachStatus({ rainPct, turbidityPct, sstAnomaly, recentTagDetected }, surveillance);
      series.push({ timestamp: new Date(ts).toISOString(), ...raw });
    }
    return series;
  }

  function analyseSeries(series, holdHours) {
    const stable = window.FourNICO.stabilizeTimeline(series, holdHours);
    const counts = { GREEN: 0, ORANGE: 0, RED: 0, RED_BLACK: 0, OTHER_BLACK: 0 };
    let transitions = 0;
    let previous = null;
    stable.forEach(s => {
      const composite = s.obsState === 'BLACKOUT' ? `${s.stableEnvFlag}_BLACK` : s.stableEnvFlag;
      if (composite === 'RED_BLACK') counts.RED_BLACK++;
      else if (s.obsState === 'BLACKOUT') counts.OTHER_BLACK++;
      else counts[s.stableEnvFlag]++;
      if (previous !== null && previous !== composite) transitions++;
      previous = composite;
    });
    const n = stable.length || 1;
    const pct = Object.fromEntries(Object.entries(counts).map(([k, v]) => [k, (v / n) * 100]));
    return { stable, counts, pct, transitions, transitionsPerMonth: transitions / MONTHS_IN_WINDOW };
  }

  function incidentStats(incident) {
    const rows = incident.profile.map(p => {
      const result = window.FourNICO.evaluateBeachStatus(p, p.surveillance);
      return { ...p, result };
    });
    const advisory = rows.find(r => r.result.envFlag !== 'GREEN' || r.result.obsState === 'BLACKOUT');
    const firstOrange = rows.find(r => r.result.envFlag === 'ORANGE' || r.result.envFlag === 'RED');
    const firstRed = rows.find(r => r.result.envFlag === 'RED');
    const firstBlack = rows.find(r => r.result.obsState === 'BLACKOUT');
    const at = h => rows.find(r => r.hoursToEvent === h) || null;
    return {
      incident,
      rows,
      lead: {
        firstAdvisoryHours: advisory ? Math.abs(advisory.hoursToEvent) : null,
        orangeHours: firstOrange ? Math.abs(firstOrange.hoursToEvent) : null,
        redHours: firstRed ? Math.abs(firstRed.hoursToEvent) : null,
        blackoutHours: firstBlack ? Math.abs(firstBlack.hoursToEvent) : null
      },
      checkpoints: [-24, -12, 0].map(h => ({ hours: h, row: at(h) }))
    };
  }

  function fmtPct(v) { return `${v.toFixed(1)}%`; }

  function renderAnalytics(beaches) {
    const body = document.getElementById('analytics-body');
    if (!body) return;
    const hold = Number(document.getElementById('hold-hours')?.value || window.FourNICOConfig.hysteresis.holdHours);
    body.innerHTML = beaches.map(beach => {
      const a = analyseSeries(generateDemoSeries(beach), hold);
      return `<tr><td><strong>${beach.name}</strong></td><td>${fmtPct(a.pct.GREEN)}</td><td>${fmtPct(a.pct.ORANGE)}</td><td>${fmtPct(a.pct.RED)}</td><td>${fmtPct(a.pct.RED_BLACK)}</td><td>${fmtPct(a.pct.OTHER_BLACK)}</td><td>${a.transitionsPerMonth.toFixed(1)}/mo</td></tr>`;
    }).join('');
    const note = document.getElementById('analytics-provenance');
    if (note) note.textContent = `18-month deterministic demonstration series · ${hold}h de-escalation hold · NOT measured environmental history. Replace with authoritative archived feeds for DPI validation.`;
  }

  function renderIncidentMatrix(history) {
    const wrap = document.getElementById('incident-matrix');
    if (!wrap) return;
    wrap.innerHTML = history.incidents.map(incident => {
      const s = incidentStats(incident);
      const lead = s.lead.firstAdvisoryHours == null ? 'No configured pre-event elevation' : `First advisory T-${s.lead.firstAdvisoryHours}h`;
      const cells = s.checkpoints.map(cp => {
        if (!cp.row) return '<td>n/a</td>';
        const r = cp.row.result;
        return `<td><div class="matrix-baseline">Without 4NICO: no integrated advisory</div><strong>${r.envFlag}${r.obsState === 'BLACKOUT' ? ' [UNMONITORED]' : ''}</strong><div class="small">Env ${r.envScore} · Obs ${r.confScore}/3</div></td>`;
      }).join('');
      return `<tr data-incident-id="${incident.id}" class="incident-row"><td><button class="incident-select" data-incident="${incident.id}">${incident.name}</button><div class="small">${incident.eventClass}</div></td><td><strong>${lead}</strong><div class="small">Orange ${s.lead.orangeHours == null ? '—' : `T-${s.lead.orangeHours}h`} · Red ${s.lead.redHours == null ? '—' : `T-${s.lead.redHours}h`} · Blackout ${s.lead.blackoutHours == null ? '—' : `T-${s.lead.blackoutHours}h`}</div></td>${cells}</tr>`;
    }).join('');
  }

  window.FourNICOAnalytics = Object.freeze({ generateDemoSeries, analyseSeries, incidentStats, renderAnalytics, renderIncidentMatrix });
})();
