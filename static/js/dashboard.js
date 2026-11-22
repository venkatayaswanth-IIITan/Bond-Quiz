/**
 * BondQuiz - Creator Dashboard Engine
 */

let dashboardQuiz = null;
let creatorToken = '';
let publicId = '';

document.addEventListener('DOMContentLoaded', () => {
  const dashApp = document.getElementById('creatorDashboardApp');
  if (!dashApp) return;

  publicId = dashApp.dataset.publicId;
  const urlParams = new URLSearchParams(window.location.search);
  creatorToken = urlParams.get('token');

  // Try recovering from localStorage if not in URL
  if (!creatorToken) {
    const stored = JSON.parse(localStorage.getItem('bondquiz_created_quizzes') || '[]');
    const match = stored.find(q => q.public_id === publicId);
    if (match && match.creator_token) {
      creatorToken = match.creator_token;
      // Update URL silently
      window.history.replaceState({}, '', `${window.location.pathname}?token=${creatorToken}`);
    }
  }

  if (creatorToken) {
    loadDashboard();
  } else {
    showAuthPrompt();
  }
});

function showAuthPrompt() {
  document.getElementById('loadingState').classList.add('d-none');
  document.getElementById('authPromptState').classList.remove('d-none');
  document.getElementById('dashboardContent').classList.add('d-none');
}

function submitAuthToken() {
  const input = document.getElementById('manualTokenInput');
  const token = input.value.trim();
  if (!token) {
    showToast('Please enter your creator access token', 'error', '🔑');
    return;
  }
  creatorToken = token;
  window.history.replaceState({}, '', `${window.location.pathname}?token=${creatorToken}`);
  loadDashboard();
}

async function loadDashboard() {
  document.getElementById('loadingState').classList.remove('d-none');
  document.getElementById('authPromptState').classList.add('d-none');

  try {
    const res = await fetch(`/api/creator/dashboard/${publicId}`, {
      headers: {
        'X-Creator-Token': creatorToken
      }
    });

    const data = await res.json();
    if (!res.ok) {
      if (res.status === 401 || res.status === 403) {
        showToast('Invalid or unauthorized creator token', 'error', '🔒');
        showAuthPrompt();
        return;
      }
      throw new Error(data.error || 'Failed to load dashboard');
    }

    dashboardQuiz = data.quiz;
    document.getElementById('loadingState').classList.add('d-none');
    document.getElementById('dashboardContent').classList.remove('d-none');

    renderDashboard(data);
    loadParticipantAttempts();

  } catch (err) {
    console.error(err);
    showToast(err.message, 'error', '⚠️');
  }
}

function renderDashboard(data) {
  const quiz = data.quiz;
  const stats = data.stats;
  const leaderboard = data.leaderboard;

  // Header meta
  document.getElementById('dashQuizTitle').innerText = quiz.title;
  document.getElementById('dashCreatorName').innerText = quiz.creator_name;
  document.getElementById('dashQuizDesc').innerText = quiz.description || 'No description provided';
  
  // Status toggle switch
  const statusToggle = document.getElementById('quizStatusToggle');
  const statusBadge = document.getElementById('quizStatusBadge');
  if (statusToggle && statusBadge) {
    statusToggle.checked = quiz.is_active;
    updateStatusBadgeUI(quiz.is_active);
    statusToggle.onchange = () => toggleQuizStatus(statusToggle.checked);
  }

  // Stats boxes
  document.getElementById('statParticipants').innerText = stats.total_participants;
  document.getElementById('statAvgScore').innerText = `${stats.average_score}/${quiz.total_questions}`;
  document.getElementById('statAvgPct').innerText = `${stats.average_percentage}%`;
  document.getElementById('statHighScore').innerText = `${stats.highest_score}/${quiz.total_questions}`;

  // Leaderboard
  renderLeaderboard(leaderboard, quiz.total_questions);

  // Questions tab
  renderQuestionsTab(quiz.questions);

  // Share tools
  setupShareTools(quiz);

  // If newly created, celebrate and show the share modal!
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('created') === '1' || urlParams.get('new') === '1') {
    if (window.soundFX) window.soundFX.playFanfare();
    launchCelebrationConfetti();
    const modalEl = document.getElementById('newQuizSuccessModal');
    if (modalEl && typeof bootstrap !== 'undefined') {
      const modal = new bootstrap.Modal(modalEl);
      modal.show();
    }
    // Clean up query param from address bar
    const cleanUrl = `${window.location.pathname}?token=${creatorToken}`;
    window.history.replaceState({}, '', cleanUrl);
  }
}

