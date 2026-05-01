# 🤖 Auto Job Applier Agent — FREE Edition

Applies to jobs on Naukri, Indeed, LinkedIn using **100% FREE** Google Gemini AI.

## ⚡ Setup (5 minutes)

### 1. Get FREE GROQ API Key
- Go to: https://console.groq.com/keys
- Click "Get API Key" → Create → Copy it (starts with `AIza...`)
- No credit card needed!

### 2. Install packages
```powershell
pip install google-generativeai playwright pdfplumber
python -m playwright install chromium
```

### 3. Set your API key (PowerShell)
```powershell
# Temporary (current session)
$env:GEMINI_API_KEY = "AIza-your-key-here"

# Permanent (recommended)
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "AIza-your-key-here", "User")
```

### 4. Edit config.py
```python
GEMINI_API_KEY = "AIza-your-key-here"   # or use env variable
JOB_TITLE      = "Python Developer"
LOCATION       = "Hyderabad"
MIN_MATCH_SCORE = 70
PLATFORMS      = ["naukri", "indeed"]
```

### 5. Add your resume
```
data/resume.pdf   ← put your resume here
```

### 6. Run!
```powershell
# Test first (no real applications submitted)
python main.py --dry-run

# Real run
python main.py

# With interview prep
python main.py --interview-prep

# View dashboard
python dashboard.py
# Open http://localhost:8080
```

