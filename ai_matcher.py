"""
agents/ai_matcher.py
Uses FREE Groq AI to score job match and write cover letter.
Get free API key at: https://console.groq.com
"""

import json

def _call_groq(api_key: str, prompt: str) -> str:
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()


def match_and_tailor(resume: dict, job: dict, api_key: str) -> dict:
    try:
        prompt = f"""You are an expert career coach. Analyze resume vs job and return ONLY valid JSON, no markdown, no extra text.

RESUME:
Name: {resume.get('name', '')}
Skills: {', '.join(resume.get('skills', []))}
Experience: {resume.get('experience_years', 0)} years
Titles: {', '.join(resume.get('job_titles', []))}
Summary: {resume.get('summary', '')}

JOB:
Title: {job.get('title', '')}
Company: {job.get('company', '')}
Description: {job.get('description', '')[:800]}

Return ONLY this JSON with no extra text:
{{
  "match_score": <integer 0-100>,
  "should_apply": <true or false>,
  "key_matches": ["skill1", "skill2"],
  "missing_skills": ["skill3"],
  "tailored_summary": "<2-sentence resume summary for this job>",
  "cover_letter": "<3-paragraph professional cover letter>"
}}"""

        raw = _call_groq(api_key, prompt)
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.split("```")[0]
        return json.loads(raw.strip())

    except Exception as e:
        print(f" (fallback: {e})", end="")
        return _keyword_match(resume, job)


def _keyword_match(resume: dict, job: dict) -> dict:
    resume_text = " ".join([
        " ".join(resume.get("skills", [])),
        " ".join(resume.get("job_titles", [])),
        resume.get("summary", "")
    ]).lower()
    job_text = (job.get("description", "") + " " + job.get("title", "")).lower()
    stop = {"the","a","an","and","or","in","at","for","to","of","with","is","are","we","our","you"}
    r = set(resume_text.split()) - stop
    j = set(job_text.split()) - stop
    overlap = r & j
    score = min(100, int(len(overlap) / max(len(j), 1) * 200))
    return {
        "match_score": score,
        "should_apply": score >= 60,
        "key_matches": list(overlap)[:5],
        "missing_skills": [],
        "tailored_summary": resume.get("summary", "Experienced professional."),
        "cover_letter": f"Dear Hiring Manager,\n\nI am interested in the {job.get('title','')} role at {job.get('company','')}.\n\nSincerely,\n{resume.get('name','')}"
    }