function updateStatusBadgeUI(isActive) {
  const badge = document.getElementById('quizStatusBadge');
  if (!badge) return;
  badge.className = isActive ? 'badge bg-success' : 'badge bg-secondary';
  badge.innerText = isActive ? 'Quiz Active' : 'Quiz Closed';
}

async function toggleQuizStatus(isActive) {
  try {
    const res = await fetch(`/api/creator/quizzes/${publicId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-Creator-Token': creatorToken
      },
      body: JSON.stringify({ is_active: isActive })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to update status');

    updateStatusBadgeUI(isActive);
    showToast(isActive ? 'Quiz is now open for participants!' : 'Quiz has been closed.', 'info', isActive ? '🔓' : '🔒');
    if (window.soundFX) window.soundFX.playTap();
  } catch (e) {
    showToast(e.message, 'error', '⚠️');
    // Revert switch
    document.getElementById('quizStatusToggle').checked = !isActive;
  }
}

function renderLeaderboard(leaderboard, totalQuestions) {
  const container = document.getElementById('dashLeaderboardBody');
  if (!container) return;

  if (!leaderboard || leaderboard.length === 0) {
    container.innerHTML = `
      <div class="text-center p-5 text-muted">
        <i class="fa-regular fa-face-smile fa-3x mb-3 text-secondary"></i>
        <h5>No participants yet!</h5>
        <p>Share your quiz link with friends and watch the leaderboard fill up live!</p>
        <button class="btn btn-bond-primary mt-2" onclick="copyPublicQuizLink()">
          <i class="fa-solid fa-share-nodes me-2"></i> Share Quiz Link
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="table-responsive">
      <table class="table leaderboard-table align-middle">
        <thead>
          <tr class="text-muted small text-uppercase">
            <th style="width: 70px;">Rank</th>
            <th>Participant</th>
            <th>Score</th>
            <th>Percentage</th>
            <th>Date Completed</th>
          </tr>
        </thead>
        <tbody>
          ${leaderboard.map(item => `
            <tr class="leaderboard-row">
              <td class="leaderboard-cell">
                ${item.trophy ? `<span style="font-size: 1.4rem;">${item.trophy}</span>` : `<span class="badge bg-light text-dark rounded-pill">#${item.rank}</span>`}
              </td>
              <td class="leaderboard-cell fw-bold">
                <div class="d-flex align-items-center gap-2">
                  <span class="avatar-circle">${item.participant_name.charAt(0).toUpperCase()}</span>
                  <span>${escapeHtml(item.participant_name)}</span>
                </div>
              </td>
              <td class="leaderboard-cell fw-bold text-primary">
                ${item.score} / ${item.total_questions || totalQuestions}
              </td>
              <td class="leaderboard-cell">
                <div class="d-flex align-items-center gap-2">
                  <div class="progress flex-grow-1" style="height: 6px; width: 80px;">
                    <div class="progress-bar bg-primary" style="width: ${item.percentage}%"></div>
                  </div>
                  <span class="small fw-bold">${item.percentage}%</span>
                </div>
              </td>
              <td class="leaderboard-cell text-muted small">
                ${escapeHtml(item.completed_at)}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

// Fetch detailed participant attempts with question answers
async function loadParticipantAttempts() {
  const container = document.getElementById('dashAttemptsBody');
  if (!container) return;

  try {
    const res = await fetch(`/api/creator/attempts/${publicId}`, {
      headers: { 'X-Creator-Token': creatorToken }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    const attempts = data.attempts || [];
    if (attempts.length === 0) {
      container.innerHTML = `
        <div class="text-center p-4 text-muted">
          <p>No participant responses yet.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="accordion" id="attemptsAccordion">
        ${attempts.map((att, i) => `
          <div class="accordion-item mb-2 border rounded-3 overflow-hidden">
            <h2 class="accordion-header" id="heading_${att.id}">
              <button class="accordion-button ${i === 0 ? '' : 'collapsed'} py-3" type="button" 
                data-bs-toggle="collapse" data-bs-target="#collapse_${att.id}">
                <div class="d-flex align-items-center justify-content-between w-100 me-3">
                  <div>
                    <strong>${escapeHtml(att.participant_name)}</strong>
                    <span class="badge bg-light text-dark ms-2">${att.completed_at}</span>
                  </div>
                  <div>
                    <span class="badge ${att.percentage >= 70 ? 'bg-success' : 'bg-primary'} fs-6">
                      ${att.score}/${att.total_questions} (${att.percentage}%)
                    </span>
                  </div>
                </div>
              </button>
            </h2>
            <div id="collapse_${att.id}" class="accordion-collapse collapse ${i === 0 ? 'show' : ''}" 
              data-bs-parent="#attemptsAccordion">
              <div class="accordion-body bg-light">
                <h6 class="fw-bold mb-3">Individual Answers:</h6>
                <div class="row g-2">
                  ${att.answers.map((ans, aIdx) => `
                    <div class="col-md-6">
                      <div class="card p-2 h-100 ${ans.is_correct ? 'border-success' : 'border-danger'}">
                        <div class="small fw-bold mb-1">${aIdx + 1}. ${escapeHtml(ans.question_text)}</div>
                        <div class="small">
                          <span class="text-muted">Selected:</span> 
                          <span class="${ans.is_correct ? 'text-success fw-bold' : 'text-danger fw-bold'}">
                            ${escapeHtml(ans.selected_text)}
                          </span>
                        </div>
                        ${!ans.is_correct ? `
                          <div class="small text-muted">
                            Correct: <span class="text-success">${escapeHtml(ans.correct_text)}</span>
                          </div>
                        ` : ''}
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}

function renderQuestionsTab(questions) {
  const container = document.getElementById('dashQuestionsList');
  if (!container) return;

  container.innerHTML = questions.map((q, idx) => `
    <div class="card p-3 mb-3 border rounded-3">
      <div class="d-flex justify-content-between align-items-center mb-2">
        <span class="fw-bold fs-6">#${idx + 1}. ${escapeHtml(q.question_text)}</span>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteExistingQuestion(${q.id})" ${questions.length <= 3 ? 'disabled' : ''}>
          <i class="fa-solid fa-trash-can me-1"></i> Delete
        </button>
      </div>
      <div class="row g-2">
        ${q.options.map(opt => `
          <div class="col-md-6">
            <div class="p-2 border rounded-2 ${opt.is_correct ? 'bg-success text-white' : 'bg-white'}">
              ${opt.is_correct ? '<i class="fa-solid fa-check me-1"></i>' : ''} ${escapeHtml(opt.option_text)}
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

async function deleteExistingQuestion(qId) {
  if (!confirm('Are you sure you want to delete this question?')) return;
  try {
    const res = await fetch(`/api/creator/questions/${qId}`, {
      method: 'DELETE',
      headers: { 'X-Creator-Token': creatorToken }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    showToast('Question deleted!', 'info', '🗑️');
    loadDashboard();
  } catch (e) {
    showToast(e.message, 'error', '⚠️');
  }
}

// Add new question modal handling
async function submitAddQuestion() {
  const qText = document.getElementById('newQText').value.trim();
  const o1 = document.getElementById('newQOpt1').value.trim();
  const o2 = document.getElementById('newQOpt2').value.trim();
  const o3 = document.getElementById('newQOpt3').value.trim();
  const o4 = document.getElementById('newQOpt4').value.trim();
  const correctIdx = parseInt(document.querySelector('input[name="newQCorrect"]:checked')?.value || '0');

  if (!qText || !o1 || !o2) {
    showToast('Please provide question text and at least 2 options', 'error', '⚠️');
    return;
  }

  const options = [o1, o2];
  if (o3) options.push(o3);
  if (o4) options.push(o4);

  try {
    const res = await fetch(`/api/creator/quizzes/${publicId}/questions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Creator-Token': creatorToken
      },
      body: JSON.stringify({
        question_text: qText,
        options: options,
        correct_index: correctIdx
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    showToast('New question added to your quiz!', 'success', '➕');
    bootstrap.Modal.getInstance(document.getElementById('addQuestionModal')).hide();
    loadDashboard();
  } catch (e) {
    showToast(e.message, 'error', '⚠️');
  }
}

// Edit quiz metadata
async function submitEditQuiz() {
  const title = document.getElementById('editQuizTitle').value.trim();
  const desc = document.getElementById('editQuizDesc').value.trim();
  const theme = document.getElementById('editQuizTheme').value;

  if (!title) {
    showToast('Title cannot be empty', 'error', '⚠️');
    return;
  }

  try {
    const res = await fetch(`/api/creator/quizzes/${publicId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-Creator-Token': creatorToken
      },
      body: JSON.stringify({
        title: title,
        description: desc,
        theme: theme
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    showToast('Quiz updated successfully!', 'success', '✨');
    bootstrap.Modal.getInstance(document.getElementById('editQuizModal')).hide();
    loadDashboard();
  } catch (e) {
    showToast(e.message, 'error', '⚠️');
  }
}

// Delete Quiz
async function confirmDeleteQuiz() {
  if (!confirm('WARNING: This will permanently delete this quiz and all participant scores. This action cannot be undone!\n\nAre you sure you want to delete?')) return;

  try {
    const res = await fetch(`/api/creator/quizzes/${publicId}`, {
      method: 'DELETE',
      headers: { 'X-Creator-Token': creatorToken }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    showToast('Quiz deleted permanently', 'info', '🗑️');
    setTimeout(() => {
      window.location.href = '/';
    }, 1200);
  } catch (e) {
    showToast(e.message, 'error', '⚠️');
  }
}

// Share tools setup
function setupShareTools(quiz) {
  const host = window.location.origin;
  const publicUrl = `${host}/quiz/${quiz.public_id}`;
  const creatorUrl = `${host}/creator/${quiz.public_id}?token=${creatorToken}`;

  // Top prominent share banner
  const topPubInput = document.getElementById('topDashPublicUrl');
  if (topPubInput) topPubInput.value = publicUrl;

  const topWaBtn = document.getElementById('topDashShareWhatsApp');
  if (topWaBtn) {
    topWaBtn.onclick = () => shareOnWhatsApp(publicUrl, `I created a quiz to test how well you know me! Think you can beat everyone? Play here: ${publicUrl}`);
  }

  const topPlayBtn = document.getElementById('topDashPlayBtn');
  if (topPlayBtn) {
    topPlayBtn.href = publicUrl;
  }

  const pubInput = document.getElementById('dashPublicUrl');
  const dashInput = document.getElementById('dashPrivateUrl');
  if (pubInput) pubInput.value = publicUrl;
  if (dashInput) dashInput.value = creatorUrl;

  const waBtn = document.getElementById('dashShareWhatsApp');
  if (waBtn) {
    waBtn.onclick = () => shareOnWhatsApp(publicUrl, `I created a quiz to test how well you know me! Think you can beat everyone? Play here: ${publicUrl}`);
  }

  // Modal share tools for newly created quiz
  const modalUrlInput = document.getElementById('newQuizModalUrl');
  if (modalUrlInput) modalUrlInput.value = publicUrl;

  const modalWaBtn = document.getElementById('newQuizModalWaBtn');
  if (modalWaBtn) {
    modalWaBtn.onclick = () => shareOnWhatsApp(publicUrl, `I created a quiz to test how well you know me! Think you can beat everyone? Play here: ${publicUrl}`);
  }

  const modalShareBtn = document.getElementById('newQuizModalShareBtn');
  if (modalShareBtn) {
    modalShareBtn.onclick = () => shareQuizNative(quiz.title, 'Can you beat my friendship test?', publicUrl);
  }

  const modalQrContainer = document.getElementById('newQuizModalQrCode');
  if (modalQrContainer) {
    modalQrContainer.innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(publicUrl)}" class="img-fluid rounded-3 shadow-sm" alt="QR Code" style="max-width: 130px;">`;
  }
}

function copyPublicQuizLink() {
  const host = window.location.origin;
  copyToClipboard(`${host}/quiz/${publicId}`);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
