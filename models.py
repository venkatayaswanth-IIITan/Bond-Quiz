from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    creator_token_hash = db.Column(db.String(256), nullable=False)
    creator_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True, default='')
    category = db.Column(db.String(50), nullable=False, default='best_friend')
    theme = db.Column(db.String(50), nullable=False, default='purple_bliss')
    avatar = db.Column(db.String(50), nullable=False, default='sparkles')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    questions = db.relationship(
        'Question',
        backref='quiz',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='Question.position'
    )
    attempts = db.relationship(
        'Attempt',
        backref='quiz',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='Attempt.created_at.desc()'
    )

    def set_creator_token(self, token: str):
        self.creator_token_hash = generate_password_hash(token)

    def verify_creator_token(self, token: str) -> bool:
        if not token or not self.creator_token_hash:
            return False
        return check_password_hash(self.creator_token_hash, token)

    def to_public_dict(self):
        """Public representation for quiz takers - DOES NOT expose correct answers."""
        return {
            'public_id': self.public_id,
            'creator_name': self.creator_name,
            'title': self.title,
            'description': self.description or '',
            'category': self.category,
            'theme': self.theme,
            'avatar': self.avatar,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'total_questions': len(self.questions),
            'questions': [q.to_public_dict() for q in self.questions]
        }

    def to_creator_dict(self):
        """Full representation for the creator - includes correct answers, NEVER creator_token_hash."""
        return {
            'public_id': self.public_id,
            'creator_name': self.creator_name,
            'title': self.title,
            'description': self.description or '',
            'category': self.category,
            'theme': self.theme,
            'avatar': self.avatar,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'total_questions': len(self.questions),
            'questions': [q.to_creator_dict() for q in self.questions]
        }


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False, index=True)
    question_text = db.Column(db.String(300), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=1)

    options = db.relationship(
        'Option',
        backref='question',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='Option.id'
    )
    answers = db.relationship(
        'Answer',
        backref='question',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def to_public_dict(self):
        return {
            'id': self.id,
            'question_text': self.question_text,
            'position': self.position,
            'options': [opt.to_public_dict() for opt in self.options]
        }

    def to_creator_dict(self):
        return {
            'id': self.id,
            'question_text': self.question_text,
            'position': self.position,
            'options': [opt.to_creator_dict() for opt in self.options]
        }


class Option(db.Model):
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False, index=True)
    option_text = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)

    def to_public_dict(self):
        """Never leak is_correct in public payload!"""
        return {
            'id': self.id,
            'option_text': self.option_text
        }

    def to_creator_dict(self):
        return {
            'id': self.id,
            'option_text': self.option_text,
            'is_correct': self.is_correct
        }


class Attempt(db.Model):
    __tablename__ = 'attempts'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False, index=True)
    participant_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    total_questions = db.Column(db.Integer, default=0, nullable=False)
    percentage = db.Column(db.Float, default=0.0, nullable=False)
    attempt_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    answers = db.relationship(
        'Answer',
        backref='attempt',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def to_dict(self, include_answers=False):
        data = {
            'id': self.id,
            'attempt_token': self.attempt_token,
            'participant_name': self.participant_name,
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': round(self.percentage, 1),
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat()
        }
        if include_answers:
            data['answers'] = [a.to_dict() for a in self.answers]
        return data


class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('attempts.id', ondelete='CASCADE'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='CASCADE'), nullable=True)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)

    selected_option = db.relationship('Option', foreign_keys=[selected_option_id])

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'selected_option_id': self.selected_option_id,
            'selected_option_text': self.selected_option.option_text if self.selected_option else 'Skipped',
            'is_correct': self.is_correct
        }
