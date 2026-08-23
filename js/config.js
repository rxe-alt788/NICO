(function () {
  'use strict';

  const CONFIG = Object.freeze({
    version: '0.2.0-pilot',
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
    envFlags: Object.freeze({
      greenMax: 1,
      orangeMin: 2,
      redMin: 3
    }),
    observation: Object.freeze({
      blackoutMax: 1,
      moderate: 2,
      high: 3
    }),
    storageKeys: Object.freeze({
      overrides: '4nico.lifeguardOverrides.v1'
    }),
    pilot: Object.freeze({
      defaultBeachId: 'north-steyne',
      replayStart: '2026-01-15T16:20:00+11:00',
      replayEnd: '2026-01-20T16:20:00+11:00'
    })
  });

  window.FourNICOConfig = CONFIG;
})();
