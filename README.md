# BondQuiz – How Well Do You Know Me? 💖🏆

A modern, playful, Gen-Z social quiz web application built with **Python Flask**, **Flask-SQLAlchemy**, **SQLite**, and modern responsive CSS/JavaScript.

Users can create personalized quizzes for best friends, friend groups, couples, crushes, and families in under 60 seconds. Quizzes can be shared via a unique link or 1-click WhatsApp share without requiring any participant to log in or register.

---

## 🌟 Key Features

1. **Zero Registration / No Login Needed**:
   - Creators and participants jump straight in without an email, password, or account.
   - Creators receive a secure tokenized private dashboard link stored in local session.
2. **Cheat-Proof Server-Side Scoring**:
   - Correct answers are stored strictly on the server and are **never** leaked via public quiz APIs or inspect element.
   - Server-side attempt tokens prevent duplicate or unauthorized score tampering.
3. **Curated Bestie Questions**:
   - 10 curated questions ready to use out-of-the-box (Full Name, Nickname, Birthday, Favourite Colour, Favourite Food, Favourite Fruit, Favourite Drink, Favourite Movie, Morning or Night, Social Media App).
4. **Live Leaderboard with Podium**:
   - Gold 🥇, Silver 🥈, Bronze 🥉 trophies for top 3 scorers with tie-breaking by earliest completion time.
5. **Private Creator Hub & Dashboard**:
   - View all participant scores, completion dates, and individual answer breakdowns.
   - Toggle quiz status (Active / Closed) or delete quizzes with cascade cleanups.
6. **Vibrant Gen-Z Aesthetic**:
   - 6 colorful themes (`purple_bliss`, `sunset_glow`, `cyber_neon`, `bubblegum`, `midnight_velvet`, `emerald_mint`).
   - Confetti celebrations, Web Audio synthesizer sound effects, and 1-click WhatsApp / Web Share API integration.

---

## 🚀 Deploy to Render (Step-by-Step)

BondQuiz is pre-configured for **Render** (via `render.yaml` and `Procfile` using `gunicorn`).

### Method A: One-Click / Blueprint Deploy
1. Push this repository to your GitHub account (`https://github.com/venkatayaswanth-IIITan/Bond-Quiz`).
2. Log in to [Render.com](https://render.com).
3. Click **New +** → **Blueprint**.
4. Connect your **`Bond-Quiz`** GitHub repository.
5. Render will automatically detect `render.yaml` and set up the Web Service.
6. Click **Apply** to deploy!

### Method B: Manual Web Service Setup
1. On [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service**.
2. Connect your GitHub repository: `venkatayaswanth-IIITan/Bond-Quiz`.
3. Fill in the service configuration:
   - **Name**: `bondquiz`
   - **Runtime**: `Python 3`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: `Free`
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.11.0`
   - `FLASK_DEBUG`: `false`
   - `SECRET_KEY`: *(Click Generate or enter a random 32-character string)*
   - `TOKEN_SALT`: *(Click Generate or enter a random string)*
5. Click **Create Web Service**.
6. Render will build and deploy your app. Once finished, you will receive a free live HTTPS URL (e.g. `https://bondquiz.onrender.com`).

---

## 💻 Local Development Setup

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Clone and Install
```bash
git clone https://github.com/venkatayaswanth-IIITan/Bond-Quiz.git
cd Bond-Quiz

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

### 4. Run Automated Tests
```bash
# Unit tests
python test_app.py

# End-to-end integration tests
python verify_workflow.py
```

---

## 📁 Project Structure

```
Bond-Quiz/
├── app.py                  # Application factory and entrypoint
├── config.py               # Database and app configurations
├── models.py               # SQLAlchemy models (Quiz, Question, Option, Attempt, Answer)
├── requirements.txt        # Production dependencies (Flask, SQLAlchemy, Gunicorn)
├── Procfile                # WSGI command for Render / Heroku
├── render.yaml             # Render Blueprint configuration
├── routes/
│   ├── quiz_routes.py      # Public quiz play, creation, and submission APIs
│   ├── creator_routes.py   # Creator authentication and editing APIs
│   └── dashboard_routes.py # Creator dashboard and analytics APIs
├── services/
│   ├── quiz_service.py     # Question banks, ID generation, database helpers
│   └── scoring_service.py  # Anti-cheat evaluation and tier feedback
├── static/
│   ├── css/                # Gen-Z gradients, animations, and 6 themes
│   └── js/                 # Steppers, confetti, Web Audio, creator storage
└── templates/              # Bootstrap 5 responsive templates
```

---

## 🔒 Security Highlights
- **Hashed Creator Tokens**: Access keys for dashboards are hashed using `werkzeug.security` with PBKDF2:SHA256.
- **Anti-Tampering Tokens**: Single-use attempt tokens generated on quiz start validate every submission.
- **Cheat-Proof API**: Answers are strictly withheld until server-side grading completes.
