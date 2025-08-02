from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from backend.matcher import match_user_to_rooms, rank_rooms_for_user, compute_compatibility, calculate_life_path_number, numerology_score
import json
import os
from dotenv import load_dotenv
import hashlib
import re
from datetime import datetime

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

templates = Jinja2Templates(directory="templates")
USERS_FILE = "backend/data/users.json"
PERSONAS_FILE = "backend/data/personas.json"
ROOMS_FILE = "backend/data/rooms.json"
SWIPES_FILE = "backend/data/swipes.json"
CURRENT_USER_FILE = "backend/data/current_user.json"
# --- UPDATE: New file to store confirmed matches ---
MATCHES_FILE = "backend/data/matches.json"
# --- END UPDATE ---


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_json_file(filepath: str):
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        if 'users.json' in filepath or 'swipes.json' in filepath or 'matches.json' in filepath:
            return {}
        else:
            return []
    with open(filepath, "r") as f:
        return json.load(f)

def save_json_file(filepath: str, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# --- Routes ---

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), dob: str = Form(...)):
    users = load_json_file(USERS_FILE)
    if email in users:
        return templates.TemplateResponse("login.html", {"request": request, "signup_error": "Email already registered"})
    users[email] = {"name": name, "password": hash_password(password), "dob": dob, "vibe": "", "traits": {}, "room_preferences": {}, "assigned_room": None}
    save_json_file(USERS_FILE, users)
    request.session["email"] = email
    return RedirectResponse("/traits", status_code=302)

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    users = load_json_file(USERS_FILE)
    user = users.get(email)
    if not user or user["password"] != hash_password(password):
        return templates.TemplateResponse("login.html", {"request": request, "login_error": "Invalid email or password"})
    request.session["email"] = email
    save_json_file(CURRENT_USER_FILE, [email])
    return RedirectResponse("/matching", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    save_json_file(CURRENT_USER_FILE, [])
    return RedirectResponse("/", status_code=302)

@app.get("/traits")
def traits_page(request: Request):
    if not request.session.get("email"): return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("traits.html", {"request": request})

@app.get("/matching")
def matching_page(request: Request):
    if not request.session.get("email"): return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("matching.html", {"request": request})

# --- API Routes ---

@app.get("/ranked-matches")
async def get_ranked_matches(request: Request):
    user_email = request.session.get("email")
    if not user_email: return JSONResponse({"error": "Not logged in"}, status_code=401)

    users = load_json_file(USERS_FILE)
    current_user_data = users.get(user_email)
    if not current_user_data: return JSONResponse({"error": "User not found"}, status_code=404)

    # --- UPDATE: The pool of potential matches is now other people (users and personas) ---
    potential_matches = []
    personas = load_json_file(PERSONAS_FILE)
    for i, p in enumerate(personas):
        if "id" not in p: p["id"] = f"persona_{i}"
        potential_matches.append(p)
    
    for email, user_data in users.items():
        if email != user_email:
            user_data_copy = user_data.copy()
            user_data_copy["id"] = email # Use email as the unique ID for real users
            potential_matches.append(user_data_copy)
    # --- END UPDATE ---

    swipes = load_json_file(SWIPES_FILE)
    user_swipes = swipes.get(user_email, {})
    seen_profiles = user_swipes.get("liked", []) + user_swipes.get("disliked", [])
    
    scored_profiles = []
    user_life_path = calculate_life_path_number(current_user_data.get("dob", ""))

    for profile in potential_matches:
        if profile["id"] in seen_profiles:
            continue

        trait_score = compute_compatibility(current_user_data.get("traits", {}), profile.get("traits", {}))
        profile_life_path = calculate_life_path_number(profile.get("dob", ""))
        numerology_score_val = numerology_score(user_life_path, profile_life_path) * 2
        final_score = (0.8 * trait_score) + (0.2 * numerology_score_val)
        
        profile_with_score = profile.copy()
        profile_with_score["score"] = round(final_score * 10, 2)
        scored_profiles.append(profile_with_score)

    scored_profiles.sort(key=lambda x: x["score"], reverse=True)
    return JSONResponse(scored_profiles)

@app.post("/swipe")
async def handle_swipe(request: Request):
    user_email = request.session.get("email")
    if not user_email: return JSONResponse({"error": "Not logged in"}, status_code=401)

    data = await request.json()
    target_id = data.get("target")
    direction = data.get("direction")

    swipes = load_json_file(SWIPES_FILE)
    if user_email not in swipes: swipes[user_email] = {"liked": [], "disliked": []}

    if direction == "right" and target_id not in swipes[user_email]["liked"]:
        swipes[user_email]["liked"].append(target_id)
    elif direction == "left" and target_id not in swipes[user_email]["disliked"]:
        swipes[user_email]["disliked"].append(target_id)
    save_json_file(SWIPES_FILE, swipes)
    
    # --- UPDATE: Check for a mutual match if the user swiped right ---
    if direction == "right":
        # Check if the other person has liked the current user
        target_swipes = swipes.get(target_id, {})
        if user_email in target_swipes.get("liked", []):
            # IT'S A MUTUAL MATCH!
            users = load_json_file(USERS_FILE)
            rooms = load_json_file(ROOMS_FILE)
            
            user1_data = users[user_email]
            user2_data = users.get(target_id) # This could be a real user
            
            # If the target is a persona, we can't allocate a room with them
            if not user2_data:
                 return JSONResponse({"status": "swipe recorded", "match": False})

            # Find the best room for the matched pair
            best_room_id, score = match_user_to_rooms(user1_data, rooms)

            if best_room_id:
                # Update user records with the assigned room
                users[user_email]["assigned_room"] = best_room_id
                users[target_id]["assigned_room"] = best_room_id
                save_json_file(USERS_FILE, users)
                
                # Store the match
                matches = load_json_file(MATCHES_FILE)
                match_key = tuple(sorted((user_email, target_id)))
                matches[str(match_key)] = {"room": best_room_id, "score": score}
                save_json_file(MATCHES_FILE, matches)

                return JSONResponse({"status": "swipe recorded", "match": True, "room": best_room_id})

    return JSONResponse({"status": "swipe recorded", "match": False})
    # --- END UPDATE ---

@app.post("/receive_traits")
async def receive_traits(request: Request):
    data = await request.json()
    extracted = data.get("extracted_variables", [])
    current_users = load_json_file(CURRENT_USER_FILE)
    if not current_users: return JSONResponse({"status": "no user currently logged in"}, status_code=400)
    email = current_users[0]
    users = load_json_file(USERS_FILE)
    if email not in users: return JSONResponse({"status": "user not found"}, status_code=404)
    for trait in extracted:
        users[email]["traits"][trait["key"]] = trait["value"]
    save_json_file(USERS_FILE, users)
    return JSONResponse({"status": "traits saved successfully"})