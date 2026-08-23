(function () {
  'use strict';

  const state = { beaches: [], selectedBeachId: null, currentSnapshot: null, overrides: {}, previousByBeach: {} };
  function qs(id) { return document.getElementById(id); }

  function loadOverrides() { try { state.overrides = JSON.parse(localStorage.getItem(window.FourNICOConfig.storageKeys.overrides) || '{}'); } catch (_) { state.overrides = {}; } }
  function saveOverrides() { localStorage.setItem(window.FourNICOConfig.storageKeys.overrides, JSON.stringify(state.overrides)); }

  function effectiveResult(beach, result) {
    const override = state.overrides[beach.id];
    if (!override || !override.active) return result;
    const envFlag = override.envFlag || result.envFlag;
    const obsState = override.obsState || result.obsState;
    return { ...result, envFlag, obsState, compositeFlag: obsState === 'BLACKOUT' ? `${envFlag}_BLACK` : envFlag, rationale: [...result.rationale, `Manual lifeguard override: ${override.note || 'no note supplied'}`] };
  }

  function statusLabel(result) {
    const env = result.envFlag === 'GREEN' ? 'Normal baseline conditions' : result.envFlag === 'ORANGE' ? 'Elevated shark-related conditions' : 'High shark-related conditions';
    const obs = result.obsState === 'BLACKOUT' ? 'Surveillance blackout / blind spot' : result.obsState === 'MODERATE' ? 'Partial observation capability' : 'High observation capability';
    return `${env}. ${obs}.`;
  }

  function primaryDrivers(prevEnv, env) {
    const out = [];
    if (prevEnv) {
      if (prevEnv.rainPct < .75 && env.rainPct >= .75) out.push(`72h Rainfall exceeded 75th percentile (${Math.round(prevEnv.rainPct*100)}th -> ${Math.round(env.rainPct*100)}th percentile)`);
      if (prevEnv.rainPct < .90 && env.rainPct >= .90) out.push(`72h Rainfall exceeded 90th percentile (${Math.round(prevEnv.rainPct*100)}th -> ${Math.round(env.rainPct*100)}th percentile)`);
      if (prevEnv.turbidityPct < .50 && env.turbidityPct >= .50) out.push(`Water clarity reduced (turbidity crossed 50th percentile)`);
      if (prevEnv.turbidityPct < .80 && env.turbidityPct >= .80) out.push(`Water clarity materially reduced (turbidity crossed 80th percentile)`);
      if (!prevEnv.recentTagDetected && env.recentTagDetected) out.push('New tagged-shark detection entered the recent-activity window');
    }
    return out;
  }

  function renderDelta(beach, env, result) {
    const box = qs('trigger-delta');
    if (!box) return;
    const prev = state.previousByBeach[beach.id];
    state.previousByBeach[beach.id] = { env: { ...env }, result: { ...result } };
    if (!prev || (prev.result.envFlag === result.envFlag && prev.result.obsState === result.obsState)) { box.classList.add('hidden'); return; }
    const when = state.currentSnapshot?.timestamp ? new Date(state.currentSnapshot.timestamp).toLocaleString('en-AU', { dateStyle:'medium', timeStyle:'short' }) : new Date().toLocaleTimeString('en-AU');
    const drivers = primaryDrivers(prev.env, env);
    const obsDelta = prev.result.obsState !== result.obsState ? `Observation: ${prev.result.obsState} -> ${result.obsState}` : '';
    box.innerHTML = `<strong>STATE CHANGE AT ${when}: ${prev.result.envFlag}${prev.result.obsState==='BLACKOUT'?' [UNMONITORED]':''} → ${result.envFlag}${result.obsState==='BLACKOUT'?' [UNMONITORED]':''}</strong><div>Primary Driver: ${drivers[0] || result.rationale[0]}</div>${drivers[1] ? `<div>Secondary Driver: ${drivers[1]}</div>` : ''}${obsDelta ? `<div>${obsDelta}</div>` : ''}`;
    box.classList.remove('hidden');
  }

  function renderPrimary(beach, env, surveillance) {
    const base = window.FourNICO.evaluateBeachStatus(env, surveillance);
    const result = effectiveResult(beach, base);
    qs('status-card').dataset.env = result.envFlag;
    qs('status-card').classList.toggle('blackout-card', result.obsState === 'BLACKOUT');
    qs('status-flag').textContent = result.envFlag;
    qs('obs-badge').textContent = result.obsState === 'BLACKOUT' ? 'SURVEILLANCE BLACKOUT' : result.obsState;
    qs('obs-badge').dataset.obs = result.obsState;
    qs('status-label').textContent = statusLabel(result);
    qs('env-score').textContent = result.envScore;
    qs('conf-score').textContent = `${result.confScore}/3`;
    qs('beach-name').textContent = beach.name;
    qs('updated-time').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    qs('rationale').innerHTML = result.rationale.map(x => `<li>${x}</li>`).join('');
    renderDelta(beach, env, result);
    return result;
  }

  function renderBeachGrid(snapshot) {
    const grid = qs('beach-grid'); grid.innerHTML = '';
    state.beaches.forEach(beach => {
      const { env, surveillance } = window.FourNICOIngestion.mergeSnapshot(beach, snapshot);
      const result = effectiveResult(beach, window.FourNICO.evaluateBeachStatus(env, surveillance));
      const card = document.createElement('article'); card.className = `mini-card${result.obsState === 'BLACKOUT' ? ' blackout-card' : ''}`; card.dataset.env = result.envFlag;
      card.innerHTML = `<h4>${beach.name}</h4><div class="state">${result.envFlag}</div><span class="obs-badge" data-obs="${result.obsState}">${result.obsState === 'BLACKOUT' ? 'SURVEILLANCE BLACKOUT' : result.obsState}</span><div class="override-note">Env ${result.envScore} · Obs ${result.confScore}/3</div>`;
      grid.appendChild(card);
    });
  }

  function renderOverrides() {
    const wrap = qs('override-list'); wrap.innerHTML = '';
    state.beaches.forEach(beach => {
      const current = state.overrides[beach.id] || { active:false, envFlag:'', obsState:'', note:'' };
      const row = document.createElement('div'); row.className = 'override-row';
      row.innerHTML = `<strong>${beach.name}</strong><select data-field="envFlag"><option value="">Auto env</option><option>GREEN</option><option>ORANGE</option><option>RED</option></select><select data-field="obsState"><option value="">Auto obs</option><option>HIGH</option><option>MODERATE</option><option>BLACKOUT</option></select><button type="button">${current.active ? 'Clear' : 'Apply'}</button><input data-field="note" type="text" placeholder="Override reason" value="${current.note || ''}" />`;
      row.querySelector('[data-field="envFlag"]').value = current.envFlag || ''; row.querySelector('[data-field="obsState"]').value = current.obsState || '';
      row.querySelector('button').addEventListener('click', () => { if (current.active) delete state.overrides[beach.id]; else state.overrides[beach.id] = { active:true, envFlag:row.querySelector('[data-field="envFlag"]').value, obsState:row.querySelector('[data-field="obsState"]').value, note:row.querySelector('[data-field="note"]').value.trim(), updatedAt:new Date().toISOString() }; saveOverrides(); renderOverrides(); renderCurrent(); });
      wrap.appendChild(row);
    });
  }

  function renderCurrent() { const beach = state.beaches.find(b => b.id === state.selectedBeachId) || state.beaches[0]; if (!beach) return; const merged = window.FourNICOIngestion.mergeSnapshot(beach, state.currentSnapshot); renderPrimary(beach, merged.env, merged.surveillance); renderBeachGrid(state.currentSnapshot); }
  function init(beaches) { state.beaches = beaches; state.selectedBeachId = window.FourNICOConfig.pilot.defaultBeachId; loadOverrides(); const picker = qs('beach-picker'); picker.innerHTML = beaches.map(b => `<option value="${b.id}">${b.name}</option>`).join(''); picker.value = state.selectedBeachId; picker.addEventListener('change', () => { state.selectedBeachId = picker.value; renderCurrent(); }); renderOverrides(); renderCurrent(); }
  function setSnapshot(snapshot) { state.currentSnapshot = snapshot; renderCurrent(); }
  window.FourNICOUI = Object.freeze({ init, setSnapshot, renderCurrent });
})();
