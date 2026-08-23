(function () {
  'use strict';

  /**
   * 4NICO deterministic beach status evaluator.
   *
   * Purpose:
   * - Communicate relative shark-related environmental conditions.
   * - Communicate observation confidence.
   * - NOT predict shark attacks.
   *
   * The scoring and resolution hierarchy below intentionally mirrors the
   * supplied specification. No additional weights or hidden modifiers are used.
   */
  function evaluateBeachStatus(envMetrics, surveillanceState) {
    const {
      rainPct,
      turbidityPct,
      sstAnomaly,
      recentTagDetected
    } = envMetrics;

    const {
      droneActive,
      lifeguardActive,
      turbidityDataOk
    } = surveillanceState;

    // Calculate Observation Confidence
    let confScore = 0;
    if (droneActive) confScore++;
    if (lifeguardActive) confScore++;
    if (turbidityDataOk) confScore++;

    // Calculate Environmental Score
    let envScore = 0;

    if (rainPct >= 0.90) envScore += 2;
    else if (rainPct >= 0.75) envScore += 1;

    if (turbidityPct >= 0.80) envScore += 2;
    else if (turbidityPct >= 0.50) envScore += 1;

    if (sstAnomaly >= 1.5) envScore += 1;
    if (recentTagDetected) envScore += 3;

    // Apply Priority Hierarchy: Black > Red > Orange > Green
    if (confScore <= 1) {
      return {
        flag: 'BLACK',
        label: 'Uncertain / No Monitoring',
        conf: 'LOW',
        score: envScore
      };
    }

    if (envScore >= 3 || recentTagDetected) {
      return {
        flag: 'RED',
        label: 'High Risk Conditions',
        conf: confScore >= 2 ? 'MED/HIGH' : 'LOW',
        score: envScore
      };
    }

    if (envScore >= 2) {
      return {
        flag: 'ORANGE',
        label: 'Elevated Risk Conditions',
        conf: 'MED/HIGH',
        score: envScore
      };
    }

    return {
      flag: 'GREEN',
      label: 'Normal Baseline',
      conf: 'HIGH',
      score: envScore
    };
  }

  // Browser API for GitHub Pages.
  window.FourNICO = Object.freeze({
    evaluateBeachStatus
  });
})();
