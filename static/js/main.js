/**
 * Main BondQuiz UI Interactions & Utility Helpers
 */

// Toast notification helper
function showToast(message, type = 'info', icon = '✨') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'bond-toast';
  toast.innerHTML = `<span style="font-size: 1.2rem;">${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(15px)';
    setTimeout(() => toast.remove(), 400);
  }, 3200);
}

// Copy text to clipboard with button feedback
async function copyToClipboard(text, btnElement) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      // Fallback for non-https or older browser context
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      document.execCommand('copy');
      textArea.remove();
    }

    showToast('Copied to clipboard!', 'success', '📋');
    if (window.soundFX) window.soundFX.playTap();

    if (btnElement) {
      const originalHTML = btnElement.innerHTML;
      btnElement.innerHTML = `<i class="fa-solid fa-check me-1"></i> Copied!`;
      btnElement.classList.add('btn-success');
      setTimeout(() => {
        btnElement.innerHTML = originalHTML;
        btnElement.classList.remove('btn-success');
      }, 2000);
    }
    return true;
  } catch (err) {
    showToast('Failed to copy. Please copy manually.', 'error', '⚠️');
    return false;
  }
}

// WhatsApp share helper
function shareOnWhatsApp(url, customMessage) {
  const defaultMsg = `I created a quiz to test how well you know me! Think you can beat everyone? Play here: ${url}`;
  const text = customMessage || defaultMsg;
  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`;
  window.open(whatsappUrl, '_blank', 'noopener,noreferrer');
}

// Web Share API with fallback
async function shareQuizNative(title, text, url) {
  if (navigator.share) {
    try {
      await navigator.share({
        title: title || 'BondQuiz - How Well Do You Know Me?',
        text: text || 'Take my friendship quiz and see how well you know me!',
        url: url
      });
      return true;
    } catch (err) {
      if (err.name !== 'AbortError') {
        copyToClipboard(url);
      }
    }
  } else {
    copyToClipboard(url);
  }
}

// Celebration Confetti blast
function launchCelebrationConfetti() {
  if (typeof confetti === 'function') {
    // Blast 1
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 }
    });
    // Blast 2
    setTimeout(() => {
      confetti({
        particleCount: 60,
        angle: 60,
        spread: 55,
        origin: { x: 0 }
      });
      confetti({
        particleCount: 60,
        angle: 120,
        spread: 55,
        origin: { x: 1 }
      });
    }, 250);
  }
}

// Initialize navbar and sound toggles on page load
document.addEventListener('DOMContentLoaded', () => {
  const navbar = document.querySelector('.navbar-bond');
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 20) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    });
  }

  // Sound toggle button if present
  const soundBtn = document.getElementById('soundToggleBtn');
  if (soundBtn && window.soundFX) {
    const updateSoundIcon = () => {
      soundBtn.innerHTML = window.soundFX.muted 
        ? '<i class="fa-solid fa-volume-xmark"></i>' 
        : '<i class="fa-solid fa-volume-high"></i>';
      soundBtn.title = window.soundFX.muted ? 'Unmute sounds' : 'Mute sounds';
    };
    updateSoundIcon();
    soundBtn.addEventListener('click', () => {
      window.soundFX.toggleMute();
      updateSoundIcon();
      showToast(window.soundFX.muted ? 'Sound muted' : 'Sound enabled', 'info', window.soundFX.muted ? '🔇' : '🔊');
    });
  }

  // Initialize My Quizzes & Leaderboards
  renderMyQuizzes();
});

// My Quizzes Persistent Manager
function getSavedQuizzes() {
  try {
    return JSON.parse(localStorage.getItem('bondquiz_created_quizzes') || '[]');
  } catch (e) {
    return [];
  }
}

function removeSavedQuiz(publicId) {
  if (!confirm('Remove this quiz from your saved list? (The quiz will still exist on the server)')) return;
  let quizzes = getSavedQuizzes();
  quizzes = quizzes.filter(q => q.public_id !== publicId);
  localStorage.setItem('bondquiz_created_quizzes', JSON.stringify(quizzes));
  renderMyQuizzes();
  showToast('Removed from your list', 'info', '🗑️');
}

