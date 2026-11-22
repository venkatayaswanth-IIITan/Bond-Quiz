from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template, abort, url_for, Response
from models import Quiz, Question, Option, Attempt, Answer, db
from services.quiz_service import (
    create_quiz_with_questions,
    generate_attempt_token,
    get_leaderboard_data,
    QUESTION_TEMPLATES
)
from services.scoring_service import calculate_and_record_attempt

quiz_bp = Blueprint('quiz', __name__)

# ==========================================
# PAGE VIEWS
# ==========================================

@quiz_bp.route('/')
def home():
    """Landing Home Page with attractive Gen Z design."""
    return render_template('index.html')


@quiz_bp.route('/create')
def create_quiz_page():
    """Quiz creation multi-step wizard."""
    category = request.args.get('category', 'best_friend')
    return render_template('create_quiz.html', initial_category=category)


@quiz_bp.route('/quiz/<public_id>')
def play_quiz_page(public_id):
    """Public quiz taking page."""
    quiz = Quiz.query.filter_by(public_id=public_id).first_or_404()
    return render_template('quiz.html', quiz=quiz)


@quiz_bp.route('/quiz/<public_id>/leaderboard')
def public_leaderboard_page(public_id):
    """Public leaderboard view for participants."""
    quiz = Quiz.query.filter_by(public_id=public_id).first_or_404()
    leaderboard = get_leaderboard_data(quiz)
    return render_template('leaderboard.html', quiz=quiz, leaderboard=leaderboard)


# ==========================================
# SEO & CRAWLER ENDPOINTS
# ==========================================

@quiz_bp.route('/robots.txt', methods=['GET'])
def robots_txt():
    """Serves robots.txt instructing web crawlers."""
    content = """User-agent: *
Allow: /
Allow: /create
Allow: /quiz/
Allow: /static/
Disallow: /creator/
Disallow: /api/

Sitemap: https://bond-quiz-1.onrender.com/sitemap.xml
"""
    response = Response(content, mimetype='text/plain')
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response


@quiz_bp.route('/sitemap.xml', methods=['GET'])
def sitemap_xml():
    """Generates valid XML sitemap for Google Search Console."""
    base_url = "https://bond-quiz-1.onrender.com"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    urls = [
        {"loc": f"{base_url}/", "lastmod": today, "changefreq": "daily", "priority": "1.0"},
        {"loc": f"{base_url}/create", "lastmod": today, "changefreq": "weekly", "priority": "0.9"},
    ]

    # Include public active quizzes and their leaderboards
    try:
        active_quizzes = Quiz.query.filter_by(is_active=True).order_by(Quiz.created_at.desc()).limit(200).all()
        for q in active_quizzes:
            q_date = q.created_at.strftime("%Y-%m-%d") if q.created_at else today
            urls.append({
                "loc": f"{base_url}/quiz/{q.public_id}",
                "lastmod": q_date,
                "changefreq": "weekly",
                "priority": "0.7"
            })
            urls.append({
                "loc": f"{base_url}/quiz/{q.public_id}/leaderboard",
                "lastmod": q_date,
                "changefreq": "daily",
                "priority": "0.6"
            })
    except Exception:
        pass

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for u in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{u["loc"]}</loc>')
        xml_lines.append(f'    <lastmod>{u["lastmod"]}</lastmod>')
        xml_lines.append(f'    <changefreq>{u["changefreq"]}</changefreq>')
        xml_lines.append(f'    <priority>{u["priority"]}</priority>')
        xml_lines.append('  </url>')
    xml_lines.append('</urlset>')

    response = Response("\n".join(xml_lines), mimetype='application/xml')
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return response


# ==========================================
# REST API ENDPOINTS
# ==========================================

@quiz_bp.route('/api/templates/<category>', methods=['GET'])
def get_template_questions(category):
    """Returns ready-made questions for a given category."""
    templates = QUESTION_TEMPLATES.get(category, QUESTION_TEMPLATES['best_friend'])
    return jsonify({
        'status': 'success',
        'category': category,
        'templates': templates
    })


