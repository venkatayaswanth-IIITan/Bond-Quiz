"""
Populate a rich sample quiz with participants to showcase the Leaderboard and Dashboard.
"""
from app import create_app
from models import db, Quiz, Question, Option, Attempt, Answer
from services.quiz_service import create_quiz_with_questions, generate_attempt_token
from services.scoring_service import calculate_and_record_attempt

app = create_app()

with app.app_context():
    # Only seed if no quizzes exist
    if Quiz.query.count() == 0:
        print("🌱 Seeding realistic demo quiz for BondQuiz...")
        
        quiz, creator_token = create_quiz_with_questions(
            creator_name="Alex",
            title="How Well Do You Know Alex? (Bestie Edition)",
            description="The real bond test! Only true inner circle friends will score above 80%.",
            category="best_friend",
            theme="purple_bliss",
            avatar="cat",
            questions_data=[
                {
                    'question_text': "What is my absolute favourite food or craving?",
                    'options': ["Crispy Pizza 🍕", "Cheesy Burgers 🍔", "Spicy Ramen / Noodles 🍜", "Sweet Desserts / Ice Cream 🍦"],
                    'correct_index': 2 # Spicy Ramen
                },
                {
                    'question_text': "What is my dream travel destination?",
                    'options': ["Tokyo, Japan 🌸", "Paris, France 🗼", "Bali, Indonesia 🏝️", "New York City, USA 🗽"],
                    'correct_index': 0 # Tokyo
                },
                {
                    'question_text': "What makes me instantly annoyed?",
                    'options': ["Loud chewers / bad manners 😤", "Slow walkers 🚶", "People being late ⏰", "Being left on read 📱"],
                    'correct_index': 3 # Being left on read
                },
                {
                    'question_text': "What is my biggest irrational fear?",
                    'options': ["Creepy spiders 🕷️", "Heights 🎢", "The dark / ghosts 👻", "Public speaking 🎤"],
                    'correct_index': 0 # Spiders
                },
                {
                    'question_text': "If I won $1,000,000 tomorrow, what's my first purchase?",
                    'options': ["A luxury house 🏡", "Travel the world nonstop ✈️", "Supercar shopping spree 🏎️", "Invest it all 💰"],
                    'correct_index': 1 # Travel the world
                }
            ]
        )

        # Questions map
        q1, q2, q3, q4, q5 = quiz.questions

        # Seed Participants:
        participants = [
            ("Jordan (Bestie)", { q1.id: q1.options[2].id, q2.id: q2.options[0].id, q3.id: q3.options[3].id, q4.id: q4.options[0].id, q5.id: q5.options[1].id }), # 5/5 = 100%
            ("Chloe", { q1.id: q1.options[2].id, q2.id: q2.options[0].id, q3.id: q3.options[3].id, q4.id: q4.options[0].id, q5.id: q5.options[0].id }),           # 4/5 = 80%
            ("Sam", { q1.id: q1.options[0].id, q2.id: q2.options[0].id, q3.id: q3.options[3].id, q4.id: q4.options[1].id, q5.id: q5.options[1].id }),             # 3/5 = 60%
            ("Taylor", { q1.id: q1.options[1].id, q2.id: q2.options[2].id, q3.id: q3.options[0].id, q4.id: q4.options[0].id, q5.id: q5.options[3].id }),           # 1/5 = 20%
        ]

        for name, ans_dict in participants:
            att = Attempt(
                quiz_id=quiz.id,
                participant_name=name,
                score=0,
                total_questions=5,
                percentage=0.0,
                attempt_token=generate_attempt_token(),
                is_completed=False
            )
            db.session.add(att)
            db.session.commit()
            calculate_and_record_attempt(quiz, att, ans_dict)

        print(f"✅ Demo quiz created!")
        print(f"Public ID: {quiz.public_id}")
        print(f"Creator Token: {creator_token}")
        print(f"Public URL: http://localhost:5000/quiz/{quiz.public_id}")
        print(f"Leaderboard URL: http://localhost:5000/quiz/{quiz.public_id}/leaderboard")
        print(f"Creator Dashboard: http://localhost:5000/creator/{quiz.public_id}?token={creator_token}")
    else:
        q = Quiz.query.first()
        print(f"ℹ️ Database already contains {Quiz.query.count()} quiz(zes).")
        print(f"Existing Quiz: http://localhost:5000/quiz/{q.public_id}")
