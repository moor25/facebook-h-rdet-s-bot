'use strict';

/* ===================================================
   STEP WIZARD
   =================================================== */
let currentStep = 1;
const TOTAL_STEPS = 3; // form steps (4th is the generating panel)

function goToStep(n) {
  // Hide all form steps
  document.querySelectorAll('.step-panel[data-step]').forEach(p => {
    if (p.id === 'generating-panel') return;
    p.classList.remove('active');
  });

  // Update indicator
  document.querySelectorAll('.step-item').forEach(item => {
    const s = parseInt(item.dataset.step);
    item.classList.remove('active', 'done');
    if (s < n) item.classList.add('done');
    else if (s === n) item.classList.add('active');
  });

  document.querySelectorAll('.step-line').forEach((line, i) => {
    line.classList.toggle('done', i + 1 < n);
  });

  if (n <= TOTAL_STEPS) {
    const panel = document.querySelector(`.step-panel[data-step="${n}"]:not(#generating-panel)`);
    if (panel) panel.classList.add('active');
    document.getElementById('generating-panel').classList.remove('active');
  } else {
    // Step 4: generating
    document.querySelector('.step-panel[data-step="3"]:not(#generating-panel)').classList.remove('active');
    document.getElementById('generating-panel').classList.add('active');
    document.querySelectorAll('.step-item').forEach(item => {
      item.classList.remove('active', 'done');
      if (parseInt(item.dataset.step) < 4) item.classList.add('done');
      else item.classList.add('active');
    });
    document.querySelectorAll('.step-line').forEach(l => l.classList.add('done'));
  }

  currentStep = n;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Next buttons
document.querySelectorAll('.btn-next').forEach(btn => {
  btn.addEventListener('click', () => {
    const next = parseInt(btn.dataset.next);
    if (!validateStep(currentStep)) return;
    goToStep(next);
  });
});

// Back buttons
document.querySelectorAll('.btn-back').forEach(btn => {
  btn.addEventListener('click', () => {
    goToStep(parseInt(btn.dataset.back));
  });
});

/* ===================================================
   VALIDATION
   =================================================== */
function validateStep(step) {
  let valid = true;
  const requiredByStep = {
    1: ['brand_name', 'service_type', 'phone', 'website'],
    2: ['main_offer'],
  };
  const fields = requiredByStep[step] || [];
  fields.forEach(name => {
    const el = document.getElementById(name);
    if (!el) return;
    if (!el.value.trim()) { el.classList.add('error'); valid = false; }
    else el.classList.remove('error');
  });

  if (step === 2) {
    const benefits = [...document.querySelectorAll('[name="benefits[]"]')].filter(i => i.value.trim());
    if (benefits.length === 0) { valid = false; }
  }

  if (!valid) {
    const firstError = document.querySelector('.step-panel.active input.error');
    if (firstError) firstError.focus();
  }
  return valid;
}

// Live clear error on input
document.addEventListener('input', (e) => {
  if (e.target.matches('input[type="text"]')) e.target.classList.remove('error');
});

/* ===================================================
   BENEFITS
   =================================================== */
document.getElementById('add-benefit').addEventListener('click', () => {
  const list = document.getElementById('benefits-list');
  if (list.children.length >= 8) return;
  const n = list.children.length + 1;
  const row = document.createElement('div');
  row.className = 'benefit-row';
  row.innerHTML = `
    <div class="benefit-num">${n}</div>
    <input type="text" name="benefits[]" placeholder="pl. Gyors helyszíni kiszállás">
    <button type="button" class="btn-remove-benefit">✕</button>`;
  list.appendChild(row);
  row.querySelector('input').focus();
  renumberBenefits();
});

document.getElementById('benefits-list').addEventListener('click', (e) => {
  if (e.target.classList.contains('btn-remove-benefit')) {
    const list = document.getElementById('benefits-list');
    if (list.children.length > 1) {
      e.target.closest('.benefit-row').remove();
      renumberBenefits();
    }
  }
});

function renumberBenefits() {
  document.querySelectorAll('.benefit-row').forEach((row, i) => {
    const num = row.querySelector('.benefit-num');
    if (num) num.textContent = i + 1;
  });
}

/* ===================================================
   FILE UPLOAD
   =================================================== */
const fileInput = document.getElementById('reference_images');
const filePreview = document.getElementById('file-preview');
const dropZone = document.getElementById('file-drop-zone');

fileInput.addEventListener('change', () => renderPreviews(fileInput.files));
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  renderPreviews(e.dataTransfer.files);
});

