"""
agents/resume_parser.py
Extracts structured info from PDF resume using FREE Groq AI.
"""

import json

try:
    import pdfplumber
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


def extract_text_from_pdf(pdf_path: str) -> str:
    if not HAS_PDF:
        raise ImportError("Run: pip install pdfplumber")
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text.strip()


def parse_resume(pdf_path: str, api_key: str = None) -> dict:
    import os
    key = api_key or os.getenv("GROQ_API_KEY", "")

    try:
        resume_text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        print(f"   ⚠️  Could not read PDF ({e}), using profile data")
        return _your_resume()

    if not resume_text:
        print(f"   ⚠️  PDF is empty, using profile data")
        return _your_resume()

    try:
        from groq import Groq
        client = Groq(api_key=key)

        prompt = f"""Extract info from this resume. Return ONLY valid JSON, no markdown, no extra text.

{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+91-XXXXXXXXXX",
  "location": "City, State",
  "skills": ["Python", "Django"],
  "experience_years": 0,
  "job_titles": ["Software Engineer"],
  "education": "B.Tech CS, XYZ University",
  "summary": "2-3 sentence professional summary",
  "companies": []
}}

Resume:
{resume_text[:3000]}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=800
        )
        raw = response.choices[0].message.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.split("```")[0]
        result = json.loads(raw.strip())
        print(f"   ✅ AI parsed resume successfully")
        return result

    except Exception as e:
        print(f"   ⚠️  Groq parsing failed ({e}), using profile data")
        return _your_resume()


def _your_resume() -> dict:
    """Harshavardhan's real resume data — used as fallback."""
    return {
        "name": "Veguru Harshavardhan",
        "email": "harshavardhan.veguru2103@gmail.com",
        "phone": "6309663013",
        "location": "Tirupati, Andhra Pradesh, India",
        "skills": [
            "Python", "C", "C++", "Java", "HTML", "CSS", "R",
            "NumPy", "Pandas", "Scikit-learn", "Matplotlib", "Seaborn",
            "TensorFlow", "PyTorch", "HuggingFace", "FastAPI",
            "Git", "Docker", "AWS", "Linux", "Jenkins",
            "MySQL", "Machine Learning", "Deep Learning",
            "Computer Vision", "NLP", "Data Science",
            "Power BI", "Streamlit", "OpenCV"
        ],
        "experience_years": 0,
        "job_titles": [
            "Software Developer", "ML Engineer",
            "Data Science Intern", "AI Engineer"
        ],
        "education": "B.Tech Computer Science, IIIT Kottayam, 2026 (CGPA: 7.19)",
        "summary": (
            "Final year B.Tech CS student at IIIT Kottayam specializing in "
            "Machine Learning, Computer Vision, and NLP. Built AI-powered "
            "projects using PyTorch, HuggingFace, and FastAPI. "
            "Passionate about AI/ML and data-driven solutions."
        ),
        "companies": [],
        "projects": [
            "Identify Me — AI multimodal vision chatbot (PyTorch, HuggingFace, FastAPI)",
            "PolitiFact Fake News Detection — BERT, ResNet-50, BLIP (84% accuracy)",
            "Job Market Intelligence Dashboard — Python, Pandas, Streamlit, NLP"
        ]
    }
