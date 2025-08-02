from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from backend.matcher import rank_rooms_for_user
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

templates = Jinja2Templates(directory="static")
USERS_FILE = "backend/data/users.json"


# ---------- Auth Logic ----------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def signup_user(email: str, password: str) -> bool:
    users = load_users()
    if email in users:
        return False
    hashed = hash_password(password)
    users[email] = {"password": hashed}
    save_users(users)
    return True

def login_user(email: str, password: str) -> bool:
    users = load_users()
    user = users.get(email)
    if not user:
        return False
    return user["password"] == hash_password(password)

# ---------- Current Users ----------

CURRENT_USERS_FILE = "backend/data/current_users.json"

def load_current_users():
    if not os.path.exists(CURRENT_USERS_FILE):
        return []
    with open(CURRENT_USERS_FILE, "r") as f:
        return json.load(f)

def save_current_users(users):
    with open(CURRENT_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ---------- Routes ----------

@app.get("/")
def home(request: Request):
    email = request.session.get("email")
    users = load_users()

    if not email or email not in users:
        return RedirectResponse("/login", status_code=302)

    user = users[email]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "name": user["name"],
        "dob": user["dob"]
    })

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/signup")
def signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    dob: str = Form(...)
):
    users = load_users()

    # Basic regex: must end in @<something>.com
    if not re.match(r"[^@]+@[^@]+\.[cC][oO][mM]$", email):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "signup_error": "Enter a valid email ending with .com"
        })

    if email in users:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "signup_error": "Email already registered"
        })

    users[email] = {
        "name": name,
        "password": hash_password(password),
        "dob": dob,
        "vibe": "",
        "traits": {},
        "room_preferences": {},
        "assigned_room": None
    }

    save_users(users)
    request.session["email"] = email

    return templates.TemplateResponse("index.html", {
        "request": request,
        "email": email,
        "signup_success": "Signup successful!"
    })

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    users = load_users()
    user = users.get(email)

    if not user or user["password"] != hash_password(password):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "login_error": "Invalid email or password"
        })

    request.session["email"] = email

    current_users = load_current_users()
    if email not in current_users:
        current_users.append(email)
        save_current_users(current_users)

    return RedirectResponse("/matching", status_code=302)

@app.get("/logout")
def logout(request: Request):
    email = request.session.get("email")
    request.session.clear()

    current_users = load_current_users()
    if email in current_users:
        current_users.remove(email)
        save_current_users(current_users)

    return RedirectResponse("/login", status_code=302)

@app.get("/receive_traits")
def get_traits(request: Request):
    current_users = load_current_users()
    if not current_users:
        return JSONResponse({"status": "no user currently logged in"}, status_code=400)

    email = current_users[0]
    users = load_users()
    if email not in users:
        return JSONResponse({"status": "user not found"}, status_code=404)

    traits = users[email].get("traits", {})
    return JSONResponse({"traits": traits})

@app.post("/receive_traits")
async def receive_traits(request: Request):
    data = await request.json()
    print("Webhook received:", data)

    extracted = data.get("extracted_variables", [])
    
    current_users = load_current_users()
    if not current_users:
        return JSONResponse({"status": "no user currently logged in"}, status_code=400)

    email = current_users[0]

    users = load_users()
    if email not in users:
        return JSONResponse({"status": "user not found"}, status_code=404)

    # Store extracted traits
    for trait in extracted:
        key = trait["key"]
        value = trait["value"]
        users[email]["traits"][key] = value

    save_users(users)

    return JSONResponse({"status": "traits saved successfully"})

@app.get("/ranked-matches")
async def get_ranked_matches(request: Request):
    session = request.session
    user_email = session.get("email")

    if not user_email:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    # Load user data
    with open("backend/data/users.json", "r") as f:
        users = json.load(f)
    user_data = users.get(user_email)

    if not user_data:
        return JSONResponse({"error": "User not found"}, status_code=404)

    # Load room data
    with open("backend/data/rooms.json", "r") as f:
        rooms_data = json.load(f)

    # Rank rooms
    ranked_matches = rank_rooms_for_user(user_data, rooms_data)

    return JSONResponse({"matches": ranked_matches})

@app.post("/swipe")
async def handle_swipe(
    request: Request,
    target: str = Form(...),  # persona ID or user email
    direction: str = Form(...)  # "right" or "left"
):
    session = request.session
    email = session.get("email")

    if not email:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    swipes_file = "backend/data/swipes.json"
    if os.path.exists(swipes_file):
        with open(swipes_file, "r") as f:
            swipes = json.load(f)
    else:
        swipes = {}

    if email not in swipes:
        swipes[email] = {"liked": [], "disliked": []}

    if direction == "right" and target not in swipes[email]["liked"]:
        swipes[email]["liked"].append(target)
    elif direction == "left" and target not in swipes[email]["disliked"]:
        swipes[email]["disliked"].append(target)


    with open(swipes_file, "w") as f:
        json.dump(swipes, f, indent=2)

    return JSONResponse({"status": "swipe recorded"})

@app.get("/get_personas")
def get_personas():
    with open("backend/data/personas.json", "r") as f:
        personas = json.load(f)
    
    personas = json.load(f)
    personas_with_ids = []
    for i, persona in enumerate(personas):
        p = persona.copy()
        if "id" not in p:
            p["id"] = f"persona_{i}"
        personas_with_ids.append(p)
    return JSONResponse(personas_with_ids)

