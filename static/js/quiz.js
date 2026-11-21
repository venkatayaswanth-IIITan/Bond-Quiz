/**
 * BondQuiz - Participant Quiz Player & Scorer
 */

let quizData = null;
let currentQuestionIndex = 0;
let userAnswers = {}; // { question_id: selected_option_id }
let participantName = '';
let attemptToken = '';
let isSubmitting = false;

document.addEventListener('DOMContentLoaded', () => {
  const playerApp = document.getElementById('quizPlayerApp');
  if (!playerApp) return;

  const publicId = playerApp.dataset.publicId;
  loadQuizData(publicId);

  // Setup nickname input enter key
  const nameInput = document.getElementById('participantNickname');
  if (nameInput) {
    nameInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') startQuizAttempt();
    });
  }

  // Keyboard navigation for options (1, 2, 3, 4)
  document.addEventListener('keydown', (e) => {
    const activeCard = document.getElementById('activeQuestionView');
    if (!activeCard || activeCard.classList.contains('d-none')) return;

    if (['1', '2', '3', '4'].includes(e.key)) {
      const optIdx = parseInt(e.key) - 1;
      const opts = activeCard.querySelectorAll('.option-card');
      if (opts[optIdx]) opts[optIdx].click();
    } else if (e.key === 'Enter') {
      const nextBtn = document.getElementById('quizNextBtn');
      const submitBtn = document.getElementById('quizSubmitBtn');
      if (nextBtn && !nextBtn.classList.contains('d-none')) nextBtn.click();
      else if (submitBtn && !submitBtn.classList.contains('d-none')) submitBtn.click();
    }
  });
});

// Fetch public quiz data (does not leak is_correct)
async function loadQuizData(publicId) {
  try {
    const res = await fetch(`/api/quizzes/${publicId}`);
    const data = await res.json();

    if (!res.ok) {
      document.getElementById('loadingState').classList.add('d-none');
      document.getElementById('closedQuizState').classList.remove('d-none');
      document.getElementById('closedQuizMessage').innerText = data.error || 'This quiz is no longer accessible.';
      return;
    }

    quizData = data.quiz;
    document.getElementById('loadingState').classList.add('d-none');
    document.getElementById('welcomeScreen').classList.remove('d-none');

    // Populate welcome screen
    document.getElementById('welcomeQuizTitle').innerText = quizData.title;
    document.getElementById('welcomeCreator').innerText = quizData.creator_name;
    document.getElementById('welcomeDesc').innerText = quizData.description || 'Test your bond and see where you rank on the leaderboard!';
    document.getElementById('welcomeQuestionCount').innerText = `${quizData.total_questions} Questions`;

  } catch (err) {
    console.error('Failed to load quiz:', err);
    showToast('Failed to load quiz. Please refresh.', 'error', '⚠️');
  }
}

// Start quiz attempt session
async function startQuizAttempt() {
  const nameInput = document.getElementById('participantNickname');
  participantName = nameInput.value.trim();

  if (!participantName) {
    showToast('Please enter your nickname or name!', 'error', '👋');
    nameInput.focus();
    return;
  }

  const startBtn = document.getElementById('startQuizBtn');
  startBtn.disabled = true;
  startBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Starting...`;

  try {
    const res = await fetch(`/api/quizzes/${quizData.public_id}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ participant_name: participantName })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || 'Could not start quiz');
    }

    attemptToken = data.attempt_token;
    if (window.soundFX) window.soundFX.playNext();

    // Transition to questions
    document.getElementById('welcomeScreen').classList.add('d-none');
    document.getElementById('activeQuestionView').classList.remove('d-none');

    currentQuestionIndex = 0;
    renderCurrentQuestion();

  } catch (e) {
    showToast(e.message, 'error', '⚠️');
    startBtn.disabled = false;
    startBtn.innerHTML = `Start Quiz <i class="fa-solid fa-arrow-right ms-2"></i>`;
  }
}

// Render active question
function renderCurrentQuestion() {
  if (!quizData || !quizData.questions[currentQuestionIndex]) return;

  const q = quizData.questions[currentQuestionIndex];
  const total = quizData.questions.length;
  const progressPct = ((currentQuestionIndex + 1) / total) * 100;

  // Update progress bar & label
  document.getElementById('questionProgressBar').style.width = `${progressPct}%`;
  document.getElementById('questionCounterBadge').innerText = `Question ${currentQuestionIndex + 1} of ${total}`;
  document.getElementById('activeQuestionText').innerText = q.question_text;

  // Render 4 options
  const container = document.getElementById('optionsContainer');
  const selectedOptionId = userAnswers[q.id];

  container.innerHTML = q.options.map((opt, idx) => {
    const isSelected = selectedOptionId === opt.id;
    const letter = ['A', 'B', 'C', 'D'][idx] || '';
    return `
      <div class="option-card ${isSelected ? 'selected' : ''}" 
        onclick="selectOption(${q.id}, ${opt.id})"
        tabindex="0"
        role="button">
        <div class="option-marker">${letter}</div>
        <div class="flex-grow-1">${escapeHtml(opt.option_text)}</div>
        <div class="selection-check ${isSelected ? 'text-primary' : 'text-muted opacity-25'}">
          <i class="fa-solid fa-circle-check fa-lg"></i>
        </div>
      </div>
    `;
  }).join('');

  // Nav buttons
  const prevBtn = document.getElementById('quizPrevBtn');
  const nextBtn = document.getElementById('quizNextBtn');
  const submitBtn = document.getElementById('quizSubmitBtn');

  prevBtn.disabled = currentQuestionIndex === 0;

  if (currentQuestionIndex === total - 1) {
    nextBtn.classList.add('d-none');
    submitBtn.classList.remove('d-none');
  } else {
    nextBtn.classList.remove('d-none');
    submitBtn.classList.add('d-none');
  }
}