function renderPreviews(files) {
  filePreview.innerHTML = '';
  Array.from(files).slice(0, 5).forEach(file => {
    const reader = new FileReader();
    reader.onload = (ev) => {
      const img = document.createElement('img');
      img.src = ev.target.result;
      img.className = 'file-thumb';
      img.alt = file.name;
      filePreview.appendChild(img);
    };
    reader.readAsDataURL(file);
  });
}

/* ===================================================
   FORM SUBMIT
   =================================================== */
document.getElementById('survey-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!validateStep(3)) return;

  goToStep(4);
  resetGeneratingUI();

  const formData = new FormData(document.getElementById('survey-form'));
  let jobId;
  try {
    const resp = await fetch('/generate', { method: 'POST', body: formData });
    if (!resp.ok) throw new Error('Szerver hiba: ' + resp.status);
    jobId = (await resp.json()).job_id;
  } catch (err) {
    showError('Nem sikerült elindítani: ' + err.message);
    return;
  }

  pollStatus(jobId);
});

/* ===================================================
   GENERATING UI
   =================================================== */
function resetGeneratingUI() {
  setProgress(0);
  document.getElementById('gen-title').textContent = 'Generálás folyamatban…';
  document.getElementById('gen-desc').textContent = 'Az AI dolgozik. Ez 60–120 másodpercet vesz igénybe.';
  document.getElementById('generating-card').classList.remove('hidden');
  document.getElementById('results-section').classList.add('hidden');
  document.getElementById('error-card').classList.add('hidden');

  setStepState('copy', 'waiting', 'Várakozik');
  setStepState('images', 'waiting', 'Várakozik');
  setStepState('pdf', 'waiting', 'Várakozik');
}

function setProgress(pct) {
  document.getElementById('gen-progress-fill').style.width = pct + '%';
  document.getElementById('gen-progress-pct').textContent = Math.round(pct) + '%';
}

function setStepState(name, state, label) {
  const item = document.getElementById(`gsi-${name}`);
  const icon = item.querySelector('.gsi-icon');
  const status = document.getElementById(`gsi-${name}-status`);
  item.classList.remove('active', 'done');
  icon.classList.remove('gsi-waiting', 'gsi-active', 'gsi-done');
  if (state === 'active') { item.classList.add('active'); icon.classList.add('gsi-active'); }
  else if (state === 'done') { item.classList.add('done'); icon.classList.add('gsi-done'); }
  else { icon.classList.add('gsi-waiting'); }
  status.textContent = label;
}

/* ===================================================
   POLLING
   =================================================== */
function pollStatus(jobId) {
  let prevStatus = '';
  let slowTick = 5; // slow progress increment

  const interval = setInterval(async () => {
    try {
      const resp = await fetch('/status/' + jobId);
      const json = await resp.json();
      const s = json.status;

      if (s !== prevStatus) {
        prevStatus = s;
        if (s === 'copy') {
          setStepState('copy', 'active', 'Folyamatban…');
          setProgress(15);
        } else if (s === 'images') {
          setStepState('copy', 'done', 'Kész ✓');
          setStepState('images', 'active', 'Folyamatban…');
          setProgress(35);
        } else if (s === 'pdf') {
          setStepState('images', 'done', 'Kész ✓');
          setStepState('pdf', 'active', 'Folyamatban…');
          setProgress(88);
        }
      } else {
        // Slowly nudge progress while waiting
        const fill = parseFloat(document.getElementById('gen-progress-fill').style.width) || 0;
        const targets = { copy: 30, images: 85, pdf: 96 };
        const target = targets[s] || 10;
        if (fill < target) setProgress(Math.min(fill + 0.8, target));
      }

      if (s === 'done') {
        clearInterval(interval);
        setStepState('pdf', 'done', 'Kész ✓');
        setProgress(100);
        setTimeout(() => showResults(jobId, json), 500);
      } else if (s === 'error') {
        clearInterval(interval);
        showError(json.error || 'Ismeretlen hiba történt.');
      }
    } catch (err) { /* network blip */ }
  }, 2500);
}

