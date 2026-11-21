import unittest
import json
from app import create_app
from models import db, Quiz, Question, Option, Attempt, Answer
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class BondQuizEndToEndTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_01_home_page_renders(self):
        """Test home landing page renders successfully."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"How well do your friends", res.data)
        self.assertIn(b"really know you?", res.data)
        self.assertIn(b"Best Friend Challenge", res.data)

    def test_02_create_quiz_with_five_questions(self):
        """Test quiz creation with 5 questions and verify security."""
        payload = {
            'creator_name': 'Alex',
            'title': 'How Well Do You Know Alex?',
            'description': 'The ultimate bestie test!',
            'category': 'best_friend',
            'theme': 'purple_bliss',
            'avatar': 'cat',
            'questions': [
                {
                    'question_text': 'What is my favorite comfort food?',
                    'options': ['Pizza 🍕', 'Burgers 🍔', 'Ramen 🍜', 'Ice Cream 🍦'],
                    'correct_index': 2 # Ramen
                },
                {
                    'question_text': 'What is my dream destination?',
                    'options': ['Tokyo 🌸', 'Paris 🗼', 'Bali 🏝️', 'NYC 🗽'],
                    'correct_index': 0 # Tokyo
                },
                {
                    'question_text': 'What is my biggest pet peeve?',
                    'options': ['Loud chewing', 'Being late', 'Slow walkers', 'Unread texts'],
                    'correct_index': 1 # Being late
                },
                {
                    'question_text': 'What time do I usually wake up?',
                    'options': ['6:00 AM', '8:00 AM', '10:00 AM', '12:00 PM'],
                    'correct_index': 1 # 8:00 AM
                },
                {
                    'question_text': 'If I won a million dollars, first purchase?',
                    'options': ['Dream house', 'World tour', 'Supercar', 'Crypto'],
                    'correct_index': 1 # World tour
                }
            ]
        }

        res = self.client.post('/api/quizzes', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue('public_id' in data)
        self.assertTrue('creator_token' in data)
        self.assertTrue(data['creator_token'].startswith('ctk_'))
        self.assertIn(data['public_id'], data['quiz_url'])
        self.assertIn(data['creator_token'], data['dashboard_url'])

        # Verify DB records
        quiz = Quiz.query.filter_by(public_id=data['public_id']).first()
        self.assertIsNotNone(quiz)
        self.assertEqual(len(quiz.questions), 5)
        self.assertEqual(quiz.creator_name, 'Alex')
        self.assertTrue(quiz.verify_creator_token(data['creator_token']))

        # Verify public API NEVER leaks is_correct or creator token
        pub_res = self.client.get(f"/api/quizzes/{data['public_id']}")
        self.assertEqual(pub_res.status_code, 200)
        pub_data = pub_res.get_json()
        self.assertNotIn('creator_token_hash', json.dumps(pub_data))
        for q in pub_data['quiz']['questions']:
            for opt in q['options']:
                self.assertNotIn('is_correct', opt, "Public API must never expose is_correct in options!")

    def test_03_participant_attempts_and_server_scoring(self):
        """Test full participant flow, anti-cheat server scoring, and duplicate blocking."""
        # 1. Create a quiz with 3 questions
        create_res = self.client.post('/api/quizzes', json={
            'creator_name': 'Maya',
            'title': 'Maya\'s Friendship Test',
            'category': 'friends',
            'theme': 'sunset_glow',
            'avatar': 'sparkles',
            'questions': [
                {
                    'question_text': 'My coffee order?',
                    'options': ['Iced Latte', 'Black Coffee', 'Caramel Macchiato', 'Green Tea'],
                    'correct_index': 0
                },
                {
                    'question_text': 'My spirit animal?',
                    'options': ['Golden Retriever', 'Black Cat', 'Sloth', 'Owl'],
                    'correct_index': 1
                },
                {
                    'question_text': 'Favorite season?',
                    'options': ['Summer', 'Autumn', 'Winter', 'Spring'],
                    'correct_index': 1
                }
            ]
        })
        created_data = create_res.get_json()
        public_id = created_data['public_id']
        creator_token = created_data['creator_token']

        # Get questions to know their DB IDs
        quiz_obj = Quiz.query.filter_by(public_id=public_id).first()
        q1, q2, q3 = quiz_obj.questions

        # Find option IDs
        q1_corr = next(o.id for o in q1.options if o.is_correct)
        q1_wrong = next(o.id for o in q1.options if not o.is_correct)

        q2_corr = next(o.id for o in q2.options if o.is_correct)
        q2_wrong = next(o.id for o in q2.options if not o.is_correct)

        q3_corr = next(o.id for o in q3.options if o.is_correct)

        # 2. Start attempt for Participant 1 (Jordan - 100% score)
        start_res1 = self.client.post(f"/api/quizzes/{public_id}/start", json={'participant_name': 'Jordan'})
        self.assertEqual(start_res1.status_code, 200)
        att_token_1 = start_res1.get_json()['attempt_token']

        # Submit Jordan's answers (all 3 correct)
        sub_res1 = self.client.post(f"/api/quizzes/{public_id}/submit", json={
            'attempt_token': att_token_1,
            'answers': {
                q1.id: q1_corr,
                q2.id: q2_corr,
                q3.id: q3_corr
            }
        })
        self.assertEqual(sub_res1.status_code, 200)
        res1_data = sub_res1.get_json()['result']
        self.assertEqual(res1_data['score'], 3)
        self.assertEqual(res1_data['percentage'], 100.0)
        self.assertIn('Ultimate', res1_data['feedback']['tier'])

        # 3. Verify duplicate submission is rejected (409 Conflict)
        dup_res = self.client.post(f"/api/quizzes/{public_id}/submit", json={
            'attempt_token': att_token_1,
            'answers': { q1.id: q1_corr }
        })
        self.assertEqual(dup_res.status_code, 409)

        # 4. Start attempt for Participant 2 (Taylor - 1 of 3 correct = 33.3%)
        start_res2 = self.client.post(f"/api/quizzes/{public_id}/start", json={'participant_name': 'Taylor'})
        att_token_2 = start_res2.get_json()['attempt_token']

        sub_res2 = self.client.post(f"/api/quizzes/{public_id}/submit", json={
            'attempt_token': att_token_2,
            'answers': {
                q1.id: q1_wrong,
                q2.id: q2_wrong,
                q3.id: q3_corr
            }
        })
        self.assertEqual(sub_res2.status_code, 200)
        res2_data = sub_res2.get_json()['result']
        self.assertEqual(res2_data['score'], 1)
        self.assertEqual(res2_data['percentage'], 33.3)
        self.assertIn('Fake Friend', res2_data['feedback']['tier'])

        # 5. Check Public Leaderboard (Rank 1: Jordan, Rank 2: Taylor)
        lb_res = self.client.get(f"/api/quizzes/{public_id}/leaderboard")
        self.assertEqual(lb_res.status_code, 200)
        lb = lb_res.get_json()['leaderboard']
        self.assertEqual(len(lb), 2)
        self.assertEqual(lb[0]['participant_name'], 'Jordan')
        self.assertEqual(lb[0]['rank'], 1)
        self.assertEqual(lb[0]['trophy'], '🥇')
        self.assertEqual(lb[1]['participant_name'], 'Taylor')
        self.assertEqual(lb[1]['rank'], 2)
        self.assertEqual(lb[1]['trophy'], '🥈')

        # 6. Check Creator Dashboard with valid creator token
        dash_res = self.client.get(
            f"/api/creator/dashboard/{public_id}",
            headers={'X-Creator-Token': creator_token}
        )
        self.assertEqual(dash_res.status_code, 200)
        dash_data = dash_res.get_json()
        self.assertEqual(dash_data['stats']['total_participants'], 2)
        self.assertEqual(dash_data['stats']['highest_score'], 3)
        self.assertEqual(dash_data['stats']['average_score'], 2.0)

        # 7. Check Creator Attempts (detailed individual answer inspector)
        att_res = self.client.get(
            f"/api/creator/attempts/{public_id}",
            headers={'X-Creator-Token': creator_token}
        )
        self.assertEqual(att_res.status_code, 200)
        attempts = att_res.get_json()['attempts']
        self.assertEqual(len(attempts), 2)
        # Taylor has 2 wrong answers and 1 correct
        taylor_att = next(a for a in attempts if a['participant_name'] == 'Taylor')
        correct_count = sum(1 for ans in taylor_att['answers'] if ans['is_correct'])
        self.assertEqual(correct_count, 1)

        # 8. Check unauthorized creator access
        unauth_res1 = self.client.get(f"/api/creator/dashboard/{public_id}")
        self.assertEqual(unauth_res1.status_code, 401)

        unauth_res2 = self.client.get(
            f"/api/creator/dashboard/{public_id}",
            headers={'X-Creator-Token': 'wrong_token'}
        )
        self.assertEqual(unauth_res2.status_code, 403)

    def test_04_creator_edit_toggle_and_delete_operations(self):
        """Test creator quiz update, pause/reopen, question add/delete, and quiz deletion."""
        # Create quiz
        create_res = self.client.post('/api/quizzes', json={
            'creator_name': 'Sam',
            'title': 'Sam\'s Vibe Quiz',
            'category': 'best_friend',
            'theme': 'bubblegum',
            'avatar': 'fire',
            'questions': [
                {'question_text': 'Q1', 'options': ['A', 'B', 'C', 'D'], 'correct_index': 0},
                {'question_text': 'Q2', 'options': ['A', 'B', 'C', 'D'], 'correct_index': 1},
                {'question_text': 'Q3', 'options': ['A', 'B', 'C', 'D'], 'correct_index': 2}
            ]
        })
        data = create_res.get_json()
        public_id = data['public_id']
        token = data['creator_token']

        # 1. Update quiz title and theme
        update_res = self.client.put(
            f"/api/creator/quizzes/{public_id}",
            headers={'X-Creator-Token': token},
            json={'title': 'Sam\'s Updated Challenge', 'theme': 'cyber_neon'}
        )
        self.assertEqual(update_res.status_code, 200)
        updated_quiz = Quiz.query.filter_by(public_id=public_id).first()
        self.assertEqual(updated_quiz.title, 'Sam\'s Updated Challenge')
        self.assertEqual(updated_quiz.theme, 'cyber_neon')

        # 2. Add a new 4th question
        add_q_res = self.client.post(
            f"/api/creator/quizzes/{public_id}/questions",
            headers={'X-Creator-Token': token},
            json={
                'question_text': 'What is my hidden talent?',
                'options': ['Singing', 'Dancing', 'Cooking', 'Sleeping'],
                'correct_index': 3
            }
        )
        self.assertEqual(add_q_res.status_code, 201)
        self.assertEqual(len(updated_quiz.questions), 4)

        # 3. Toggle quiz status to inactive (close quiz)
        toggle_res = self.client.put(
            f"/api/creator/quizzes/{public_id}",
            headers={'X-Creator-Token': token},
            json={'is_active': False}
        )
        self.assertEqual(toggle_res.status_code, 200)
        self.assertFalse(updated_quiz.is_active)

        # Verify that start attempt on closed quiz returns 403
        blocked_start = self.client.post(
            f"/api/quizzes/{public_id}/start",
            json={'participant_name': 'LateFriend'}
        )
        self.assertEqual(blocked_start.status_code, 403)

        # 4. Reopen quiz
        self.client.put(
            f"/api/creator/quizzes/{public_id}",
            headers={'X-Creator-Token': token},
            json={'is_active': True}
        )

        # 5. Delete quiz completely
        del_res = self.client.delete(
            f"/api/creator/quizzes/{public_id}",
            headers={'X-Creator-Token': token}
        )
        self.assertEqual(del_res.status_code, 200)
        self.assertIsNone(Quiz.query.filter_by(public_id=public_id).first())

if __name__ == '__main__':
    unittest.main()
