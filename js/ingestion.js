(function () {
  'use strict';

  async function fetchJson(path) {
    const response = await fetch(path, { cache: 'no-store' });
    if (!response.ok) throw new Error(`Failed to load ${path}: ${response.status}`);
    return response.json();
  }

  async function loadPilotBeaches() {
    return fetchJson('data/pilot_beaches.json');
  }

  async function loadIncidentHistory() {
    return fetchJson('data/incident_history.json');
  }

  function defaultEnvironmentalState(beach) {
    return {
      rainPct: 0.25,
      turbidityPct: 0.25,
      sstAnomaly: 0,
      recentTagDetected: false,
      beachId: beach.id
    };
  }

  function defaultSurveillanceState() {
    return {
      droneActive: true,
      lifeguardActive: true,
      turbidityDataOk: true
    };
  }

  function mergeSnapshot(beach, snapshot) {
    const env = defaultEnvironmentalState(beach);
    const surveillance = defaultSurveillanceState();
    if (!snapshot) return { env, surveillance };

    Object.assign(env, snapshot.global || {});
    const local = (snapshot.beaches || {})[beach.id] || {};
    Object.assign(env, local);
    if (local.surveillance) Object.assign(surveillance, local.surveillance);
    delete env.surveillance;

    return { env, surveillance };
  }

  window.FourNICOIngestion = Object.freeze({
    loadPilotBeaches,
    loadIncidentHistory,
    defaultEnvironmentalState,
    defaultSurveillanceState,
    mergeSnapshot
  });
})();
