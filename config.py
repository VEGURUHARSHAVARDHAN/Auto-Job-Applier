"""
config.py — All settings for Auto Job Applier Agent
Edit this file before running!
"""

import os
from dataclasses import dataclass, field
from typing import List

@dataclass
class Config:
    # ── Groq API Key (FREE) ───────────────────────────────
    # Get free key at: https://console.groq.com
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "user_API_Key")

    # ── Your Resume ───────────────────────────────────────
    RESUME_PATH: str = "data/resume.pdf"

    # ── Job Search Settings ───────────────────────────────
    JOB_TITLE: str = "Machine Learning Engineer"   # Best match for your profile
    LOCATION: str = "Hyderabad"
    MIN_MATCH_SCORE: int = 60                      # Lower = more jobs matched

    # ── Which platforms to scrape ─────────────────────────
    PLATFORMS: List[str] = field(default_factory=lambda: ["linkedin"])
    LINKEDIN_EMAIL: str = "harshavardhan.veguru2103@gmail.com"
    LINKEDIN_PASSWORD: str = "your-linkedin-password"
    # Options: "naukri", "indeed", "linkedin"

    # ── LinkedIn Credentials (optional) ──────────────────
    LINKEDIN_EMAIL: str = os.getenv("LINKEDIN_EMAIL", "")
    LINKEDIN_PASSWORD: str = os.getenv("LINKEDIN_PASSWORD", "")

    # ── Email Settings (for follow-up emails) ────────────
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "harshavardhan.veguru2103@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    # ── Database ──────────────────────────────────────────
    DB_PATH: str = "data/tracker.db"

    # ── Browser settings ─────────────────────────────────
    HEADLESS: bool = True       # Set False to watch the browser
    SLOW_MO: int = 500
