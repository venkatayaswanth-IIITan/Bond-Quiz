import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(BASE_DIR, 'bondquiz.sqlite')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Security and rate limit configurations
    MAX_QUESTIONS_PER_QUIZ = 30
    MIN_QUESTIONS_PER_QUIZ = 3
    MAX_OPTIONS_PER_QUESTION = 4
    TOKEN_SALT = os.environ.get('TOKEN_SALT', 'bondquiz-salt-secure-2026')
