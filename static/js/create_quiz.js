/**
 * BondQuiz - Multi-step Quiz Creator Wizard
 */

// Global questions state
let questions = [];
let currentCategory = 'best_friend';
let selectedTheme = 'purple_bliss';
let selectedAvatar = 'sparkles';

// Avatars map
const AVATARS = [
  { id: 'sparkles', emoji: '✨' },
  { id: 'cat', emoji: '🐱' },
  { id: 'crown', emoji: '👑' },
  { id: 'heart', emoji: '💖' },
  { id: 'fire', emoji: '🔥' },
  { id: 'pizza', emoji: '🍕' },
  { id: 'rocket', emoji: '🚀' },
  { id: 'sunglasses', emoji: '🕶️' },
  { id: 'gamepad', emoji: '🎮' },
  { id: 'unicorn', emoji: '🦄' }
];

document.addEventListener('DOMContentLoaded', () => {
  // Initialize initial category from dataset or query param
  const container = document.getElementById('createQuizApp');
  if (!container) return;

  const initCat = container.dataset.initialCategory || 'best_friend';
  selectCategory(initCat);
  renderAvatarSelector();
  setupEventListeners();
});

// Category Selection
async function selectCategory(catKey) {
  currentCategory = catKey;
  document.querySelectorAll('.cat-select-btn').forEach(btn => {
    btn.classList.toggle('selected', btn.dataset.category === catKey);
  });

  // Suggest default title
  const titleInput = document.getElementById('quizTitle');
  const nameInput = document.getElementById('creatorName');
  const creator = nameInput && nameInput.value.trim() ? nameInput.value.trim() : 'Me';

  if (titleInput && (!titleInput.value || titleInput.dataset.autoFilled === 'true')) {
    const defaultTitles = {
      'best_friend': `How Well Do You Know ${creator}? (Bestie Edition)`,
      'friends': `The Ultimate ${creator} Friendship Test!`,
      'couple': `Our Love Story: How Well Do You Know ${creator}?`,
      'crush': `Can You Guess What ${creator} Really Thinks?`,
      'family': `Family Trivia: The Real Facts About ${creator}!`,
      'custom': `The Real ${creator} Quiz: Challenge Your Knowledge!`
    };
    titleInput.value = defaultTitles[catKey] || `How Well Do You Know ${creator}?`;
    titleInput.dataset.autoFilled = 'true';
  }

  // Load template questions for this category
  try {
    const res = await fetch(`/api/templates/${catKey}`);
    const data = await res.json();
    if (data.status === 'success' && data.templates) {
      questions = data.templates.map((tpl, i) => ({
        id: 'q_' + Date.now() + '_' + i,
        question_text: tpl.question,
        options: [...tpl.options],
        correct_index: tpl.correct_index || 0
      }));
      renderQuestionsList();
    }
  } catch (e) {
    console.error('Failed to load templates:', e);
  }
}

// Avatar Selector
function renderAvatarSelector() {
  const container = document.getElementById('avatarSelector');
  if (!container) return;

  container.innerHTML = AVATARS.map(av => `
    <button type="button" class="btn btn-outline-light avatar-btn ${selectedAvatar === av.id ? 'active' : ''}" 
      data-avatar="${av.id}" onclick="selectAvatar('${av.id}')" style="font-size: 1.5rem; border-radius: 14px; width: 48px; height: 48px; padding: 0;">
      ${av.emoji}
    </button>
  `).join('');
}

function selectAvatar(avatarId) {
  selectedAvatar = avatarId;
  document.querySelectorAll('.avatar-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.avatar === avatarId);
  });
  if (window.soundFX) window.soundFX.playTap();
}

// Theme Selector
function selectTheme(themeId) {
  selectedTheme = themeId;
  document.body.className = `theme-${themeId}`;
  document.querySelectorAll('.theme-card').forEach(card => {
    card.classList.toggle('active', card.dataset.theme === themeId);
  });
  if (window.soundFX) window.soundFX.playTap();
}

