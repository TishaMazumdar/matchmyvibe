# 💫 MatchMyVibe: Find Your Perfect Roommate Match

**Built with empathy. Designed for sisterhood. Powered by ethical AI.**

## 👩‍💻 About the Project

**MatchMyVibe** is an inclusive, AI-powered roommate matching platform designed especially for **women in co-living spaces**. It empowers users to make independent and informed choices based on **personality traits, lifestyle preferences, and birthdates** — rather than socio-economic or demographic biases.

This project was built as part of the **SheBuilds Hackathon** to promote **design thinking**, **ethical AI**, and **digital sisterhood**.

---

## 🌟 Key Features

* 🎙️ **Voice-first onboarding**: We use [**Omnidim**](https://www.omnidim.io/) to collect your personality traits through a conversational AI agent named **Misha**.
* 🔢 **Numerology-matched vibes**: We use your **birthdate** to compute a **numerology number**, which helps add a mystical yet thoughtful dimension to the matching logic.
* 🧠 **Personality over prejudice**: Our matchmaking engine focuses only on 5 personality traits, logistics preferences, and date of birth.
* ✨ **Swipe-based UX**: You see your potential roommate matches one-by-one and swipe left/right to express your interest.
* 🪄 **Backend ↔️ Frontend Integration** powered by **GitHub Copilot**, making the system intelligent and seamless.
* 🖥️ **Admin-friendly JSON database** (for MVP): All rooms, users, and preferences are stored in structured `JSON` files.

---

## 🧩 Numerology Matching Logic

We calculate a user's **life path number** from their birthdate (DOB). The compatibility matrix is defined as:

```python
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
```

This influences the final **roommate compatibility score** alongside personality and room preferences. [Numerology source](https://www.mindbodygreen.com/articles/most-romantically-compatible-life-path-numbers-in-numerology?srsltid=AfmBOoqFMbrvQhnUZGZBXMpWVbupNFJ_YRRykfCMcYjOUveTeNo45ww_)

---

## 🔧 Tech Stack

| Layer        | Tools Used                                                         |
| ------------ | ------------------------------------------------------------------ |
| **Frontend** | HTML, CSS, JavaScript                                              |
| **Backend**  | Python, FastAPI, Webhooks, GitHub Copilot                          |
| **AI Layer** | [Omnidim Voice Agent](https://www.omnidim.io/), Gemini (Google AI) |
| **Database** | JSON files for MVP (rooms, users, personas, sessions)              |

---

## 📲 Future Scope

* 📱 **Mobile App Version**: Build a native or cross-platform app for wider adoption.
* 💬 **Icebreaker Chat**: Introduce a “first message” or “vibe test” to break the ice between matches.
* 🔐 **Firebase Integration**: Migrate from JSON to Firebase for secure auth and scalable storage.

---

## 💖 Why This Matters

* **Inclusive & Safe**: Tailored for women and gender-diverse individuals in co-living spaces.
* **Ethical AI**: No race, religion, caste, or economic indicators used in matchmaking.
* **Empathy-Driven Design**: We let users define *how* and *with whom* they want to live.
* **Independent Choice**: The final decision is always with the user — just like swiping right.

---

## 🤝 Team aVoid

This project was designed and developed by **Tisha Mazumdar** and **Megha Yadav** under the team name **aVoid**, as a submission to the **SheBuilds Hackathon** 2025.

---

## 🪷 Closing Note

**MatchMyVibe** is more than just an app — it’s an invitation to live better, together. Thoughtfully built for women, by women.

> *“Because vibes matter.”*