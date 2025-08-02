from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from backend.matcher import compute_compatibility, calculate_life_path_number, numerology_score
import json
import os
from dotenv import load_dotenv
import hashlib
import re
from datetime import datetime

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Point Jinja2 to the 'templates' directory
templates = Jinja2Templates(directory="templates")
USERS_FILE = "backend/data/users.json"
PERSONAS_FILE = "backend/data/personas.json"
ROOMS_FILE = "backend/data/rooms.json"
SWIPES_FILE = "backend/data/swipes.json"
CURRENT_USER_FILE = "backend/data/current_user.json"

# ---------- Auth & Data Logic ----------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_json_file(filepath: str):
    """Loads a JSON file, returning the correct empty type if it doesn't exist."""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        if 'users.json' in filepath or 'swipes.json' in filepath:
            return {}
        else:
            return []
    with open(filepath, "r") as f:
        return json.load(f)

def save_json_file(filepath: str, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# ---------- Routes ----------

@app.get("/")
def home(request: Request):
    """Serves the main landing page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
def login_page(request: Request):
    """Serves the login/signup page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup")
def signup_page(request: Request):
    """Redirects to the login page, which handles both."""
    return RedirectResponse("/login", status_code=302)

@app.post("/signup")
async def signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    dob: str = Form(...)
):
    users = load_json_file(USERS_FILE)
    if not re.match(r"[^@]+@[^@]+\.[cC][oO][mM]$", email):
        return templates.TemplateResponse("login.html", {"request": request, "signup_error": "Enter a valid email ending with .com"})
    if email in users:
        return templates.TemplateResponse("login.html", {"request": request, "signup_error": "Email already registered"})

    users[email] = {
        "name": name, "password": hash_password(password), "dob": dob,
        "vibe": "", "traits": {}, "room_preferences": {}, "assigned_room": None
    }
    save_json_file(USERS_FILE, users)
    request.session["email"] = email
    
    # After signup, new users go to the traits page to fill out the questionnaire
    return RedirectResponse("/traits", status_code=302)

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    users = load_json_file(USERS_FILE)
    user = users.get(email)
    if not user or user["password"] != hash_password(password):
        return templates.TemplateResponse("login.html", {"request": request, "login_error": "Invalid email or password"})
    
    request.session["email"] = email
    save_json_file(CURRENT_USER_FILE, [email])

    # --- UPDATE: Existing users who log in go directly to the matching/swipe page ---
    return RedirectResponse("/matching", status_code=302)
    # --- END UPDATE ---

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    save_json_file(CURRENT_USER_FILE, [])
    return RedirectResponse("/", status_code=302)

@app.get("/traits")
def traits_page(request: Request):
    """Serves the page for the user to interact with the Omnidimension widget."""
    if not request.session.get("email"):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("traits.html", {"request": request})

@app.get("/matching")
def matching_page(request: Request):
    """Serves the main swipe interface page."""
    if not request.session.get("email"):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("matching.html", {"request": request})

# ---------- API Routes for Frontend Interaction ----------

@app.get("/ranked-matches")
async def get_ranked_matches(request: Request):
    user_email = request.session.get("email")
    if not user_email:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    users = load_json_file(USERS_FILE)
    current_user_data = users.get(user_email)
    if not current_user_data:
        return JSONResponse({"error": "User not found"}, status_code=404)

    potential_matches = load_json_file(PERSONAS_FILE)
    swipes = load_json_file(SWIPES_FILE)
    user_swipes = swipes.get(user_email, {})
    seen_personas = user_swipes.get("liked", []) + user_swipes.get("disliked", [])
    
    scored_personas = []
    user_life_path = calculate_life_path_number(current_user_data.get("dob", ""))

    for i, persona in enumerate(potential_matches):
        if "id" not in persona:
            persona["id"] = f"persona_{i}"
            
        if persona["id"] in seen_personas:
            continue

        trait_score = compute_compatibility(current_user_data.get("traits", {}), persona.get("traits", {}))
        persona_life_path = calculate_life_path_number(persona.get("dob", ""))
        numerology_score_val = numerology_score(user_life_path, persona_life_path) * 2
        final_score = (0.8 * trait_score) + (0.2 * numerology_score_val)
        
        persona_with_score = persona.copy()
        persona_with_score["score"] = round(final_score * 10, 2)
        scored_personas.append(persona_with_score)

    scored_personas.sort(key=lambda x: x["score"], reverse=True)

    return JSONResponse(scored_personas)


@app.post("/swipe")
async def handle_swipe(request: Request):
    user_email = request.session.get("email")
    if not user_email:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    data = await request.json()
    target_id = data.get("target")
    direction = data.get("direction")

    swipes = load_json_file(SWIPES_FILE)
    if user_email not in swipes:
        swipes[user_email] = {"liked": [], "disliked": []}

    if direction == "right" and target_id not in swipes[user_email]["liked"]:
        swipes[user_email]["liked"].append(target_id)
    elif direction == "left" and target_id not in swipes[user_email]["disliked"]:
        swipes[user_email]["disliked"].append(target_id)

    save_json_file(SWIPES_FILE, swipes)
    return JSONResponse({"status": "swipe recorded"})

@app.post("/receive_traits")
async def receive_traits(request: Request):
    data = await request.json()
    print("Webhook received:", data)

    extracted = data.get("extracted_variables", [])
    
    current_users = load_json_file(CURRENT_USER_FILE)
    if not current_users:
        return JSONResponse({"status": "no user currently logged in"}, status_code=400)

    email = current_users[0]

    users = load_json_file(USERS_FILE)
    if email not in users:
        return JSONResponse({"status": "user not found"}, status_code=404)

    for trait in extracted:
        key = trait["key"]
        value = trait["value"]
        users[email]["traits"][key] = value

    save_json_file(USERS_FILE, users)

    return JSONResponse({"status": "traits saved successfully"})