// Questions Rendering & Management
function renderQuestionsList() {
  const listEl = document.getElementById('questionsList');
  const countEl = document.getElementById('questionCountBadge');
  if (!listEl) return;

  if (countEl) {
    countEl.innerText = `${questions.length} Question${questions.length === 1 ? '' : 's'}`;
  }

  if (questions.length === 0) {
    listEl.innerHTML = `
      <div class="text-center p-4 text-muted">
        <i class="fa-regular fa-folder-open fa-2x mb-2"></i>
        <p>No questions yet. Click "+ Add Question" below or choose from templates!</p>
      </div>
    `;
    return;
  }

  listEl.innerHTML = questions.map((q, qIdx) => `
    <div class="card quiz-card mb-3 p-3 position-relative question-builder-item" data-id="${q.id}">
      <div class="d-flex align-items-center justify-content-between mb-2">
        <span class="badge badge-soft-primary">
          <i class="fa-solid fa-circle-question me-1"></i> Question #${qIdx + 1}
        </span>
        <div class="btn-group btn-group-sm">
          <button type="button" class="btn btn-sm btn-outline-secondary" onclick="moveQuestion(${qIdx}, -1)" ${qIdx === 0 ? 'disabled' : ''} title="Move Up">
            <i class="fa-solid fa-arrow-up"></i>
          </button>
          <button type="button" class="btn btn-sm btn-outline-secondary" onclick="moveQuestion(${qIdx}, 1)" ${qIdx === questions.length - 1 ? 'disabled' : ''} title="Move Down">
            <i class="fa-solid fa-arrow-down"></i>
          </button>
          <button type="button" class="btn btn-sm btn-outline-danger" onclick="deleteQuestion(${qIdx})" title="Delete Question">
            <i class="fa-solid fa-trash-can"></i>
          </button>
        </div>
      </div>

      <div class="mb-3">
        <input type="text" class="form-control form-control-lg fw-bold" 
          value="${escapeHtml(q.question_text)}" 
          placeholder="e.g. What is my biggest pet peeve?"
          oninput="updateQuestionText(${qIdx}, this.value)"
          style="border-radius: 12px; font-size: 1.05rem;" required>
      </div>

      <div class="text-muted small mb-2 fw-semibold">
        <i class="fa-regular fa-circle-check text-success me-1"></i> Tap the radio circle next to your real answer:
      </div>

      <div class="row g-2">
        ${[0, 1, 2, 3].map(optIdx => `
          <div class="col-md-6">
            <div class="input-group">
              <div class="input-group-text bg-white" style="border-radius: 12px 0 0 12px; cursor: pointer;" 
                onclick="setCorrectAnswer(${qIdx}, ${optIdx})">
                <input class="form-check-input mt-0" type="radio" 
                  name="correct_opt_${q.id}" 
                  ${q.correct_index === optIdx ? 'checked' : ''} 
                  title="Mark this as the correct answer"
                  style="cursor: pointer;">
              </div>
              <input type="text" class="form-control" 
                value="${escapeHtml(q.options[optIdx] || '')}" 
                placeholder="Option ${optIdx + 1}"
                oninput="updateOptionText(${qIdx}, ${optIdx}, this.value)"
                style="border-radius: 0 12px 12px 0;" required>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

function updateQuestionText(qIdx, text) {
  if (questions[qIdx]) questions[qIdx].question_text = text;
}

function updateOptionText(qIdx, optIdx, text) {
  if (questions[qIdx]) questions[qIdx].options[optIdx] = text;
}

function setCorrectAnswer(qIdx, optIdx) {
  if (questions[qIdx]) {
    questions[qIdx].correct_index = optIdx;
    renderQuestionsList();
    if (window.soundFX) window.soundFX.playTap();
  }
}

function moveQuestion(index, direction) {
  const target = index + direction;
  if (target < 0 || target >= questions.length) return;
  const temp = questions[index];
  questions[index] = questions[target];
  questions[target] = temp;
  renderQuestionsList();
  if (window.soundFX) window.soundFX.playTap();
}

function deleteQuestion(index) {
  if (questions.length <= 3) {
    showToast('A quiz needs at least 3 questions to be fun!', 'error', '⚠️');
    return;
  }
  questions.splice(index, 1);
  renderQuestionsList();
  showToast('Question removed', 'info', '🗑️');
  if (window.soundFX) window.soundFX.playTap();
}

function addCustomQuestion() {
  if (questions.length >= 30) {
    showToast('Maximum 30 questions per quiz.', 'error', '⚠️');
    return;
  }
  questions.push({
    id: 'q_' + Date.now(),
    question_text: '',
    options: ['', '', '', ''],
    correct_index: 0
  });
  renderQuestionsList();
  if (window.soundFX) window.soundFX.playTap();
  // Scroll to bottom
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}

// Modal Question Bank to quickly pick additional questions
async function openQuestionBank() {
  const modalEl = new bootstrap.Modal(document.getElementById('questionBankModal'));
  modalEl.show();
}

function addFromBank(qText, opts, correctIdx) {
  if (questions.length >= 30) {
    showToast('Maximum 30 questions reached.', 'error', '⚠️');
    return;
  }
  questions.push({
    id: 'q_' + Date.now(),
    question_text: qText,
    options: [...opts],
    correct_index: correctIdx || 0
  });
  renderQuestionsList();
  showToast('Question added!', 'success', '➕');
  if (window.soundFX) window.soundFX.playTap();
}

// Wizard Step Navigation
function goToStep(stepNumber) {
  // Validate Step 2 before going to Step 3
  if (stepNumber >= 3) {
    const creatorName = document.getElementById('creatorName').value.trim();
    const title = document.getElementById('quizTitle').value.trim();
    if (!creatorName) {
      showToast('Please enter your nickname!', 'error', '⚠️');
      document.getElementById('creatorName').focus();
      return;
    }
    if (!title) {
      showToast('Please enter a quiz title!', 'error', '⚠️');
      document.getElementById('quizTitle').focus();
      return;
    }
  }

  document.querySelectorAll('.wizard-step').forEach(step => {
    step.classList.add('d-none');
  });
  const targetStep = document.getElementById(`step${stepNumber}`);
  if (targetStep) {
    targetStep.classList.remove('d-none');
  }

  document.querySelectorAll('.step-indicator-item').forEach(ind => {
    const stepVal = parseInt(ind.dataset.step);
    ind.classList.toggle('active', stepVal === stepNumber);
    ind.classList.toggle('completed', stepVal < stepNumber);
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (window.soundFX) window.soundFX.playNext();
}

// Quiz Preview
function openPreviewModal() {
  const previewContainer = document.getElementById('previewModalBody');
  const creatorName = document.getElementById('creatorName').value.trim() || 'Alex';
  const title = document.getElementById('quizTitle').value.trim() || 'Friendship Quiz';
  const desc = document.getElementById('quizDesc').value.trim() || 'How well do you know me?';

  let previewHTML = `
    <div class="text-center mb-4">
      <div style="font-size: 3rem;">${AVATARS.find(a => a.id === selectedAvatar)?.emoji || '✨'}</div>
      <h3 class="fw-bold mt-2">${escapeHtml(title)}</h3>
      <p class="text-muted">${escapeHtml(desc)}</p>
      <span class="badge badge-soft-primary">Created by ${escapeHtml(creatorName)} • ${questions.length} Questions</span>
    </div>
    <hr>
    <h5 class="fw-bold mb-3">Sample Question 1 Preview:</h5>
  `;

  if (questions.length > 0) {
    const q1 = questions[0];
    previewHTML += `
      <div class="card p-3 border-0 bg-light rounded-4 mb-3">
        <h6 class="fw-bold mb-3">${escapeHtml(q1.question_text || 'Sample Question')}</h6>
        ${q1.options.map((opt, i) => `
          <div class="option-card mb-2" style="cursor: default;">
            <div class="option-marker">${['A', 'B', 'C', 'D'][i]}</div>
            <div>${escapeHtml(opt || `Option ${i + 1}`)}</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  previewContainer.innerHTML = previewHTML;
  const modal = new bootstrap.Modal(document.getElementById('quizPreviewModal'));
  modal.show();
}

// Submit Quiz Creation
async function submitQuizGeneration() {
  const creatorName = document.getElementById('creatorName').value.trim();
  const title = document.getElementById('quizTitle').value.trim();
  const description = document.getElementById('quizDesc').value.trim();

  if (!creatorName) {
    showToast('Please enter your nickname', 'error', '⚠️');
    goToStep(2);
    return;
  }
  if (!title) {
    showToast('Please enter a quiz title', 'error', '⚠️');
    goToStep(2);
    return;
  }
  if (questions.length < 3) {
    showToast('Quiz must have at least 3 questions', 'error', '⚠️');
    goToStep(3);
    return;
  }

  // Validate that questions and options are non-empty
  for (let i = 0; i < questions.length; i++) {
    const q = questions[i];
    if (!q.question_text.trim()) {
      showToast(`Question #${i + 1} has no text!`, 'error', '⚠️');
      goToStep(3);
      return;
    }
    const filledOptions = q.options.filter(o => o && o.trim().length > 0);
    if (filledOptions.length < 2) {
      showToast(`Question #${i + 1} must have at least 2 options!`, 'error', '⚠️');
      goToStep(3);
      return;
    }
  }

  const submitBtn = document.getElementById('generateQuizBtn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Generating Quiz...`;

  const payload = {
    creator_name: creatorName,
    title: title,
    description: description,
    category: currentCategory,
    theme: selectedTheme,
    avatar: selectedAvatar,
    questions: questions.map(q => ({
      question_text: q.question_text.trim(),
      options: q.options.filter(o => o && o.trim().length > 0),
      correct_index: q.correct_index
    }))
  };

  try {
    const response = await fetch('/api/quizzes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || 'Failed to create quiz');
    }

    // Success! Save to localStorage for creator convenience
    try {
      const stored = JSON.parse(localStorage.getItem('bondquiz_created_quizzes') || '[]');
      stored.unshift({
        public_id: result.public_id,
        title: title,
        creator_name: creatorName,
        creator_token: result.creator_token,
        dashboard_url: result.dashboard_url,
        quiz_url: result.quiz_url,
        leaderboard_url: `/quiz/${result.public_id}/leaderboard`,
        created_at: new Date().toISOString()
      });
      localStorage.setItem('bondquiz_created_quizzes', JSON.stringify(stored));
    } catch (storageErr) {
      console.warn('localStorage error:', storageErr);
    }

    // Play celebrations
    try {
      if (window.soundFX) window.soundFX.playFanfare();
    } catch (e) {}
    try {
      if (typeof launchCelebrationConfetti === 'function') launchCelebrationConfetti();
    } catch (e) {}

    // Show Step 4 (Success / Share Screen) immediately so creator gets links!
    renderSuccessScreen(result, title);

  } catch (err) {
    showToast(err.message, 'error', '❌');
    submitBtn.disabled = false;
    submitBtn.className = 'btn btn-bond-primary btn-lg';
    submitBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles me-2"></i> Generate & Share Quiz`;
  }
}

function renderSuccessScreen(result, quizTitle) {
  document.querySelectorAll('.wizard-step').forEach(s => s.classList.add('d-none'));
  const successStep = document.getElementById('stepSuccess');
  successStep.classList.remove('d-none');

  const fullQuizUrl = window.location.origin + result.quiz_url;
  const fullDashboardUrl = window.location.origin + result.dashboard_url;

  const pubInput = document.getElementById('publicQuizUrl');
  if (pubInput) pubInput.value = fullQuizUrl;

  const dashInput = document.getElementById('creatorDashboardUrl');
  if (dashInput) dashInput.value = fullDashboardUrl;

  const openQuiz = document.getElementById('openQuizBtn');
  if (openQuiz) openQuiz.href = fullQuizUrl;

  const openDash = document.getElementById('openDashboardBtn');
  if (openDash) openDash.href = fullDashboardUrl;

  // WhatsApp button
  const waBtn = document.getElementById('shareWhatsAppBtn');
  if (waBtn) {
    const waText = `I created a quiz to test how well you know me! Think you can beat everyone? Play here: ${fullQuizUrl}`;
    waBtn.onclick = () => shareOnWhatsApp(fullQuizUrl, waText);
  }

  // Native share button
  const shareBtn = document.getElementById('shareNativeBtn');
  if (shareBtn) {
    shareBtn.onclick = () => shareQuizNative(quizTitle || 'My BondQuiz', 'Can you beat my friendship test?', fullQuizUrl);
  }

  // QR Code generator (renders SVG barcode/QR)
  renderQRCode('quizQrCodeContainer', fullQuizUrl);

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Lightweight QR code SVG generator using quickchart.io or pure SVG matrix
function renderQRCode(containerId, url) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const qrImg = document.createElement('img');
  qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(url)}`;
  qrImg.alt = 'Scan QR Code';
  qrImg.className = 'img-fluid rounded-3 shadow-sm';
  qrImg.style.maxWidth = '150px';
  container.innerHTML = '';
  container.appendChild(qrImg);
}

function setupEventListeners() {
  // Creator nickname auto-updates default quiz title
  const nameInput = document.getElementById('creatorName');
  const titleInput = document.getElementById('quizTitle');
  if (nameInput && titleInput) {
    nameInput.addEventListener('input', () => {
      if (titleInput.dataset.autoFilled === 'true') {
        const name = nameInput.value.trim() || 'Me';
        titleInput.value = `How Well Do You Know ${name}?`;
      }
    });
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
