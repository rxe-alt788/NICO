(function () {
  'use strict';

  const severity = Object.freeze({ GREEN: 0, ORANGE: 1, RED: 2 });

  function evaluateBeachStatus(envMetrics, surveillanceState) {
    const cfg = window.FourNICOConfig;
    const t = cfg.thresholds;
    const w = cfg.weights;
    const rainPct = Number(envMetrics.rainPct ?? 0);
    const turbidityPct = Number(envMetrics.turbidityPct ?? 0);
    const sstAnomaly = Number(envMetrics.sstAnomaly ?? 0);
    const recentTagDetected = Boolean(envMetrics.recentTagDetected);
    const droneActive = Boolean(surveillanceState.droneActive);
    const lifeguardActive = Boolean(surveillanceState.lifeguardActive);
    const turbidityDataOk = Boolean(surveillanceState.turbidityDataOk);

    let confScore = 0;
    if (droneActive) confScore++;
    if (lifeguardActive) confScore++;
    if (turbidityDataOk) confScore++;

    let envScore = 0;
    const rationale = [];
    if (rainPct >= t.rainfall.p90) { envScore += w.rainP90; rationale.push('72h Rainfall > 90th percentile'); }
    else if (rainPct >= t.rainfall.p75) { envScore += w.rainP75; rationale.push('72h Rainfall > 75th percentile'); }
    if (turbidityPct >= t.turbidity.p80) { envScore += w.turbidityP80; rationale.push('Turbidity > 80th percentile'); }
    else if (turbidityPct >= t.turbidity.p50) { envScore += w.turbidityP50; rationale.push('Turbidity > 50th percentile'); }
    if (sstAnomaly >= t.sstAnomalyC) { envScore += w.sstAnomaly; rationale.push(`SST anomaly >= +${t.sstAnomalyC.toFixed(1)}°C`); }
    if (recentTagDetected) { envScore += w.recentTag; rationale.push('Recent tagged shark detection'); }

    let envFlag = 'GREEN';
    if (envScore >= cfg.envFlags.redMin || recentTagDetected) envFlag = 'RED';
    else if (envScore >= cfg.envFlags.orangeMin) envFlag = 'ORANGE';

    let obsState = 'HIGH';
    if (confScore <= cfg.observation.blackoutMax) { obsState = 'BLACKOUT'; rationale.push('Surveillance offline or materially degraded'); }
    else if (confScore === cfg.observation.moderate) { obsState = 'MODERATE'; rationale.push('Partial surveillance coverage'); }

    const compositeFlag = obsState === 'BLACKOUT' ? `${envFlag}_BLACK` : envFlag;
    if (!rationale.length) rationale.push('No configured elevated-condition triggers');
    return Object.freeze({ envFlag, obsState, compositeFlag, envScore, confScore, rationale });
  }

  function createHysteresisState(initialFlag) {
    return { stableFlag: initialFlag || 'GREEN', lowerCandidate: null, lowerSince: null };
  }

  function applyHysteresis(hState, candidateFlag, timestamp, holdHours) {
    const state = hState || createHysteresisState(candidateFlag);
    const hold = Number(holdHours ?? window.FourNICOConfig.hysteresis.holdHours);
    const now = new Date(timestamp).getTime();
    const stable = state.stableFlag;

    if (severity[candidateFlag] >= severity[stable]) {
      state.stableFlag = candidateFlag;
      state.lowerCandidate = null;
      state.lowerSince = null;
      return { flag: state.stableFlag, held: false, remainingHours: 0, state };
    }

    if (state.lowerCandidate !== candidateFlag) {
      state.lowerCandidate = candidateFlag;
      state.lowerSince = timestamp;
    }
    const elapsedHours = Math.max(0, (now - new Date(state.lowerSince).getTime()) / 3600000);
    if (elapsedHours >= hold) {
      state.stableFlag = candidateFlag;
      state.lowerCandidate = null;
      state.lowerSince = null;
      return { flag: state.stableFlag, held: false, remainingHours: 0, state };
    }
    return { flag: stable, held: true, remainingHours: Math.max(0, hold - elapsedHours), state };
  }

  function stabilizeTimeline(samples, holdHours) {
    let hState = createHysteresisState(samples[0] ? samples[0].envFlag : 'GREEN');
    return samples.map((sample, index) => {
      if (index === 0) return { ...sample, stableEnvFlag: hState.stableFlag, hysteresisHeld: false, remainingHours: 0 };
      const applied = applyHysteresis(hState, sample.envFlag, sample.timestamp, holdHours);
      hState = applied.state;
      return { ...sample, stableEnvFlag: applied.flag, hysteresisHeld: applied.held, remainingHours: applied.remainingHours };
    });
  }

  window.FourNICO = Object.freeze({ evaluateBeachStatus, createHysteresisState, applyHysteresis, stabilizeTimeline });
})();