function selectOption(questionId, optionId) {
  userAnswers[questionId] = optionId;
  if (window.soundFX) window.soundFX.playTap();

  // Highlight selected card visually
  const container = document.getElementById('optionsContainer');
  const cards = container.querySelectorAll('.option-card');
  const q = quizData.questions[currentQuestionIndex];

  q.options.forEach((opt, idx) => {
    if (cards[idx]) {
      const isSelected = opt.id === optionId;
      cards[idx].classList.toggle('selected', isSelected);
      const icon = cards[idx].querySelector('.selection-check');
      if (icon) {
        icon.className = isSelected ? 'selection-check text-primary' : 'selection-check text-muted opacity-25';
      }
    }
  });

  // Smooth auto-advance after brief delay if not on last question
  if (currentQuestionIndex < quizData.questions.length - 1) {
    setTimeout(() => {
      goToNextQuestion();
    }, 350);
  }
}

function goToNextQuestion() {
  const currentQ = quizData.questions[currentQuestionIndex];
  if (!userAnswers[currentQ.id]) {
    showToast('Please pick an answer to continue!', 'info', '👇');
    return;
  }

  if (currentQuestionIndex < quizData.questions.length - 1) {
    currentQuestionIndex++;
    if (window.soundFX) window.soundFX.playNext();
    renderCurrentQuestion();
  }
}

function goToPrevQuestion() {
  if (currentQuestionIndex > 0) {
    currentQuestionIndex--;
    if (window.soundFX) window.soundFX.playTap();
    renderCurrentQuestion();
  }
}

// Submit Quiz Answers to Backend
async function submitQuiz() {
  const currentQ = quizData.questions[currentQuestionIndex];
  if (!userAnswers[currentQ.id]) {
    showToast('Please select an answer for the final question!', 'info', '👇');
    return;
  }

  if (isSubmitting) return;
  isSubmitting = true;

  const submitBtn = document.getElementById('quizSubmitBtn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Calculating Score...`;

  try {
    const res = await fetch(`/api/quizzes/${quizData.public_id}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        attempt_token: attemptToken,
        answers: userAnswers
      })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || 'Failed to submit quiz');
    }

    try {
      if (window.soundFX) window.soundFX.playFanfare();
    } catch (e) {}

    try {
      if (typeof launchCelebrationConfetti === 'function') launchCelebrationConfetti();
    } catch (e) {}

    // Show Results View immediately
    renderQuizResults(data);

  } catch (err) {
    console.error('Quiz submission error:', err);
    try {
      showToast(err.message || 'Error submitting answers', 'error', '⚠️');
    } catch (e) {
      alert(err.message || 'Error submitting answers');
    }
    submitBtn.disabled = false;
    submitBtn.innerHTML = `Submit Quiz <i class="fa-solid fa-flag-checkered ms-2"></i>`;
    isSubmitting = false;
  }
}

function renderQuizResults(data) {
  document.getElementById('activeQuestionView').classList.add('d-none');
  const resultView = document.getElementById('quizResultView');
  resultView.classList.remove('d-none');

  const result = data.result;
  const feedback = result.feedback;

  // Result Header
  document.getElementById('resultTierBadge').innerText = feedback.tier;
  document.getElementById('resultFeedbackTitle').innerText = feedback.title;
  document.getElementById('resultFeedbackMsg').innerText = feedback.message;
  document.getElementById('resultScoreDisplay').innerText = `${result.score}/${result.total_questions}`;
  document.getElementById('resultPercentage').innerText = `${result.percentage}%`;

  // WhatsApp share
  const shareText = `I scored ${result.score}/${result.total_questions} (${result.percentage}%) on ${quizData.creator_name}'s BondQuiz! Think you know them better? Try here: ${window.location.href}`;
  const waBtn = document.getElementById('resultShareWhatsAppBtn');
  if (waBtn) {
    waBtn.onclick = () => shareOnWhatsApp(window.location.href, shareText);
  }

  // Copy score link
  const copyBtn = document.getElementById('resultCopyScoreBtn');
  if (copyBtn) {
    copyBtn.onclick = () => copyToClipboard(shareText, copyBtn);
  }

  // Leaderboard link
  const lbBtn = document.getElementById('resultLeaderboardBtn');
  if (lbBtn) {
    lbBtn.href = data.leaderboard_url || `/quiz/${quizData.public_id}/leaderboard`;
  }

  // Answer Breakdown
  const breakdownList = document.getElementById('resultBreakdownList');
  if (breakdownList && result.breakdown) {
    breakdownList.innerHTML = result.breakdown.map((item, idx) => `
      <div class="card quiz-card mb-3 p-3 text-start ${item.is_correct ? 'border-success' : 'border-danger'}">
        <div class="d-flex align-items-center justify-content-between mb-2">
          <span class="fw-bold">${idx + 1}. ${escapeHtml(item.question_text)}</span>
          <span class="badge ${item.is_correct ? 'bg-success' : 'bg-danger'}">
            ${item.is_correct ? '<i class="fa-solid fa-check me-1"></i> Correct' : '<i class="fa-solid fa-xmark me-1"></i> Missed'}
          </span>
        </div>
        <div class="small">
          <div class="mb-1">
            <span class="text-muted">Your answer:</span> 
            <strong class="${item.is_correct ? 'text-success' : 'text-danger'}">
              ${escapeHtml(item.selected_text)}
            </strong>
          </div>
          ${!item.is_correct ? `
            <div>
              <span class="text-muted">Correct answer:</span> 
              <strong class="text-success">${escapeHtml(item.correct_text)}</strong>
            </div>
          ` : ''}
        </div>
      </div>
    `).join('');
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
