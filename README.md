# Instagram B2B Outreach Control Hub (Garment & Martial Arts Manufacturing)

A premium, highly secure, and human-like automation dashboard designed for bulk B2B leads contact rotation. Powered by **FastAPI** on the backend and **Tailwind CSS** with Glassmorphism styles on the frontend. The copywriter service hooks natively into the high-speed **Groq API Engine** (Llama-3-8B) to generate context-aware comments and personalized wholesale proposals.

## 🚀 Features
- **Sleek Glassmorphic Dashboard**: Real-time stats visualization, responsive columns, and live tracking lists.
- **Dynamic Groq Copywriter**: Direct interface with Groq API to formulate cold outreach pitches and post-comments based on the leads' exact B2B niches.
- **MongoDB Atlas Integration**: Automated seeding and state preservation of leads and target profiles.
- **SSE Live Activity Logger**: Streaming console output directly from backend automation tasks.
- **B2B Cooldown Engine**: Enforces strict action limits to simulate real organic browser behavior.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.10+
- A running MongoDB Atlas cluster or a local MongoDB community edition server.
- A free **Groq Cloud API Key** from [console.groq.com](https://console.groq.com).

### 2. Configure Environment Variables
Create a file named `.env` in the root workspace directory (`c:\Users\Pakeeza\Desktop\insta\.env`):

```env
MONGODB_URI="mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
DATABASE_NAME="insta_outreach"
GROQ_API_KEY="gsk_xxxxxxYourGroqKeyHerexxxxxx"
```

### 3. Install Dependencies
Open your shell terminal in the project directory and run:

```bash
pip install -r backend/requirements.txt
```

### 4. Fire up the Backend API
Start the FastAPI server via Uvicorn:

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Launch the Dashboard
Simply open **`frontend/index.html`** in any modern web browser or host it on your local dev server. The page is configured to fetch dynamically from your running API!

---

## 🛡️ Safe B2B Outreach Principles
To keep accounts clean, our system supports safe delays:
- **Proxy Rotation**: Custom residential proxy slots are assigned per outreach account.
- **Coordinated Cooldowns**: Safe random waits (ranging from 3 to 7 minutes) are performed between consecutive actions.
- **Strict Limit Enforcement**: Daily limits check automated follows (< 50) and messages (< 40) per profile.
# instagran-auto