/* ===================================================
   RESULTS
   =================================================== */
function showResults(jobId, json) {
  document.getElementById('generating-card').classList.add('hidden');
  document.getElementById('results-section').classList.remove('hidden');

  const brand = json.brand_name || 'kreativok';
  const num = json.num_creatives || 6;
  document.getElementById('results-title').textContent = `Kész! ${num} kreatív vár rád.`;
  document.getElementById('results-sub').textContent =
    `${brand} – Nézd meg az előnézetet, majd töltsd le a teljes PDF csomagot.`;

  const pdfUrl = '/download/' + jobId;
  const safeBrand = brand.replace(/[^a-z0-9_-]/gi, '').toLowerCase();
  document.getElementById('download-btn').href = pdfUrl;
  document.getElementById('download-btn').download = safeBrand + '_facebook_kreativok.pdf';
  document.getElementById('download-btn-bottom').href = pdfUrl;
  document.getElementById('download-btn-bottom').download = safeBrand + '_facebook_kreativok.pdf';

  const grid = document.getElementById('creatives-grid');
  grid.innerHTML = '';

  (json.previews || []).forEach(p => {
    const card = buildCreativeCard(jobId, p);
    grid.appendChild(card);
  });

  // Update generating title
  document.getElementById('gen-title').textContent = 'Elkészültek a kreatívok!';
  document.getElementById('gen-desc').textContent = 'Görgess le az előnézethez.';
}

function buildCreativeCard(jobId, p) {
  const adImgUrl = `/preview/${jobId}/${p.index}/ad`;

  const card = document.createElement('div');
  card.className = 'creative-card';

  const bullets = Array.isArray(p.bullets)
    ? p.bullets.map(b => `
        <div class="copy-bullet">
          <div class="copy-bullet-dot"></div>
          <span>${escHtml(b)}</span>
        </div>`).join('')
    : '';

  card.innerHTML = `
    <div class="creative-card-header">
      <span class="creative-card-num">Kreatív #${p.index}</span>
      <span class="creative-card-hook">${escHtml(p.hook || '')}</span>
    </div>
    <div class="creative-card-body">
      <div class="creative-img-wrap" data-img="${adImgUrl}">
        <img src="${adImgUrl}" alt="Kreatív #${p.index}" loading="lazy">
        <div class="creative-img-overlay">
          <span class="zoom-icon">⊕</span>
        </div>
      </div>
      <div class="creative-copy">
        ${p.headline ? `<div class="copy-section">
          <label>Hirdetés headline</label>
          <p><strong>${escHtml(p.headline)}</strong></p>
        </div>` : ''}
        ${p.caption ? `<div class="copy-section">
          <label>Poszt caption</label>
          <p>${escHtml(p.caption)}</p>
        </div>` : ''}
        ${bullets ? `<div class="copy-section">
          <label>Bullet pontok</label>
          <div class="copy-bullets">${bullets}</div>
        </div>` : ''}
        ${p.cta_text ? `<div class="copy-section">
          <label>CTA</label>
          <p>${escHtml(p.cta_text)}</p>
        </div>` : ''}
      </div>
    </div>`;

  // Lightbox on image click
  card.querySelector('.creative-img-wrap').addEventListener('click', () => {
    openLightbox(adImgUrl);
  });

  return card;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ===================================================
   LIGHTBOX
   =================================================== */
const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightbox-img');

function openLightbox(src) {
  lightboxImg.src = src;
  lightbox.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  lightbox.classList.add('hidden');
  document.body.style.overflow = '';
}

document.getElementById('lightbox-close').addEventListener('click', closeLightbox);
document.getElementById('lightbox-bg').addEventListener('click', closeLightbox);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox(); });

/* ===================================================
   ERROR
   =================================================== */
function showError(msg) {
  document.getElementById('generating-card').classList.add('hidden');
  document.getElementById('results-section').classList.add('hidden');
  document.getElementById('error-card').classList.remove('hidden');
  document.getElementById('error-msg').textContent = msg;
  document.getElementById('gen-title').textContent = 'Hiba történt';
  document.getElementById('gen-desc').textContent = '';
}
