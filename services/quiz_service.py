import secrets
import string
from typing import Dict, Any, List, Optional, Tuple
from models import Quiz, Question, Option, Attempt, Answer, db

ALPHABET = string.ascii_lowercase + string.digits

def generate_public_id(length: int = 8) -> str:
    """Generate a clean, URL-safe random string for public quiz access."""
    while True:
        pid = ''.join(secrets.choice(ALPHABET) for _ in range(length))
        if not Quiz.query.filter_by(public_id=pid).first():
            return pid

def generate_creator_token() -> str:
    """Generate a secure secret token for the quiz creator."""
    return f"ctk_{secrets.token_urlsafe(24)}"

def generate_attempt_token() -> str:
    """Generate a unique token for a quiz participant session."""
    return f"att_{secrets.token_urlsafe(24)}"

# Pre-packaged Question Bank for instant quiz creation
QUESTION_TEMPLATES = {
    'best_friend': [
        {
            'question': "What is my absolute favourite food?",
            'options': ["Crispy Pizza 🍕", "Cheesy Burgers 🍔", "Spicy Noodles / Biryani 🍜", "Ice Cream / Desserts 🍦"],
            'correct_index': 0
        },
        {
            'question': "Do I like tea or coffee?",
            'options': ["Hot or Iced Tea 🫖", "Strong Coffee / Latte ☕", "Both equally 💕", "Neither / Energy Drinks ⚡"],
            'correct_index': 1
        },
        {
            'question': "What is my favourite drink?",
            'options': ["Refreshing Boba / Milk Tea 🧋", "Iced Cold Coffee ☕", "Fresh Fruit Smoothie / Juice 🍓", "Fizzy Soda / Mocktail 🥤"],
            'correct_index': 0
        },
        {
            'question': "What is my favourite chocolate?",
            'options': ["Creamy Milk Chocolate 🍫", "Intense Dark Chocolate 🖤", "White Chocolate 🤍", "Nutty Chocolate (KitKat/Snickers) 🥜"],
            'correct_index': 0
        },
        {
            'question': "Do I prefer morning or night?",
            'options': ["Night Owl (Up until 3 AM!) 🦉", "Early Morning Bird 🌅", "Afternoon Chiller 🛋️", "Depends on the weekend 🎉"],
            'correct_index': 0
        },
        {
            'question': "Do I like cats or dogs?",
            'options': ["Dogs all the way! 🐶", "Cats are my spirit animal! 🐱", "Love both equally! 🐾", "Neither / Prefer other pets 🦜"],
            'correct_index': 1
        },
        {
            'question': "Am I an introvert or extrovert?",
            'options': ["Proud Introvert (Homebody) 🛋️", "Total Extrovert (Social Butterfly) 🦋", "Ambivert (Depends on who I'm with) ☯️", "Extrovert online, Introvert IRL 📱"],
            'correct_index': 2
        },
        {
            'question': "What is my favourite social media app?",
            'options': ["Instagram (Reels & DMs) 📸", "TikTok / YouTube Shorts 🎬", "Snapchat (Streaks) 👻", "Twitter / X or Pinterest 💬"],
            'correct_index': 0
        },
        {
            'question': "What is my favourite movie genre or comfort watch?",
            'options': ["Laugh-out-loud Comedy 😂", "Rom-Com / Feel Good 🍿", "Mind-bending Sci-Fi / Mystery 🕵️", "Horror / Thriller 👻"],
            'correct_index': 1
        },
        {
            'question': "What is my favourite colour aesthetic?",
            'options': ["Black / Dark Aesthetic 🖤", "Pastel Pink / Lavender 🌸", "Sky Blue / Ocean 🌊", "Forest Green / Sage 🌿"],
            'correct_index': 1
        }
    ],
    'friends': [
        {
            'question': "What is my morning routine vibe?",
            'options': ["Hit snooze 5 times 😴", "Ready and productive by 7 AM 🏃", "Need 2 cups of coffee before speaking ☕", "Running out the door in panic 🏃‍♂️"],
            'correct_index': 0
        },
        {
            'question': "What type of music is on repeat in my headphones?",
            'options': ["Pop / Chart Hits 🎵", "Hip-hop & R&B 🎧", "Indie / Alternative Rock 🎸", "EDM / House Beats ⚡"],
            'correct_index': 1
        },
        {
            'question': "How do I react in an awkward situation?",
            'options': ["Laugh uncontrollably 😂", "Pretend to look at my phone 📱", "Make an even more awkward joke 🤡", "Disappear completely 👻"],
            'correct_index': 0
        },
        {
            'question': "What's my signature drink when we go out?",
            'options': ["Iced Caramel Latte 🧋", "Refreshing Boba Tea 🥤", "Fizzy Soda / Energy Drink ⚡", "Just pure iced water 💧"],
            'correct_index': 0
        },
        {
            'question': "If our friendship was a movie genre, what would it be?",
            'options': ["A chaotic comedy 😂", "An epic adventure quest 🗺️", "A dramatic mystery series 🕵️", "A wholesome feel-good movie 🍿"],
            'correct_index': 0
        }
    ],
    'couple': [
        {
            'question': "Where would our ideal date night be?",
            'options': ["Candlelit dinner at a cute restaurant 🕯️", "Cozy movie night with takeout & blankets 🍕", "Stargazing on a quiet rooftop 🌌", "Fun arcade or amusement park 🎡"],
            'correct_index': 1
        },
        {
            'question': "What is my love language?",
            'options': ["Quality Time together 💕", "Words of Affirmation & sweet texts 💌", "Physical Touch & warm hugs 🤗", "Acts of Service & caring surprises 🎁"],
            'correct_index': 0
        },
        {
            'question': "Who usually apologizes first after a silly disagreement?",
            'options': ["Me (I can't stay mad!) 🥺", "You (You're the sweeter one!) 🥰", "We both laugh it off together 😂", "Whoever gets hungry first 🍕"],
            'correct_index': 2
        },
        {
            'question': "What's my favourite thing we do together?",
            'options': ["Late night deep talks 🌙", "Trying new restaurants & street food 🍜", "Road trips with loud singing 🚗", "Lazy Sunday cuddles 🛋️"],
            'correct_index': 0
        },
        {
            'question': "What little habit of mine do you notice most?",
            'options': ["Singing or humming randomly 🎤", "Stealing your hoodies / clothes 🧥", "Forgetting where my keys/phone are 🔍", "Always wanting a sweet dessert 🍰"],
            'correct_index': 2
        }
    ],
    'crush': [
        {
            'question': "What was your very first impression of me?",
            'options': ["Super cute & attractive 😍", "Mysterious & intriguing 🤔", "Hilarious and fun to talk to 😂", "A little shy at first 🙈"],
            'correct_index': 0
        },
        {
            'question': "What do you think is my best feature?",
            'options': ["My smile & laugh 😊", "My eyes 👀", "My sense of humor & wit 🌟", "My style and aesthetic 👗"],
            'correct_index': 0
        },
        {
            'question': "If we hung out just the two of us, what would we do?",
            'options': ["Get iced coffee and walk around ☕", "Go to a fun arcade / bowling 🎳", "Cook or bake something yummy together 🧁", "Watch a movie and chat 🎬"],
            'correct_index': 0
        },
        {
            'question': "Do you believe in love at first sight or should I walk by again?",
            'options': ["Definitely love at first sight! 💘", "Walk by again, let me check! 😉", "Slow burn romance is the best 🕯️", "Time will tell! ✨"],
            'correct_index': 1
        },
        {
            'question': "What emoji best describes our chemistry?",
            'options': ["🔥 Pure Fire", "✨ Magical Sparks", "🥰 Heart Eyes", "🤪 Playful Chaos"],
            'correct_index': 1
        }
    ],
    'family': [
        {
            'question': "Who am I most like in the family?",
            'options': ["Mom / Maternal side 👩", "Dad / Paternal side 👨", "My own unique rebel self 🕶️", "A wild mix of everyone 🌀"],
            'correct_index': 2
        },
        {
            'question': "What chore do I dread doing the most?",
            'options': ["Washing dishes 🍽️", "Cleaning / folding laundry 🧺", "Taking out the trash 🗑️", "Waking up early for chores ⏰"],
            'correct_index': 0
        },
        {
            'question': "What is my comfort food when I'm home?",
            'options': ["Mom's / Dad's homemade cooking 🍲", "Warm soup or noodles 🥣", "Pizza delivery 🍕", "Anything sweet in the pantry 🍫"],
            'correct_index': 0
        },
        {
            'question': "What childhood memory do we always laugh about?",
            'options': ["A chaotic holiday road trip 🚗", "A hilarious kitchen disaster 🍳", "A funny secret we kept from parents 🤫", "An embarrassing childhood photo 📸"],
            'correct_index': 0
        },
        {
            'question': "What's my biggest strength in our family?",
            'options': ["Always bringing joy & laughs 😂", "Being the calm voice of reason 🧘", "The most caring & helpful heart 💖", "The tech support for everyone 💻"],
            'correct_index': 0
        }
    ],
    'custom': [
        {
            'question': "What's the one thing I cannot live without?",
            'options': ["My smartphone & music 📱", "My morning coffee / tea ☕", "My best friends / partner 💕", "Good food & snacks 🍕"],
            'correct_index': 0
        },
        {
            'question': "If I had a superpower, which one would I pick?",
            'options': ["Invisibility 👻", "Time Travel ⏳", "Teleportation anywhere ✈️", "Reading minds 🧠"],
            'correct_index': 2
        },
        {
            'question': "What is my favorite season of the year?",
            'options': ["Sunny Summer ☀️", "Cozy Autumn / Fall 🍂", "Magical Winter ❄️", "Blossoming Spring 🌸"],
            'correct_index': 1
        },
        {
            'question': "Are you team Early Bird or Night Owl for me?",
            'options': ["Ultimate Night Owl 🦉", "Early Morning Bird 🌅", "Permasleep Bear 🐻", "Depends on the weekend 🎉"],
            'correct_index': 0
        },
        {
            'question': "What's the best way to cheer me up when I'm stressed?",
            'options': ["Buy me food / Boba 🧋", "Give me space and quiet 🤫", "Send funny memes & videos 🐱", "A long warm hug & listening 🤗"],
            'correct_index': 0
        }
    ]
}

