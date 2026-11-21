from typing import Dict, Any, List
from models import Quiz, Question, Option, Attempt, Answer, db

def get_feedback_message(percentage: float, category: str = 'best_friend') -> Dict[str, str]:
    """Return playful feedback messages and titles based on score percentage."""
    if percentage >= 95:
        return {
            'tier': 'Ultimate Soulmate 🏆',
            'title': "Mind Reader Level Unlocked!",
            'message': "Unbelievable! You know them inside and out. You two are practically telepathic!",
            'badge': '🏆',
            'color': '#8B5CF6'
        }
    elif percentage >= 80:
        return {
            'tier': 'VIP Inner Circle 💖',
            'title': "True Bestie Alert!",
            'message': "You know them better than almost anyone! Just a tiny secret or two left to unlock.",
            'badge': '💖',
            'color': '#EC4899'
        }
    elif percentage >= 60:
        return {
            'tier': 'Certified Close Friend ✨',
            'title': "Solid Friendship Energy!",
            'message': "You've got the essentials down! Time for a late-night chat to fill in the rest.",
            'badge': '✨',
            'color': '#F59E0B'
        }
    elif percentage >= 40:
        return {
            'tier': 'Casual Buddy 😊',
            'title': "Getting There!",
            'message': "Not bad, but there is still plenty to learn. Grab some snacks and hang out more!",
            'badge': '😊',
            'color': '#3B82F6'
        }
    else:
        return {
            'tier': 'Fake Friend Alert 👀',
            'title': "Do You Even Know Me?!",
            'message': "Oof! Who is this stranger taking my quiz? We definitely need to spend more quality time together!",
            'badge': '👀',
            'color': '#EF4444'
        }


def calculate_and_record_attempt(quiz: Quiz, attempt: Attempt, user_answers: Dict[int, int]) -> Dict[str, Any]:
    """
    Evaluates participant answers against ground-truth options in the database.
    user_answers is a dict: {question_id: selected_option_id}
    Saves Answer models and updates Attempt score and percentage.
    Returns detailed summary for the participant.
    """
    total_questions = len(quiz.questions)
    if total_questions == 0:
        return {'score': 0, 'percentage': 0.0, 'breakdown': []}

    score = 0
    breakdown = []

    # Map question_id to question
    questions_map = {q.id: q for q in quiz.questions}

    # Delete any prior answers for this attempt (idempotence safety)
    Answer.query.filter_by(attempt_id=attempt.id).delete()

    for q_id, question in questions_map.items():
        # Get selected option id from submitted payload (can be int or string)
        selected_option_id = user_answers.get(q_id) or user_answers.get(str(q_id))
        if selected_option_id is not None:
            try:
                selected_option_id = int(selected_option_id)
            except (ValueError, TypeError):
                selected_option_id = None

        # Find the correct option for this question
        correct_option = next((opt for opt in question.options if opt.is_correct), None)
        selected_option = next((opt for opt in question.options if opt.id == selected_option_id), None) if selected_option_id else None

        is_correct = False
        if correct_option and selected_option and correct_option.id == selected_option.id:
            is_correct = True
            score += 1

        # Record Answer row
        db_answer = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=selected_option.id if selected_option else None,
            is_correct=is_correct
        )
        db.session.add(db_answer)

        # Build response item for participant review
        options_data = []
        for opt in question.options:
            options_data.append({
                'id': opt.id,
                'text': opt.option_text,
                'is_correct': opt.is_correct,
                'was_selected': (selected_option is not None and opt.id == selected_option.id)
            })

        breakdown.append({
            'question_id': question.id,
            'question_text': question.question_text,
            'position': question.position,
            'is_correct': is_correct,
            'selected_option_id': selected_option.id if selected_option else None,
            'selected_text': selected_option.option_text if selected_option else 'No answer selected',
            'correct_option_id': correct_option.id if correct_option else None,
            'correct_text': correct_option.option_text if correct_option else '',
            'options': options_data
        })

    percentage = round((score / total_questions) * 100.0, 1)

    attempt.score = score
    attempt.total_questions = total_questions
    attempt.percentage = percentage
    attempt.is_completed = True

    db.session.commit()

    feedback = get_feedback_message(percentage, quiz.category)

    return {
        'attempt_token': attempt.attempt_token,
        'participant_name': attempt.participant_name,
        'score': score,
        'total_questions': total_questions,
        'percentage': percentage,
        'feedback': feedback,
        'breakdown': breakdown
    }
