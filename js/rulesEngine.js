(function () {
  'use strict';

  const severity = Object.freeze({ GREEN: 0, ORANGE: 1, RED: 2 });
  const CORE_FIELDS = Object.freeze(['rainPct', 'turbidityPct', 'sstAnomaly']);

  function finite(v) { return v !== null && v !== undefined && v !== '' && Number.isFinite(Number(v)); }

  function evaluateBeachStatus(envMetrics, surveillanceState, options) {
    const cfg = window.FourNICOConfig;
    const missingCore = CORE_FIELDS.filter(k => !finite(envMetrics?.[k]));
    if (missingCore.length) {
      return Object.freeze({
        envFlag: 'INSUFFICIENT_ENV_DATA',
        obsState: 'BLACKOUT',
        compositeFlag: 'INSUFFICIENT_ENV_DATA_BLACK',
        envScore: null,
        confScore: 0,
        rationale: [`Insufficient environmental data: missing ${missingCore.join(', ')}`],
        experimentalSecondaryCues: false,
        missingCore
      });
    }

    const t = cfg.thresholds; const w = cfg.weights;
    const experimentalEnabled = Boolean(options?.experimentalSecondaryCues ?? cfg.experimental.secondaryCues.enabledByDefault);
    const rainPct = Number(envMetrics.rainPct);
    const turbidityPct = Number(envMetrics.turbidityPct);
    const sstAnomaly = Number(envMetrics.sstAnomaly);
    const recentTagDetected = Boolean(envMetrics.recentTagDetected);
    const droneActive = Boolean(surveillanceState?.droneActive);
    const lifeguardActive = Boolean(surveillanceState?.lifeguardActive);
    const turbidityDataOk = Boolean(surveillanceState?.turbidityDataOk);

    let confScore = 0;
    if (droneActive) confScore++;
    if (lifeguardActive) confScore++;
    if (turbidityDataOk) confScore++;

    let envScore = 0; const rationale = [];
    if (rainPct >= t.rainfall.p90) { envScore += w.rainP90; rationale.push('72h Rainfall > 90th percentile'); }
    else if (rainPct >= t.rainfall.p75) { envScore += w.rainP75; rationale.push('72h Rainfall > 75th percentile'); }
    if (turbidityPct >= t.turbidity.p80) { envScore += w.turbidityP80; rationale.push('Turbidity > 80th percentile'); }
    else if (turbidityPct >= t.turbidity.p50) { envScore += w.turbidityP50; rationale.push('Turbidity > 50th percentile'); }
    if (sstAnomaly >= t.sstAnomalyC) { envScore += w.sstAnomaly; rationale.push(`SST anomaly >= +${t.sstAnomalyC.toFixed(1)}°C`); }
    if (recentTagDetected) { envScore += w.recentTag; rationale.push('Recent tagged shark detection'); }

    if (experimentalEnabled) {
      const e = cfg.experimental.secondaryCues;
      const upwellingAnomaly = Number(envMetrics.upwellingAnomaly ?? envMetrics.upwellingIndex ?? 0);
      const acousticDensityPct = Number(envMetrics.acousticDensityPct ?? envMetrics.seasonalAcousticDensityPct ?? 0);
      if (Math.abs(upwellingAnomaly) >= e.upwellingAnomalyThreshold) {
        envScore += e.weights.upwellingAnomaly;
        rationale.push('EXPERIMENTAL: upwelling anomaly threshold exceeded');
      }
      if (acousticDensityPct >= e.acousticDensityPctThreshold) {
        envScore += e.weights.acousticDensity;
        rationale.push('EXPERIMENTAL: seasonal acoustic tag density >= 90th percentile');
      }
    }

    let envFlag = 'GREEN';
    if (envScore >= cfg.envFlags.redMin || recentTagDetected) envFlag = 'RED';
    else if (envScore >= cfg.envFlags.orangeMin) envFlag = 'ORANGE';

    let obsState = 'HIGH';
    if (confScore <= cfg.observation.blackoutMax) { obsState = 'BLACKOUT'; rationale.push('Surveillance offline or materially degraded'); }
    else if (confScore === cfg.observation.moderate) { obsState = 'MODERATE'; rationale.push('Partial surveillance coverage'); }

    const compositeFlag = obsState === 'BLACKOUT' ? `${envFlag}_BLACK` : envFlag;
    if (!rationale.length) rationale.push('No configured elevated-condition triggers');
    return Object.freeze({ envFlag, obsState, compositeFlag, envScore, confScore, rationale, experimentalSecondaryCues: experimentalEnabled, missingCore: [] });
  }

  function createHysteresisState(initialFlag) { return { stableFlag: initialFlag || 'GREEN', lowerCandidate: null, lowerSince: null }; }

  function applyHysteresis(hState, candidateFlag, timestamp, holdHours) {
    if (!(candidateFlag in severity)) return { flag: candidateFlag, held: false, remainingHours: 0, state: hState || createHysteresisState('GREEN') };
    const state = hState || createHysteresisState(candidateFlag);
    const hold = Number(holdHours ?? window.FourNICOConfig.hysteresis.holdHours);
    const now = new Date(timestamp).getTime(); const stable = state.stableFlag;
    if (!(stable in severity) || severity[candidateFlag] >= severity[stable]) {
      state.stableFlag = candidateFlag; state.lowerCandidate = null; state.lowerSince = null;
      return { flag: state.stableFlag, held: false, remainingHours: 0, state };
    }
    if (state.lowerCandidate !== candidateFlag) { state.lowerCandidate = candidateFlag; state.lowerSince = timestamp; }
    const elapsedHours = Math.max(0, (now - new Date(state.lowerSince).getTime()) / 3600000);
    if (elapsedHours >= hold) {
      state.stableFlag = candidateFlag; state.lowerCandidate = null; state.lowerSince = null;
      return { flag: state.stableFlag, held: false, remainingHours: 0, state };
    }
    return { flag: stable, held: true, remainingHours: Math.max(0, hold - elapsedHours), state };
  }

  function stabilizeTimeline(samples, holdHours) {
    const firstValid = samples.find(s => s.envFlag in severity);
    let hState = createHysteresisState(firstValid ? firstValid.envFlag : 'GREEN');
    return samples.map(sample => {
      if (!(sample.envFlag in severity)) return { ...sample, stableEnvFlag: sample.envFlag, hysteresisHeld: false, remainingHours: 0 };
      const applied = applyHysteresis(hState, sample.envFlag, sample.timestamp, holdHours); hState = applied.state;
      return { ...sample, stableEnvFlag: applied.flag, hysteresisHeld: applied.held, remainingHours: applied.remainingHours };
    });
  }

  window.FourNICO = Object.freeze({ evaluateBeachStatus, createHysteresisState, applyHysteresis, stabilizeTimeline });
})();