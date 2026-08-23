(function () {
  'use strict';

  let history = null;
  let selectedIncident = null;
  function qs(id) { return document.getElementById(id); }

  function profileTimestamp(incident, hoursToEvent) {
    return new Date(new Date(incident.timestamp).getTime() + hoursToEvent * 3600000).toISOString();
  }

  function renderProfilePoint(index) {
    if (!selectedIncident) return;
    const point = selectedIncident.profile[index];
    const result = window.FourNICO.evaluateBeachStatus(point, point.surveillance);
    const ts = profileTimestamp(selectedIncident, point.hoursToEvent);
    qs('timeline-label').textContent = point.hoursToEvent === 0 ? 'INCIDENT' : `T${point.hoursToEvent}h`;
    qs('timeline-time').textContent = new Date(ts).toLocaleString('en-AU', { dateStyle:'medium', timeStyle:'short' });
    qs('timeline-index').textContent = `${index + 1} / ${selectedIncident.profile.length}`;
    qs('incident-replay-state').innerHTML = `<strong>${selectedIncident.name}: ${result.envFlag}${result.obsState === 'BLACKOUT' ? ' [UNMONITORED]' : ''}</strong><div>Env ${result.envScore} · Obs ${result.confScore}/3</div><div>${result.rationale.join(' · ')}</div>`;

    const snapshot = { timestamp: ts, label: qs('timeline-label').textContent, global:{}, beaches:{} };
    snapshot.beaches[selectedIncident.beachId] = {
      rainPct: point.rainPct, turbidityPct: point.turbidityPct, sstAnomaly: point.sstAnomaly,
      recentTagDetected: Boolean(point.recentTagDetected), surveillance: point.surveillance
    };
    window.FourNICOUI.setSnapshot(snapshot);
  }

  function selectIncident(id) {
    selectedIncident = history.incidents.find(x => x.id === id) || history.incidents[0];
    const slider = qs('timeline-slider');
    slider.min = 0; slider.max = selectedIncident.profile.length - 1; slider.step = 1; slider.value = 0;
    qs('timeline-start').textContent = 'T-72h'; qs('timeline-end').textContent = 'T-0h';
    qs('incident-selector').value = selectedIncident.id;
    window.FourNICOUI.selectBeach(selectedIncident.beachId);
    renderProfilePoint(0);
  }

  function init(data) {
    history = data;
    const selector = qs('incident-selector');
    selector.innerHTML = data.incidents.map(i => `<option value="${i.id}">${i.name}</option>`).join('');
    selector.addEventListener('change', () => selectIncident(selector.value));
    qs('timeline-slider').addEventListener('input', e => renderProfilePoint(Number(e.target.value)));
    qs('replay-provenance').textContent = data.provenance.environmentalProfiles;
    window.FourNICOAnalytics.renderIncidentMatrix(data);
    document.querySelectorAll('[data-incident]').forEach(btn => btn.addEventListener('click', () => selectIncident(btn.dataset.incident)));
    selectIncident(data.incidents[0].id);
  }

  window.FourNICOSimulator = Object.freeze({ init, selectIncident, renderProfilePoint });
})();