def create_quiz_with_questions(
    creator_name: str,
    title: str,
    description: str,
    category: str,
    theme: str,
    avatar: str,
    questions_data: List[Dict[str, Any]]
) -> Tuple[Quiz, str]:
    """
    Validates input, creates a Quiz with its Questions and Options in one transaction,
    hashes the creator token, and returns (quiz, raw_creator_token).
    """
    creator_name = (creator_name or '').strip()
    title = (title or '').strip()
    description = (description or '').strip()
    category = category if category in QUESTION_TEMPLATES else 'best_friend'
    theme = theme or 'purple_bliss'
    avatar = avatar or 'sparkles'

    if not creator_name or len(creator_name) > 100:
        raise ValueError("Creator nickname must be between 1 and 100 characters.")
    if not title or len(title) > 150:
        raise ValueError("Quiz title must be between 1 and 150 characters.")
    if not questions_data or len(questions_data) < 3:
        raise ValueError("Quiz must have at least 3 questions.")
    if len(questions_data) > 30:
        raise ValueError("Quiz can have at most 30 questions.")

    public_id = generate_public_id()
    creator_token = generate_creator_token()

    quiz = Quiz(
        public_id=public_id,
        creator_name=creator_name,
        title=title,
        description=description,
        category=category,
        theme=theme,
        avatar=avatar,
        is_active=True
    )
    quiz.set_creator_token(creator_token)
    db.session.add(quiz)

    for idx, q_item in enumerate(questions_data, start=1):
        q_text = (q_item.get('question_text') or q_item.get('question') or '').strip()
        if not q_text:
            raise ValueError(f"Question #{idx} cannot be blank.")
        
        question = Question(
            question_text=q_text,
            position=idx
        )
        quiz.questions.append(question)

        raw_options = q_item.get('options') or []
        if len(raw_options) < 2 or len(raw_options) > 4:
            raise ValueError(f"Question #{idx} must have between 2 and 4 options.")

        correct_idx = q_item.get('correct_index')
        has_correct = False
        created_options = []

        for opt_idx, opt_data in enumerate(raw_options):
            if isinstance(opt_data, dict):
                opt_text = (opt_data.get('option_text') or opt_data.get('text') or '').strip()
                is_corr = bool(opt_data.get('is_correct', False))
            else:
                opt_text = str(opt_data).strip()
                is_corr = (opt_idx == correct_idx)

            if not opt_text:
                raise ValueError(f"Question #{idx} has an empty option.")

            if is_corr:
                has_correct = True

            option = Option(
                option_text=opt_text,
                is_correct=is_corr
            )
            question.options.append(option)
            created_options.append(option)

        if not has_correct and created_options:
            created_options[0].is_correct = True

    db.session.commit()
    return quiz, creator_token


