# matcher.py

from datetime import datetime

TRAITS = [
    "daily_rhythm",
    "lifestyle",
    "study_habits",
    "room_vibe",
    "conflict_style"
]

# Acceptable (but not perfect) matches
ACCEPTABLE_MATCHES = {
    "daily_rhythm": {
        "morning": ["night"],
        "night": ["morning"]
    },
    "lifestyle": {
        "social": ["chill"],
        "chill": ["social"]
    },
    "study_habits": {},
    "room_vibe": {
        "cozy": ["minimal"],
        "minimal": ["cozy"]
    },
    "conflict_style": {}
}

# Numerology Chart
numerology_chart = {
    1: {"same": [1, 2, 5], "neutral": [3, 7, 8, 9], "challenges": [4, 6]},
    2: {"same": [1, 2, 4, 6, 8], "neutral": [3, 9], "challenges": [5, 7]},
    3: {"same": [3, 6, 9], "neutral": [1, 2, 5], "challenges": [4, 7, 8]},
    4: {"same": [2, 4, 8], "neutral": [6, 7], "challenges": [1, 3, 5, 9]},
    5: {"same": [1, 5, 7], "neutral": [3, 8, 9], "challenges": [2, 4, 6]},
    6: {"same": [3, 6, 9], "neutral": [2, 4, 8], "challenges": [1, 5, 7]},
    7: {"same": [4, 5, 7], "neutral": [1, 9], "challenges": [2, 3, 6, 8]},
    8: {"same": [2, 4, 8], "neutral": [1, 5, 6], "challenges": [3, 7, 9]},
    9: {"same": [3, 6, 9], "neutral": [1, 2, 5, 7], "challenges": [4, 8]}
}

def calculate_life_path_number(dob: str) -> int:
    """Calculate numerology life path number from DOB (yyyy-mm-dd)."""
    if not dob: return 0
    digits = [int(char) for char in dob if char.isdigit()]
    total = sum(digits)
    
    while total > 9:
        total = sum(int(d) for d in str(total))
    
    return total

def numerology_score(user_number: int, other_number: int) -> float:
    """Returns compatibility score between two life path numbers (out of 5)."""
    if user_number == 0 or other_number == 0: return 1.0 # Return a neutral score if DOB is missing
    
    same = numerology_chart.get(user_number, {}).get("same", [])
    neutral = numerology_chart.get(user_number, {}).get("neutral", [])
    challenges = numerology_chart.get(user_number, {}).get("challenges", [])

    if other_number in same:
        return 5.0
    elif other_number in neutral:
        return 3.0
    elif other_number in challenges:
        return 0.0
    else:
        return 1.0  # Unknown, fallback

def compute_compatibility(traits1, traits2):
    """Simple matching: +2 for full match, +1 for partial (same group), 0 otherwise."""
    if not traits1 or not traits2:
        return 0

    matching_traits = 0
    total_traits = len(traits1)
    if total_traits == 0: return 0

    for key in traits1:
        if key in traits2:
            if traits1[key] == traits2[key]:
                matching_traits += 1

    # Normalize to a score out of 10
    score = (matching_traits / total_traits) * 10
    return score

def compute_logistics_score(user_prefs, room):
    matches = 0
    # UPDATE: Use .get() to avoid errors if a key is missing
    if user_prefs.get("room_type") == room.get("room_type"):
        matches += 1
    if user_prefs.get("floor") == room.get("floor"):
        matches += 1
    if user_prefs.get("has_window") == room.get("has_window"):
        matches += 1
    return (matches / 3) * 10  # Normalize to 10


def match_user_to_rooms(new_user, rooms):
    best_room = None
    best_score = -1

    for room in rooms:
        if len(room.get("occupants", [])) >= room["capacity"]:
            continue

        compatibility_total = 0

        # Roommate compatibility
        if room.get("occupants"):
            for occupant in room["occupants"]:
                compatibility_total += compute_compatibility(new_user["traits"], occupant["traits"])
            compatibility_score = compatibility_total / len(room["occupants"])
        else:
            # No roommate yet, assume neutral compatibility
            compatibility_score = 5

        # Logistics preference score
        logistics_score = compute_logistics_score(new_user["room_preferences"], room)

        # Numerology for new user
        user_life_path = calculate_life_path_number(new_user["dob"])
        numerology_scores = []

        # For each occupant, compare numerology
        for occupant in room["occupants"]:
            if "dob" in occupant:
                occupant_path = calculate_life_path_number(occupant["dob"])
                score = numerology_score(user_life_path, occupant_path)
                numerology_scores.append(score)

        # Average numerology score (0 if no one has DOB)
        numerology_score_value = (
            sum(numerology_scores) / len(numerology_scores)
            if numerology_scores else 0
        )

        # Debug print for individual scores
        print(f"DEBUG | Room {room['room_id']} -> Compatibility Score: {compatibility_score}, Logistics Score: {logistics_score}, Numerology Score: {numerology_score_value}")

        # Weighted hybrid score
        final_score = (0.7 * compatibility_score + 0.2 * logistics_score + 0.1 * numerology_score_value)

        if final_score > best_score:
            best_score = final_score
            best_room = room["room_id"]

    return best_room, f"{round(best_score * 10, 1)}%"

def rank_rooms_for_user(new_user, rooms):
    scored_rooms = []

    user_life_path = calculate_life_path_number(new_user.get("dob", ""))

    for room in rooms:
        if len(room.get("occupants", [])) >= room.get("capacity", 1):
            continue

        # Roommate compatibility
        compatibility_total = 0
        if room.get("occupants"):
            for occupant in room["occupants"]:
                compatibility_total += compute_compatibility(new_user.get("traits", {}), occupant.get("traits", {}))
            compatibility_score = compatibility_total / len(room["occupants"])
        else:
            compatibility_score = 5

        # Logistics score
        # --- THIS IS THE MAIN FIX ---
        # Changed "preferences" to "room_preferences" to match your user data structure in main.py
        logistics_score = compute_logistics_score(new_user.get("room_preferences", {}), room)

        # Numerology score
        numerology_scores = []
        for occupant in room.get("occupants", []):
            if "dob" in occupant:
                occupant_path = calculate_life_path_number(occupant.get("dob", ""))
                score = numerology_score(user_life_path, occupant_path)
                numerology_scores.append(score)
        numerology_score_value = (
            sum(numerology_scores) / len(numerology_scores)
            if numerology_scores else 0
        )

        # Final hybrid score (weighted)
        final_score = (0.7 * compatibility_score +
                       0.2 * logistics_score +
                       0.1 * numerology_score_value)

        # Add all room occupants to the response for the frontend
        room_data_with_occupants = room.copy()
        room_data_with_occupants['occupants_details'] = room.get("occupants", [])


        scored_rooms.append({
            "id": room["room_id"], # Use room_id as the unique identifier
            "name": f"Room {room['room_id']}",
            "vibe": f"{len(room.get('occupants', []))} / {room.get('capacity', 1)} occupants",
            "avatar_color": "#A78BFA", # A default color for rooms
            "room_data": room_data_with_occupants,
            "score": round(final_score * 10, 2)  # Convert to percentage
        })

    # Sort rooms by descending score
    scored_rooms.sort(key=lambda x: x["score"], reverse=True)

    return scored_rooms