function renderMyQuizzes() {
  const quizzes = getSavedQuizzes();
  
  // 1. Update Navbar item & badge
  const navItem = document.getElementById('navMyQuizzesItem');
  const badge = document.getElementById('myQuizzesBadge');
  if (navItem) {
    if (quizzes.length > 0) {
      navItem.style.display = 'block';
      if (badge) {
        badge.innerText = quizzes.length;
        badge.style.display = 'inline-block';
      }
    } else {
      navItem.style.display = 'none';
    }
  }

  // 2. Populate Offcanvas Body
  const offcanvasBody = document.getElementById('myQuizzesOffcanvasBody');
  if (offcanvasBody) {
    if (quizzes.length === 0) {
      offcanvasBody.innerHTML = `
        <div class="text-center p-4 text-muted">
          <i class="fa-solid fa-trophy fa-3x mb-3 text-warning opacity-50"></i>
          <h6 class="fw-bold">No quizzes created yet!</h6>
          <p class="small">Create a quiz for your besties in 60 seconds and your live leaderboard will always appear here!</p>
          <a href="/create" class="btn btn-bond-primary btn-sm rounded-pill mt-2">
            <i class="fa-solid fa-wand-magic-sparkles me-1"></i> Create a Quiz
          </a>
        </div>
      `;
    } else {
      offcanvasBody.innerHTML = `
        <p class="text-muted small mb-3">
          Here are the quizzes you created. You can check the live leaderboard or manage answers anytime!
        </p>
        <div class="d-flex flex-column gap-3">
          ${quizzes.map(q => {
            const host = window.location.origin;
            const lbUrl = `/quiz/${q.public_id}/leaderboard`;
            const dashUrl = `/creator/${q.public_id}?token=${q.creator_token}`;
            const quizUrl = `${host}/quiz/${q.public_id}`;
            const dateStr = q.created_at ? new Date(q.created_at).toLocaleDateString() : '';

            return `
              <div class="card p-3 border shadow-sm rounded-4 position-relative">
                <button type="button" class="btn-close position-absolute top-0 end-0 m-2" 
                  style="font-size: 0.75rem;" title="Remove from list" onclick="removeSavedQuiz('${q.public_id}')"></button>
                <div class="fw-bold fs-6 mb-1 text-truncate pe-4">${escapeHtml(q.title || 'Friendship Quiz')}</div>
                <div class="small text-muted mb-3">
                  <span>${dateStr ? '📅 ' + dateStr : ''}</span>
                  <span class="badge bg-light text-primary ms-1">ID: ${q.public_id}</span>
                </div>
                
                <div class="d-grid gap-2">
                  <a href="${lbUrl}" class="btn btn-bond-primary btn-sm fw-bold">
                    <i class="fa-solid fa-trophy me-1 text-warning"></i> View Leaderboard
                  </a>
                  <div class="d-flex gap-2">
                    <a href="${dashUrl}" class="btn btn-bond-secondary btn-sm flex-grow-1 fw-semibold">
                      <i class="fa-solid fa-chart-line me-1"></i> Dashboard
                    </a>
                    <button class="btn btn-bond-outline btn-sm" onclick="copyToClipboard('${quizUrl}', this)" title="Copy Quiz Link">
                      <i class="fa-regular fa-copy"></i>
                    </button>
                  </div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    }
  }

  // 3. Populate Home Page Section if on index.html
  const homeSection = document.getElementById('myQuizzesHomeSection');
  const homeContainer = document.getElementById('myQuizzesHomeContainer');
  if (homeSection && homeContainer) {
    if (quizzes.length > 0) {
      homeSection.classList.remove('d-none');
      homeContainer.innerHTML = quizzes.map(q => {
        const host = window.location.origin;
        const lbUrl = `/quiz/${q.public_id}/leaderboard`;
        const dashUrl = `/creator/${q.public_id}?token=${q.creator_token}`;
        const quizUrl = `${host}/quiz/${q.public_id}`;
        const dateStr = q.created_at ? new Date(q.created_at).toLocaleDateString() : '';

        return `
          <div class="col-md-6 col-lg-4">
            <div class="quiz-card p-4 h-100 position-relative">
              <span class="badge badge-soft-primary mb-2">
                <i class="fa-solid fa-crown text-warning me-1"></i> Your Created Quiz
              </span>
              <h5 class="fw-bold mb-1">${escapeHtml(q.title || 'My Friendship Quiz')}</h5>
              <div class="small text-muted mb-3">${dateStr ? 'Created on ' + dateStr : ''}</div>
              
              <div class="d-flex flex-column gap-2 mt-auto">
                <a href="${lbUrl}" class="btn btn-bond-primary w-100 fw-bold">
                  <i class="fa-solid fa-trophy me-2 text-warning"></i> View Live Leaderboard
                </a>
                <div class="d-flex gap-2">
                  <a href="${dashUrl}" class="btn btn-bond-secondary flex-grow-1">
                    <i class="fa-solid fa-chart-line me-1"></i> Dashboard
                  </a>
                  <button class="btn btn-bond-outline" onclick="copyToClipboard('${quizUrl}', this)" title="Copy Link">
                    <i class="fa-regular fa-copy"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        `;
      }).join('');
    } else {
      homeSection.classList.add('d-none');
    }
  }

  // 4. If on public leaderboard page, check if current user is the creator!
  const creatorBanner = document.getElementById('creatorLeaderboardBanner');
  const creatorBannerLink = document.getElementById('creatorDashboardBannerLink');
  if (creatorBanner && creatorBannerLink) {
    const currentPublicId = document.getElementById('leaderboardPageApp')?.dataset?.publicId;
    if (currentPublicId) {
      const match = quizzes.find(q => q.public_id === currentPublicId);
      if (match && match.creator_token) {
        creatorBanner.classList.remove('d-none');
        creatorBannerLink.href = `/creator/${currentPublicId}?token=${match.creator_token}`;
      }
    }
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
