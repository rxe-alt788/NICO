(function () {
  'use strict';

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

    if (rainPct >= t.rainfall.p90) {
      envScore += w.rainP90;
      rationale.push('72h Rainfall > 90th percentile');
    } else if (rainPct >= t.rainfall.p75) {
      envScore += w.rainP75;
      rationale.push('72h Rainfall > 75th percentile');
    }

    if (turbidityPct >= t.turbidity.p80) {
      envScore += w.turbidityP80;
      rationale.push('Turbidity > 80th percentile');
    } else if (turbidityPct >= t.turbidity.p50) {
      envScore += w.turbidityP50;
      rationale.push('Turbidity > 50th percentile');
    }

    if (sstAnomaly >= t.sstAnomalyC) {
      envScore += w.sstAnomaly;
      rationale.push(`SST anomaly >= +${t.sstAnomalyC.toFixed(1)}°C`);
    }

    if (recentTagDetected) {
      envScore += w.recentTag;
      rationale.push('Recent tagged shark detection');
    }

    let envFlag = 'GREEN';
    if (envScore >= cfg.envFlags.redMin || recentTagDetected) envFlag = 'RED';
    else if (envScore >= cfg.envFlags.orangeMin) envFlag = 'ORANGE';

    let obsState = 'HIGH';
    if (confScore <= cfg.observation.blackoutMax) {
      obsState = 'BLACKOUT';
      rationale.push('Surveillance offline or materially degraded');
    } else if (confScore === cfg.observation.moderate) {
      obsState = 'MODERATE';
      rationale.push('Partial surveillance coverage');
    }

    const compositeFlag = obsState === 'BLACKOUT' ? `${envFlag}_BLACK` : envFlag;

    if (rationale.length === 0) rationale.push('No configured elevated-condition triggers');

    return Object.freeze({
      envFlag,
      obsState,
      compositeFlag,
      envScore,
      confScore,
      rationale
    });
  }

  window.FourNICO = Object.freeze({ evaluateBeachStatus });
})();
