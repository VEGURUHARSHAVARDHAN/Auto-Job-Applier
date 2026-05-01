"""
agents/interview_prep.py
Generates interview prep using FREE Groq AI.
"""


def generate_interview_prep(job: dict, resume: dict, api_key: str) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": f"""You are an expert interview coach. Create a complete interview prep guide.

CANDIDATE:
Name: {resume.get('name', '')}
Skills: {', '.join(resume.get('skills', []))}
Experience: {resume.get('experience_years', 0)} years
Background: {resume.get('summary', '')}

JOB:
Title: {job.get('title', '')}
Company: {job.get('company', '')}
Description: {job.get('description', '')[:500]}

Generate:
## 🎯 Top 5 Behavioral Questions (with answers)
## 💻 Technical Questions Likely to Be Asked
## ❓ 5 Questions to Ask the Interviewer
## 🏢 Company Research Checklist
## 💰 Salary Negotiation Tips"""}],
            max_tokens=1500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return (f"Interview prep unavailable: {e}\n\n"
                f"Common questions for {job.get('title','this role')}:\n"
                "1. Tell me about yourself\n"
                "2. Why do you want this role?\n"
                "3. Describe a challenging project\n"
                "4. Where do you see yourself in 5 years?\n"
                "5. What are your salary expectations?")


def save_prep_to_file(job: dict, prep: str):
    import os
    os.makedirs("data/interview_prep", exist_ok=True)
    company  = job.get("company", "company").replace(" ", "_")
    title    = job.get("title", "role").replace(" ", "_")
    filename = f"data/interview_prep/{company}_{title}.md"
    with open(filename, "w") as f:
        f.write(f"# Interview Prep: {job.get('title')} @ {job.get('company')}\n\n")
        f.write(prep)
    print(f"   💾 Saved to: {filename}")
    return filename
