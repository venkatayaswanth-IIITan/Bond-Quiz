from flask import Blueprint, request, jsonify, render_template, abort
from models import Quiz, Attempt, Question, db
from routes.creator_routes import require_creator_auth, extract_token_from_request
from services.quiz_service import get_leaderboard_data, get_creator_dashboard_stats

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/creator/<public_id>')
def creator_dashboard_page(public_id):
    """
    Renders the private creator dashboard.
    Authentication token can be present in query ?token=... or restored by client from localStorage.
    """
    quiz = Quiz.query.filter_by(public_id=public_id).first_or_404()
    token = request.args.get('token', '')
    return render_template('dashboard.html', quiz=quiz, token=token)


@dashboard_bp.route('/api/creator/dashboard/<public_id>', methods=['GET'])
@require_creator_auth
def get_dashboard_data(public_id):
    """Returns complete stats, quiz meta, top participants, and config."""
    quiz = Quiz.query.filter_by(public_id=public_id).first_or_404()

    stats = get_creator_dashboard_stats(quiz)
    leaderboard = get_leaderboard_data(quiz)

    return jsonify({
        'status': 'success',
        'quiz': quiz.to_creator_dict(),
        'stats': stats,
        'leaderboard': leaderboard
    })


@dashboard_bp.route('/api/creator/leaderboard/<public_id>', methods=['GET'])
@require_creator_auth
def get_creator_leaderboard(public_id):
    """Returns current leaderboard ranks and scores."""
    quiz = Quiz.query.filter_by(public_id=public_id).first_or_404()
    leaderboard = get_leaderboard_data(quiz)
    return jsonify({
        'status': 'success',
        'leaderboard': leaderboard
    })


@dashboard_bp.route('/api/creator/attempts/<public_id>', methods=['GET'])
@require_creator_auth
def get_creator_attempts(public_id):
    """
    Returns all participant attempts including individual question answers,
    so the creator can see exactly who chose what answer!
    """
    quiz = Quiz.query.filter_by(public_id=public_id).first_or_404()

    attempts = Attempt.query.filter_by(quiz_id=quiz.id, is_completed=True)\
        .order_by(Attempt.created_at.desc())\
        .all()

    # Pre-fetch questions map
    q_map = {q.id: q for q in quiz.questions}

    detailed_attempts = []
    for att in attempts:
        answers_list = []
        for ans in att.answers:
            q = q_map.get(ans.question_id)
            correct_opt = next((opt for opt in q.options if opt.is_correct), None) if q else None
            answers_list.append({
                'question_id': ans.question_id,
                'question_text': q.question_text if q else 'Unknown Question',
                'selected_option_id': ans.selected_option_id,
                'selected_text': ans.selected_option.option_text if ans.selected_option else 'Skipped',
                'correct_option_id': correct_opt.id if correct_opt else None,
                'correct_text': correct_opt.option_text if correct_opt else '',
                'is_correct': ans.is_correct
            })

        detailed_attempts.append({
            'id': att.id,
            'participant_name': att.participant_name,
            'score': att.score,
            'total_questions': att.total_questions,
            'percentage': round(att.percentage, 1),
            'completed_at': att.created_at.strftime("%b %d, %Y • %I:%M %p"),
            'answers': answers_list
        })

    return jsonify({
        'status': 'success',
        'attempts': detailed_attempts
    })
