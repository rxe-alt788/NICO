(function () {
  'use strict';

  const CONFIG = Object.freeze({
    version: '0.4.0-empirical-bridge',
    thresholds: Object.freeze({
      rainfall: Object.freeze({ p75: 0.75, p90: 0.90 }),
      turbidity: Object.freeze({ p50: 0.50, p80: 0.80 }),
      sstAnomalyC: 1.5,
      recentTagHours: 24
    }),
    weights: Object.freeze({
      rainP75: 1,
      rainP90: 2,
      turbidityP50: 1,
      turbidityP80: 2,
      sstAnomaly: 1,
      recentTag: 3
    }),
    experimental: Object.freeze({
      secondaryCues: Object.freeze({
        enabledByDefault: false,
        status: 'PROVISIONAL_NOT_VALIDATED',
        upwellingAnomalyThreshold: 1.5,
        acousticDensityPctThreshold: 0.90,
        weights: Object.freeze({ upwellingAnomaly: 1, acousticDensity: 1 })
      })
    }),
    envFlags: Object.freeze({ greenMax: 1, orangeMin: 2, redMin: 3 }),
    observation: Object.freeze({ blackoutMax: 1, moderate: 2, high: 3 }),
    hysteresis: Object.freeze({ holdHours: 24, applyTo: 'ENVIRONMENTAL_DEESCALATION_ONLY' }),
    analytics: Object.freeze({
      evaluationStart: '2025-02-23T00:00:00+11:00',
      evaluationEnd: '2026-08-23T23:59:59+10:00',
      demoStepHours: 6,
      provenance: 'DETERMINISTIC_DEMONSTRATION_SERIES_NOT_MEASURED_HISTORY'
    }),
    storageKeys: Object.freeze({ overrides: '4nico.lifeguardOverrides.v1' }),
    pilot: Object.freeze({
      defaultBeachId: 'north-steyne',
      replayStart: '2026-01-15T16:20:00+11:00',
      replayEnd: '2026-06-13T11:00:00+10:00'
    })
  });

  window.FourNICOConfig = CONFIG;
})();
