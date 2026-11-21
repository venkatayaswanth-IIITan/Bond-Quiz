from flask import Blueprint, request, jsonify
from models import Quiz, Question, Option, db
from functools import wraps

creator_bp = Blueprint('creator', __name__)

def extract_token_from_request() -> str:
    """Extract creator token from headers, auth header, query params, or json body."""
    token = request.headers.get('X-Creator-Token')
    if not token and 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
    if not token:
        token = request.args.get('token')
    if not token and request.is_json:
        data = request.get_json(silent=True) or {}
        token = data.get('creator_token') or data.get('token')
    return token or ''

def require_creator_auth(f):
    """Decorator ensuring request possesses a valid creator token for the quiz."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        public_id = kwargs.get('public_id')
        quiz = None
        if public_id:
            quiz = Quiz.query.filter_by(public_id=public_id).first()
            if not quiz:
                return jsonify({'error': 'Quiz not found'}), 404

        token = extract_token_from_request()
        if not token:
            return jsonify({'error': 'Missing creator access token. Unauthorized.'}), 401

        if quiz and not quiz.verify_creator_token(token):
            return jsonify({'error': 'Invalid creator access token. Access denied.'}), 403

        # Attach quiz to kwargs if route expects it
        return f(*args, **kwargs)
    return decorated_function


@creator_bp.route('/api/creator/quizzes/<public_id>', methods=['PUT'])
@require_creator_auth
def update_quiz(public_id):
    """Update quiz metadata (title, description, theme, is_active status)."""
    quiz = Quiz.query.filter_by(public_id=public_id).first_or_404()
    data = request.get_json() or {}

    if 'title' in data:
        title = data['title'].strip()
        if not title or len(title) > 150:
            return jsonify({'error': 'Title must be between 1 and 150 characters.'}), 422
        quiz.title = title

    if 'description' in data:
        quiz.description = data['description'].strip()

    if 'theme' in data:
        quiz.theme = data['theme'].strip()

    if 'avatar' in data:
        quiz.avatar = data['avatar'].strip()

    if 'is_active' in data:
        quiz.is_active = bool(data['is_active'])

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Quiz updated successfully!',
        'quiz': quiz.to_creator_dict()
    })


@creator_bp.route('/api/creator/quizzes/<public_id>', methods=['DELETE'])
@require_creator_auth
def delete_quiz(public_id):
    """Permanently delete a quiz and all associated attempts and answers."""
    quiz = Quiz.query.filter_by(public_id=public_id).first_or_404()
    db.session.delete(quiz)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Quiz deleted permanently.'
    })


@creator_bp.route('/api/creator/quizzes/<public_id>/questions', methods=['POST'])
@require_creator_auth
def add_question(public_id):
    """Add a new question with options to an existing quiz."""
    quiz = Quiz.query.filter_by(public_id=public_id).first_or_404()
    data = request.get_json() or {}

    q_text = (data.get('question_text') or '').strip()
    options_data = data.get('options') or []
    correct_index = data.get('correct_index', 0)

    if not q_text:
        return jsonify({'error': 'Question text cannot be blank.'}), 422
    if len(options_data) < 2 or len(options_data) > 4:
        return jsonify({'error': 'Question must have between 2 and 4 options.'}), 422

    max_pos = len(quiz.questions)
    question = Question(
        quiz_id=quiz.id,
        question_text=q_text,
        position=max_pos + 1
    )
    db.session.add(question)
    db.session.flush()

    for idx, opt_item in enumerate(options_data):
        if isinstance(opt_item, dict):
            opt_text = (opt_item.get('option_text') or opt_item.get('text') or '').strip()
            is_corr = bool(opt_item.get('is_correct', False))
        else:
            opt_text = str(opt_item).strip()
            is_corr = (idx == correct_index)

        if not opt_text:
            return jsonify({'error': f"Option #{idx+1} cannot be empty."}), 422

        option = Option(
            question_id=question.id,
            option_text=opt_text,
            is_correct=is_corr
        )
        db.session.add(option)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Question added successfully!',
        'question': question.to_creator_dict()
    }), 201


@creator_bp.route('/api/creator/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    """Update an existing question text, options, and correct option."""
    question = Question.query.get_or_404(question_id)
    quiz = question.quiz

    token = extract_token_from_request()
    if not token or not quiz.verify_creator_token(token):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    if 'question_text' in data:
        q_text = data['question_text'].strip()
        if not q_text:
            return jsonify({'error': 'Question text cannot be blank.'}), 422
        question.question_text = q_text

    if 'options' in data:
        raw_options = data['options']
        if len(raw_options) < 2 or len(raw_options) > 4:
            return jsonify({'error': 'Question must have 2 to 4 options.'}), 422

        # Replace existing options
        Option.query.filter_by(question_id=question.id).delete()
        correct_index = data.get('correct_index', 0)
        has_correct = False

        for idx, opt_item in enumerate(raw_options):
            if isinstance(opt_item, dict):
                opt_text = (opt_item.get('option_text') or opt_item.get('text') or '').strip()
                is_corr = bool(opt_item.get('is_correct', False))
            else:
                opt_text = str(opt_item).strip()
                is_corr = (idx == correct_index)

            if is_corr:
                has_correct = True

            option = Option(
                question_id=question.id,
                option_text=opt_text,
                is_correct=is_corr
            )
            db.session.add(option)

        if not has_correct:
            first_opt = Option.query.filter_by(question_id=question.id).first()
            if first_opt:
                first_opt.is_correct = True

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Question updated successfully!',
        'question': question.to_creator_dict()
    })


@creator_bp.route('/api/creator/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Delete a single question from the quiz."""
    question = Question.query.get_or_404(question_id)
    quiz = question.quiz

    token = extract_token_from_request()
    if not token or not quiz.verify_creator_token(token):
        return jsonify({'error': 'Unauthorized'}), 403

    if len(quiz.questions) <= 3:
        return jsonify({'error': 'Quiz must have at least 3 questions. Cannot delete further.'}), 422

    db.session.delete(question)
    # Re-sequence positions
    remaining_questions = Question.query.filter_by(quiz_id=quiz.id).order_by(Question.position).all()
    for idx, q in enumerate(remaining_questions, start=1):
        q.position = idx

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Question deleted.'
    })