def get_leaderboard_data(quiz: Quiz) -> List[Dict[str, Any]]:
    """
    Returns ranked leaderboard for a quiz.
    Sorted by score DESC, then created_at ASC (earliest completion wins ties).
    """
    attempts = Attempt.query.filter_by(quiz_id=quiz.id, is_completed=True)\
        .order_by(Attempt.score.desc(), Attempt.created_at.asc())\
        .all()

    leaderboard = []
    for rank, att in enumerate(attempts, start=1):
        leaderboard.append({
            'rank': rank,
            'id': att.id,
            'participant_name': att.participant_name,
            'score': att.score,
            'total_questions': att.total_questions,
            'percentage': round(att.percentage, 1),
            'completed_at': att.created_at.strftime("%b %d, %Y • %I:%M %p"),
            'trophy': '🥇' if rank == 1 else ('🥈' if rank == 2 else ('🥉' if rank == 3 else None))
        })
    return leaderboard


def get_creator_dashboard_stats(quiz: Quiz) -> Dict[str, Any]:
    """Calculates statistics for the creator dashboard."""
    completed_attempts = Attempt.query.filter_by(quiz_id=quiz.id, is_completed=True).all()
    total_participants = len(completed_attempts)

    if total_participants > 0:
        scores = [a.score for a in completed_attempts]
        percentages = [a.percentage for a in completed_attempts]
        avg_score = round(sum(scores) / total_participants, 1)
        avg_percentage = round(sum(percentages) / total_participants, 1)
        highest_score = max(scores)
        highest_percentage = round(max(percentages), 1)
    else:
        avg_score = 0
        avg_percentage = 0.0
        highest_score = 0
        highest_percentage = 0.0

    return {
        'total_participants': total_participants,
        'average_score': avg_score,
        'average_percentage': avg_percentage,
        'highest_score': highest_score,
        'highest_percentage': highest_percentage,
        'completion_count': total_participants
    }
