# SignalFlow AI - Setup & Installation Guide
**Beginner-Friendly Step-by-Step Instructions**

This guide walks you through setting up SignalFlow AI on Windows PowerShell, macOS, and Linux.

---

## 1. System Requirements

- **Python**: Python 3.10 to 3.14 (Tested on Python 3.14.7 64-bit)
- **RAM**: Minimum 8 GB, recommended 16 GB Physical RAM
- **GPU**: None required. Strands Decider 2B runs locally on CPU using vectorized `float32` instructions.
- **Google AI Studio API Key**: Free tier available from [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## 2. Installation on Windows (PowerShell)

### Step 1: Open PowerShell and Navigate to the Project
```powershell
cd "c:\Users\YourUser\path\to\signalflow-ai"
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If you see an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and re-activate).*

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 3. Installation on macOS / Linux (Bash / Zsh)

### Step 1: Open Terminal and Navigate to the Project
```bash
cd ~/path/to/signalflow-ai
```

### Step 2: Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 4. Configuring Google AI Studio Gemini API

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey) and click **"Create API Key"**.
2. Copy `.env.example` to `.env`:
   - **Windows**: `Copy-Item .env.example .env`
   - **macOS/Linux**: `cp .env.example .env`
3. Open `.env` in any text editor and paste your key:
   ```ini
   GEMINI_API_KEY=AIzaSy...YourKeyHere
   GEMINI_MODEL_ID=gemini-3.5-flash-lite
   MIN_CONFIDENCE_THRESHOLD=0.80
   ```
4. Save `.env`. SignalFlow AI automatically loads this file via `python-dotenv`.

> **Security Reminder:**
> Never commit `.env` to GitHub. The project's `.gitignore` automatically excludes `.env` and `.env.*`.

---

## 5. Running the System

### Option A: Run Automated Unit Tests (Recommended First Step)
Verify all 26 unit tests pass with zero cloud quota usage:
```powershell
pytest tests/ -v
```

### Option B: Run Live Gemini Integration Test
Verify your Google AI Studio API key and catalog access:
```powershell
python test_gemini_live.py gemini-3.5-flash-lite
```

### Option C: Run End-to-End Pipeline Demo
Execute the full terminal pipeline demonstration:
```powershell
python demo.py gemini-3.5-flash-lite
```

### Option D: Launch the Interactive Streamlit Dashboard
Launch the fintech dashboard in your web browser:
```powershell
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 6. Running with Official Strands Decider HTTP Server (Optional)

You can launch the official Strands Decider HTTP server:
```powershell
.\.venv\Scripts\strands-decider.exe serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --device cpu --port 8000
```
SignalFlow AI automatically connects to `http://localhost:8000/ask` when the server is active.
