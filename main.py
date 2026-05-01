"""
Automatic Job Applier Agent - Powered by FREE Groq AI
Run: python main.py --dry-run
"""

import asyncio
import argparse
from agents.resume_parser import parse_resume
from agents.job_scraper import scrape_jobs
from agents.ai_matcher import match_and_tailor
from agents.tracker import init_db, save_application, get_all_applications
from agents.interview_prep import generate_interview_prep
from config import Config


def print_banner():
    print("""
╔══════════════════════════════════════════════════╗
║     🤖  AUTO JOB APPLIER AGENT  v2.0            ║
║       Powered by FREE Groq AI (LLaMA 3)         ║
║     LinkedIn · Naukri · Indeed · Auto-Apply     ║
╚══════════════════════════════════════════════════╝
""")


async def run_pipeline(args):
    print_banner()
    cfg = Config()
    init_db()

    if cfg.GROQ_API_KEY in ("YOUR_GROQ_API_KEY_HERE", ""):
        print("❌ ERROR: Please set your Groq API key in config.py")
        print("   Get a FREE key at: https://console.groq.com")
        return

    # ── Step 1: Parse resume ─────────────────────────────
    print("📄 Step 1: Parsing your resume with Groq AI...")
    resume = parse_resume(cfg.RESUME_PATH, cfg.GROQ_API_KEY)
    print(f"   ✅ Name:       {resume['name']}")
    print(f"   ✅ Skills:     {', '.join(resume['skills'][:6])}")
    print(f"   ✅ Experience: {resume['experience_years']} years")
    print(f"   ✅ Location:   {resume.get('location','')}")

    # ── Step 2: Scrape jobs ──────────────────────────────
    print(f"\n🔍 Step 2: Scraping '{cfg.JOB_TITLE}' jobs in '{cfg.LOCATION}'...")
    jobs = await scrape_jobs(cfg.JOB_TITLE, cfg.LOCATION, cfg.PLATFORMS)
    print(f"   ✅ Found {len(jobs)} job listings")

    if not jobs:
        print("   ⚠️  No jobs found. Try changing JOB_TITLE or LOCATION in config.py")
        return

    # ── Step 3: AI Match ─────────────────────────────────
    print(f"\n🧠 Step 3: AI matching with Groq — threshold: {cfg.MIN_MATCH_SCORE}%...")
    matched = []
    for i, job in enumerate(jobs):
        print(f"   [{i+1}/{len(jobs)}] {job['title']} @ {job['company']}...", end=" ", flush=True)
        result = match_and_tailor(resume, job, cfg.GROQ_API_KEY)
        job.update(result)
        score = result.get("match_score", 0)
        if score >= cfg.MIN_MATCH_SCORE:
            matched.append(job)
            print(f"✅ {score}/100 — MATCH!")
        else:
            print(f"⏭️  {score}/100 — skip")

    print(f"\n   🎯 {len(matched)} jobs matched threshold ({cfg.MIN_MATCH_SCORE}+)")

    # ── Step 4: Apply ────────────────────────────────────
    if args.dry_run:
        print(f"\n🔶 DRY RUN — would apply to {len(matched)} jobs:")
        for job in matched:
            print(f"   → [{job.get('match_score',0)}/100] {job['title']} @ {job['company']} ({job['source']})")
            print(f"     Cover letter preview: {job.get('cover_letter','')[:80]}...")
    else:
        print(f"\n📨 Step 4: Applying to {len(matched)} jobs...")
        from agents.auto_applier import apply_to_job
        applied = 0
        async with apply_to_job(matched, resume) as applier:
            async for job, success in applier:
                icon   = "✅" if success else "❌"
                status = "applied" if success else "failed"
                save_application(job, status)
                print(f"   {icon} {job['title']} @ {job['company']}")
                if success:
                    applied += 1
        print(f"\n   🎉 Applied to {applied}/{len(matched)} jobs!")

    # ── Step 5: Save to tracker ──────────────────────────
    print("\n📊 Step 5: Saving to tracker database...")
    for job in matched:
        save_application(job, "applied" if not args.dry_run else "pending")
    total = len(get_all_applications())
    print(f"   ✅ Total applications tracked: {total}")
    print(f"   📋 View dashboard: python dashboard.py → http://localhost:8080")

    # ── Step 6: Interview prep ───────────────────────────
    if matched and args.interview_prep:
        print(f"\n🎤 Step 6: Interview prep for top match...")
        top  = matched[0]
        prep = generate_interview_prep(top, resume, cfg.GROQ_API_KEY)
        print(f"\n{'─'*60}")
        print(prep)
        print('─'*60)

    print("\n✅ All done!\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Job Applier — Groq Edition")
    parser.add_argument("--dry-run",        action="store_true", help="Preview only, don't submit")
    parser.add_argument("--interview-prep", action="store_true", help="Generate interview prep for top match")
    args = parser.parse_args()
    asyncio.run(run_pipeline(args))
