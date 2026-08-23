(function () {
  'use strict';

  let history = null;

  function qs(id) { return document.getElementById(id); }

  function renderSnapshot(index) {
    if (!history || !history.snapshots.length) return;
    const snapshot = history.snapshots[index];
    qs('timeline-label').textContent = snapshot.label;
    qs('timeline-time').textContent = new Date(snapshot.timestamp).toLocaleString('en-AU', {
      dateStyle: 'medium', timeStyle: 'short'
    });
    qs('timeline-index').textContent = `${index + 1} / ${history.snapshots.length}`;
    window.FourNICOUI.setSnapshot(snapshot);
  }

  function init(data) {
    history = data;
    const slider = qs('timeline-slider');
    slider.min = 0;
    slider.max = Math.max(0, data.snapshots.length - 1);
    slider.step = 1;
    slider.value = 0;
    slider.addEventListener('input', () => renderSnapshot(Number(slider.value)));

    qs('timeline-start').textContent = new Date(data.window.start).toLocaleDateString('en-AU');
    qs('timeline-end').textContent = new Date(data.window.end).toLocaleDateString('en-AU');
    qs('replay-provenance').textContent = data.provenance.environmentalSnapshots;
    renderSnapshot(0);
  }

  window.FourNICOSimulator = Object.freeze({ init, renderSnapshot });
})();