@quiz_bp.route('/api/quizzes', methods=['POST'])
def api_create_quiz():
    """
    Creates a new quiz with questions and options.
    Generates a secure creator token and unique public link.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    try:
        creator_name = data.get('creator_name')
        title = data.get('title')
        description = data.get('description', '')
        category = data.get('category', 'best_friend')
        theme = data.get('theme', 'purple_bliss')
        avatar = data.get('avatar', 'sparkles')
        questions = data.get('questions', [])

        quiz, raw_creator_token = create_quiz_with_questions(
            creator_name=creator_name,
            title=title,
            description=description,
            category=category,
            theme=theme,
            avatar=avatar,
            questions_data=questions
        )

        host_url = request.host_url.rstrip('/')
        quiz_url = f"{host_url}/quiz/{quiz.public_id}"
        dashboard_url = f"{host_url}/creator/{quiz.public_id}?token={raw_creator_token}"

        return jsonify({
            'status': 'success',
            'message': 'Quiz created successfully!',
            'public_id': quiz.public_id,
            'creator_token': raw_creator_token,
            'quiz_url': quiz_url,
            'dashboard_url': dashboard_url,
            'quiz': quiz.to_creator_dict()
        }), 201

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f"Failed to create quiz: {str(e)}"}), 500


@quiz_bp.route('/api/quizzes/<public_id>', methods=['GET'])
def api_get_quiz(public_id):
    """
    Public quiz data endpoint.
    NEVER leaks is_correct flag or creator token.
    """
    quiz = Quiz.query.filter_by(public_id=public_id).first()
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404

    if not quiz.is_active:
        return jsonify({
            'error': 'This quiz has been closed by its creator.',
            'is_active': False,
            'title': quiz.title,
            'creator_name': quiz.creator_name
        }), 403

    return jsonify({
        'status': 'success',
        'quiz': quiz.to_public_dict()
    })


@quiz_bp.route('/api/quizzes/<public_id>/start', methods=['POST'])
def api_start_quiz(public_id):
    """
    Registers a participant attempt session.
    Returns an attempt_token to guard against duplicate submissions.
    """
    quiz = Quiz.query.filter_by(public_id=public_id).first()
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404

    if not quiz.is_active:
        return jsonify({'error': 'This quiz is currently closed.'}), 403

    data = request.get_json() or {}
    participant_name = (data.get('participant_name') or '').strip()

    if not participant_name:
        return jsonify({'error': 'Please enter your nickname to play!'}), 422
    if len(participant_name) > 60:
        return jsonify({'error': 'Nickname must be under 60 characters.'}), 422

    # Check recent submission rate for same participant on this quiz
    recent_attempt = Attempt.query.filter_by(
        quiz_id=quiz.id,
        participant_name=participant_name,
        is_completed=True
    ).order_by(Attempt.created_at.desc()).first()

    attempt_token = generate_attempt_token()
    attempt = Attempt(
        quiz_id=quiz.id,
        participant_name=participant_name,
        score=0,
        total_questions=len(quiz.questions),
        percentage=0.0,
        attempt_token=attempt_token,
        is_completed=False
    )
    db.session.add(attempt)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'attempt_token': attempt_token,
        'participant_name': participant_name,
        'total_questions': len(quiz.questions),
        'already_played': bool(recent_attempt)
    })


@quiz_bp.route('/api/quizzes/<public_id>/submit', methods=['POST'])
def api_submit_quiz(public_id):
    """
    Validates participant answers against the server database.
    Calculates final score, records individual answers, and returns full breakdown.
    Guarded with attempt_token to prevent duplicate submissions.
    """
    quiz = Quiz.query.filter_by(public_id=public_id).first()
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404

    data = request.get_json() or {}
    attempt_token = data.get('attempt_token')
    user_answers = data.get('answers') or {}

    if not attempt_token:
        return jsonify({'error': 'Missing attempt token. Please restart quiz.'}), 400

    attempt = Attempt.query.filter_by(attempt_token=attempt_token, quiz_id=quiz.id).first()
    if not attempt:
        return jsonify({'error': 'Invalid or expired attempt token.'}), 404

    if attempt.is_completed:
        return jsonify({'error': 'This attempt has already been submitted and scored.'}), 409

    # Score on server
    result = calculate_and_record_attempt(quiz, attempt, user_answers)

    host_url = request.host_url.rstrip('/')
    leaderboard_url = f"{host_url}/quiz/{quiz.public_id}/leaderboard"

    return jsonify({
        'status': 'success',
        'message': 'Quiz submitted successfully!',
        'result': result,
        'quiz_title': quiz.title,
        'creator_name': quiz.creator_name,
        'leaderboard_url': leaderboard_url
    })


@quiz_bp.route('/api/quizzes/<public_id>/leaderboard', methods=['GET'])
def api_public_leaderboard(public_id):
    """Public read-only leaderboard for a quiz."""
    quiz = Quiz.query.filter_by(public_id=public_id).first()
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404

    leaderboard = get_leaderboard_data(quiz)
    return jsonify({
        'status': 'success',
        'public_id': quiz.public_id,
        'quiz_title': quiz.title,
        'creator_name': quiz.creator_name,
        'leaderboard': leaderboard
    })
