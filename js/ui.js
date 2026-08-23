(function () {
  'use strict';

  const state = {
    beaches: [],
    selectedBeachId: null,
    currentSnapshot: null,
    overrides: {}
  };

  function qs(id) { return document.getElementById(id); }

  function loadOverrides() {
    try {
      state.overrides = JSON.parse(localStorage.getItem(window.FourNICOConfig.storageKeys.overrides) || '{}');
    } catch (_) {
      state.overrides = {};
    }
  }

  function saveOverrides() {
    localStorage.setItem(window.FourNICOConfig.storageKeys.overrides, JSON.stringify(state.overrides));
  }

  function effectiveResult(beach, result) {
    const override = state.overrides[beach.id];
    if (!override || !override.active) return result;
    return {
      ...result,
      envFlag: override.envFlag || result.envFlag,
      obsState: override.obsState || result.obsState,
      compositeFlag: (override.obsState || result.obsState) === 'BLACKOUT'
        ? `${override.envFlag || result.envFlag}_BLACK`
        : (override.envFlag || result.envFlag),
      rationale: [...result.rationale, `Manual lifeguard override: ${override.note || 'no note supplied'}`]
    };
  }

  function statusLabel(result) {
    const env = result.envFlag === 'GREEN' ? 'Normal baseline conditions'
      : result.envFlag === 'ORANGE' ? 'Elevated shark-related conditions'
      : 'High shark-related conditions';
    const obs = result.obsState === 'BLACKOUT' ? 'Unmonitored / surveillance blind spot'
      : result.obsState === 'MODERATE' ? 'Partial observation capability'
      : 'High observation capability';
    return `${env}. ${obs}.`;
  }

  function renderPrimary(beach, env, surveillance) {
    const base = window.FourNICO.evaluateBeachStatus(env, surveillance);
    const result = effectiveResult(beach, base);
    qs('status-card').dataset.env = result.envFlag;
    qs('status-flag').textContent = result.envFlag;
    qs('obs-badge').textContent = result.obsState === 'BLACKOUT' ? 'UNMONITORED' : result.obsState;
    qs('obs-badge').dataset.obs = result.obsState;
    qs('status-label').textContent = statusLabel(result);
    qs('env-score').textContent = result.envScore;
    qs('conf-score').textContent = `${result.confScore}/3`;
    qs('beach-name').textContent = beach.name;
    qs('updated-time').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    qs('rationale').innerHTML = result.rationale.map(x => `<li>${x}</li>`).join('');
    return result;
  }

  function renderBeachGrid(snapshot) {
    const grid = qs('beach-grid');
    grid.innerHTML = '';
    state.beaches.forEach(beach => {
      const { env, surveillance } = window.FourNICOIngestion.mergeSnapshot(beach, snapshot);
      const result = effectiveResult(beach, window.FourNICO.evaluateBeachStatus(env, surveillance));
      const card = document.createElement('article');
      card.className = 'mini-card';
      card.dataset.env = result.envFlag;
      card.innerHTML = `<h4>${beach.name}</h4><div class="state">${result.envFlag}${result.obsState === 'BLACKOUT' ? ' [UNMONITORED]' : ''}</div><div class="override-note">Env ${result.envScore} · Obs ${result.confScore}/3 · ${result.obsState}</div>`;
      grid.appendChild(card);
    });
  }

  function renderOverrides() {
    const wrap = qs('override-list');
    wrap.innerHTML = '';
    state.beaches.forEach(beach => {
      const current = state.overrides[beach.id] || { active: false, envFlag: '', obsState: '', note: '' };
      const row = document.createElement('div');
      row.className = 'override-row';
      row.innerHTML = `
        <strong>${beach.name}</strong>
        <select data-field="envFlag"><option value="">Auto env</option><option>GREEN</option><option>ORANGE</option><option>RED</option></select>
        <select data-field="obsState"><option value="">Auto obs</option><option>HIGH</option><option>MODERATE</option><option>BLACKOUT</option></select>
        <button type="button">${current.active ? 'Clear' : 'Apply'}</button>
        <input data-field="note" type="text" placeholder="Override reason" value="${current.note || ''}" />`;
      row.querySelector('[data-field="envFlag"]').value = current.envFlag || '';
      row.querySelector('[data-field="obsState"]').value = current.obsState || '';
      row.querySelector('button').addEventListener('click', () => {
        if (current.active) {
          delete state.overrides[beach.id];
        } else {
          const envFlag = row.querySelector('[data-field="envFlag"]').value;
          const obsState = row.querySelector('[data-field="obsState"]').value;
          const note = row.querySelector('[data-field="note"]').value.trim();
          state.overrides[beach.id] = { active: true, envFlag, obsState, note, updatedAt: new Date().toISOString() };
        }
        saveOverrides();
        renderOverrides();
        renderCurrent();
      });
      wrap.appendChild(row);
    });
  }

  function renderCurrent() {
    const beach = state.beaches.find(b => b.id === state.selectedBeachId) || state.beaches[0];
    if (!beach) return;
    const merged = window.FourNICOIngestion.mergeSnapshot(beach, state.currentSnapshot);
    renderPrimary(beach, merged.env, merged.surveillance);
    renderBeachGrid(state.currentSnapshot);
  }

  function init(beaches) {
    state.beaches = beaches;
    state.selectedBeachId = window.FourNICOConfig.pilot.defaultBeachId;
    loadOverrides();
    const picker = qs('beach-picker');
    picker.innerHTML = beaches.map(b => `<option value="${b.id}">${b.name}</option>`).join('');
    picker.value = state.selectedBeachId;
    picker.addEventListener('change', () => { state.selectedBeachId = picker.value; renderCurrent(); });
    renderOverrides();
    renderCurrent();
  }

  function setSnapshot(snapshot) {
    state.currentSnapshot = snapshot;
    renderCurrent();
  }

  window.FourNICOUI = Object.freeze({ init, setSnapshot, renderCurrent });
})();
