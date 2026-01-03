
````markdown
# Council of Experts 🧠

**Council of Experts** is a FastAPI-based web app that takes a user problem and streams advice from 3 AI-simulated expert personas in real-time. Each expert responds from their unique perspective.

---

## Features
- ✅ Content safety validation for user input
- ✅ Expert selection and persona-based responses
- ✅ Real-time streaming of multiple expert answers
- ✅ Lightweight demo UI at `/ui`
- ✅ Fully async for performance

---

## Tech Stack
- **Backend**: Python, FastAPI, asyncio
- **AI**: Google Gemini via `google-genai`
- **Graph orchestration**: LangGraph
- **Frontend**: Vanilla JS + HTML
- **Other**: Pydantic, CORS, dotenv

---

## Setup

1. **Clone the repo**
```bash
git clone https://github.com/RajaVardhan-coder/Council-of-Experts.git
cd council-of-experts
````

2. **Install dependencies**

```bash
python -m pip install -r requirements.txt
```

3. **Create `.env`**

```bash
cp .env.example .env
# Then add your GEMINI_API_KEY
```

4. **Run the server**

```bash
uvicorn main:app --reload
```

5. **Open the demo UI**
   Visit: [http://localhost:8000/ui](http://localhost:8000/ui)

---

## API Endpoints

* **POST `/advice`**

```json
Request:
{
  "problem": "How can I improve my study habits?"
}

Response: (streaming JSON events)
{
  "type": "delta",
  "expert": "Albert Einstein",
  "content": "..."
}
```

---

## Notes / Warnings

* Currently **CORS allows all origins**; this is only safe for development.
* Validator rejects NSFW, abusive, or malicious inputs.
* Frontend is a simple demo; production use requires enhancements.
* Streaming depends on the Gemini API key.

---
