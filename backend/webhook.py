from omnidimension import Client
from dotenv import load_dotenv
import os

load_dotenv()

OMNIDIM_API_KEY = os.getenv("OMNIDIM_API_KEY")

# Initialize client
client = Client(OMNIDIM_API_KEY)

# Create an agent
response = client.agent.create(
    name="Misha",
    welcome_message="""Hey there! I'm Misha, your friendly onboarding buddy from MatchMyVibe. Can we chat for a sec to get to know each other better?""",
    context_breakdown=[
                {"title": "Introduction and Purpose Statement", "body": """ Hi! I'm Misha, your Gen-Z friendly onboarding assistant at MatchMyVibe. I'll be asking you a few quick questions to help find you the perfect roommate and living space. Let's dive in, shall we? """ , 
                "is_enabled" : True},
                {"title": "Understanding Daily Rhythms", "body": """ When do you feel most productive – early in the morning or late at night? Your answer will help us understand your daily rhythm. Feel free to use words like 'sunrise' or 'after dark'. """ , 
                "is_enabled" : True},
                {"title": "Lifestyle Preferences", "body": """ How do you prefer to spend your weekends? Are you all about the party life, or do you enjoy a chill weekend binge-watching your favorite shows? This helps us capture your lifestyle preference. """ , 
                "is_enabled" : True},
                {"title": "Study or Work Setup", "body": """ What does your ideal study or work setup look like? Do you thrive in a quiet library setting, or do you prefer the buzz of a group discussion? We're capturing your study habits here. """ , 
                "is_enabled" : True},
                {"title": "Room Environment Preferences", "body": """ Can you describe your ideal room environment? Whether you prefer a cozy nook with fairy lights or a clean minimalist space, your vibe will help us suggest the best match. """ , 
                "is_enabled" : True},
                {"title": "Conflict Resolution Style", "body": """ How do you usually handle conflicts or disagreements? Are you someone who talks things out directly, or do you prefer to avoid confrontation? This insight helps us understand your conflict style. """ , 
                "is_enabled" : True},
                {"title": "Gathering and Wrap-Up", "body": """ Thanks for sharing all that with me! I'll crunch the data to find the roommate who matches your vibe! """ , 
                "is_enabled" : True},
                {"title": "Speech Style and Delivery", "body": """ As a bestie-type voice assistant, be warm, casual, a little playful, and professional. - Use informal GenZ language like 'hey' and 'let's dive in'. - Keep the conversation flowing with short and snappy questions. - Speak in a cheerful tone, conveying enthusiasm and genuine interest. - Add small affirming words like 'awesome' or 'cool' to encourage engagement. """ , 
                "is_enabled" : True}
    ],
    call_type="Outgoing",
    transcriber={
        "provider": "deepgram_stream",
        "silence_timeout_ms": 400,
        "model": "nova-3",
        "numerals": True,
        "punctuate": True,
        "smart_format": True,
        "diarize": False
    },
    model={
        "model": "gemini-2.5-flash",
        "temperature": 0.7
    },
    voice={
        "provider": "eleven_labs",
        "voice_id": "brHdTxI2cvSTiRe1fQlH"
    },
    post_call_actions={

        "webhook": {
            "enabled": True,
            "url": "https://avoid-80p2.onrender.com/receive_traits",
            "include": ["extracted_variables"],
            "extracted_variables": [
            {"key": "daily_rhythm", "prompt": "Classify and extract the trait from keywords like 'morning' or 'night' related to productivity."},
            {"key": "lifestyle", "prompt": "Classify and extract the trait based on weekend preferences using keywords like 'social' or 'chill'."},
            {"key": "study_habits", "prompt": "Classify and extract the trait regarding study setup preferences using keywords like 'quiet' or 'collab'."},
            {"key": "room_vibe", "prompt": "Classify and extract the trait based on room environment preferences using keywords like 'minimal', 'cozy', or 'maximal'."},
            {"key": "conflict_style", "prompt": "Classify and extract the trait from conflict handling strategies using keywords like 'direct' or 'avoidant'."},
            ]
        }
    },
)

print(response)