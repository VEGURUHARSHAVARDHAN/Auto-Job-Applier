"""
agents/job_scraper.py
Scrapes job listings from Naukri.com, Indeed.com, and LinkedIn.
Uses Playwright for real browser automation.
"""

import asyncio
import re
from typing import List, Dict
from urllib.parse import quote


async def scrape_jobs(job_title: str, location: str, platforms: List[str]) -> List[Dict]:
    """Scrape jobs from all specified platforms."""
    all_jobs = []

    tasks = []
    if "naukri" in platforms:
        tasks.append(_scrape_naukri(job_title, location))
    if "indeed" in platforms:
        tasks.append(_scrape_indeed(job_title, location))
    if "linkedin" in platforms:
        tasks.append(_scrape_linkedin(job_title, location))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)
        elif isinstance(result, Exception):
            print(f"   ⚠️  Scraper error: {result}")

    # Deduplicate by title+company
    seen = set()
    unique = []
    for job in all_jobs:
        key = f"{job['title'].lower()}_{job['company'].lower()}"
        if key not in seen:
            seen.add(key)
            unique.append(job)

    return unique


async def _scrape_naukri(job_title: str, location: str) -> List[Dict]:
    """Scrape Naukri.com job listings."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("   ⚠️  Playwright not installed. Run: pip install playwright && playwright install chromium")
        return _demo_jobs("naukri", job_title, location)

    jobs = []
    title_slug = quote(job_title.replace(" ", "-"))
    loc_slug = quote(location.lower())
    url = f"https://www.naukri.com/{title_slug}-jobs-in-{loc_slug}"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(3000)

            # Naukri job card selectors
            cards = await page.query_selector_all("article.jobTuple, .job-container, [class*='jobTuple']")
            
            for card in cards[:25]:
                try:
                    title_el  = await card.query_selector("a.title, .jobTitle a, [class*='title'] a")
                    comp_el   = await card.query_selector("a.subTitle, .companyInfo a, [class*='company']")
                    loc_el    = await card.query_selector(".location, [class*='location']")
                    exp_el    = await card.query_selector(".experience, [class*='experience']")
                    desc_el   = await card.query_selector(".job-description, [class*='description']")

                    title   = await title_el.inner_text()   if title_el  else "Unknown"
                    company = await comp_el.inner_text()    if comp_el   else "Unknown"
                    loc     = await loc_el.inner_text()     if loc_el    else location
                    exp     = await exp_el.inner_text()     if exp_el    else ""
                    desc    = await desc_el.inner_text()    if desc_el   else ""
                    link    = await title_el.get_attribute("href") if title_el else url

                    jobs.append({
                        "title":       title.strip(),
                        "company":     company.strip(),
                        "location":    loc.strip(),
                        "experience":  exp.strip(),
                        "description": desc.strip()[:500],
                        "link":        link if link.startswith("http") else "https://www.naukri.com" + (link or ""),
                        "source":      "naukri"
                    })
                except Exception:
                    continue

            await browser.close()
    except Exception as e:
        print(f"   ⚠️  Naukri scrape failed: {e}. Using demo data.")
        return _demo_jobs("naukri", job_title, location)

    return jobs if jobs else _demo_jobs("naukri", job_title, location)


async def _scrape_indeed(job_title: str, location: str) -> List[Dict]:
    """Scrape Indeed.co.in job listings."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return _demo_jobs("indeed", job_title, location)

    jobs = []
    url = f"https://in.indeed.com/jobs?q={quote(job_title)}&l={quote(location)}"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(3000)

            cards = await page.query_selector_all(".job_seen_beacon, .tapItem, [class*='job_seen']")

            for card in cards[:25]:
                try:
                    title_el   = await card.query_selector("h2.jobTitle a, [data-testid='jobTitle'] a, .jobTitle a")
                    comp_el    = await card.query_selector("[data-testid='company-name'], .companyName, span.company")
                    loc_el     = await card.query_selector("[data-testid='text-location'], .companyLocation")
                    snippet_el = await card.query_selector(".job-snippet, [class*='snippet']")

                    title   = await title_el.inner_text()   if title_el   else "Unknown"
                    company = await comp_el.inner_text()    if comp_el    else "Unknown"
                    loc     = await loc_el.inner_text()     if loc_el     else location
                    snippet = await snippet_el.inner_text() if snippet_el else ""
                    href    = await title_el.get_attribute("href") if title_el else ""

                    jobs.append({
                        "title":       title.strip(),
                        "company":     company.strip(),
                        "location":    loc.strip(),
                        "experience":  "",
                        "description": snippet.strip()[:500],
                        "link":        "https://in.indeed.com" + href if href and not href.startswith("http") else href,
                        "source":      "indeed"
                    })
                except Exception:
                    continue

            await browser.close()
    except Exception as e:
        print(f"   ⚠️  Indeed scrape failed: {e}. Using demo data.")
        return _demo_jobs("indeed", job_title, location)

    return jobs if jobs else _demo_jobs("indeed", job_title, location)


async def _scrape_linkedin(job_title: str, location: str) -> List[Dict]:
    """Scrape LinkedIn public job listings (no login required for public listings)."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return _demo_jobs("linkedin", job_title, location)

    jobs = []
    url = (f"https://www.linkedin.com/jobs/search/?"
           f"keywords={quote(job_title)}&location={quote(location)}&f_TPR=r604800")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(4000)

            cards = await page.query_selector_all(".base-card, .job-search-card")

            for card in cards[:25]:
                try:
                    title_el   = await card.query_selector("h3.base-search-card__title, .job-search-card__title")
                    comp_el    = await card.query_selector("h4.base-search-card__subtitle a, .job-search-card__company-name")
                    loc_el     = await card.query_selector(".job-search-card__location")
                    link_el    = await card.query_selector("a.base-card__full-link, a.job-search-card__title-link")

                    title   = await title_el.inner_text() if title_el else "Unknown"
                    company = await comp_el.inner_text()  if comp_el  else "Unknown"
                    loc     = await loc_el.inner_text()   if loc_el   else location
                    link    = await link_el.get_attribute("href") if link_el else url

                    jobs.append({
                        "title":       title.strip(),
                        "company":     company.strip(),
                        "location":    loc.strip(),
                        "experience":  "",
                        "description": "",
                        "link":        link,
                        "source":      "linkedin"
                    })
                except Exception:
                    continue

            await browser.close()
    except Exception as e:
        print(f"   ⚠️  LinkedIn scrape failed: {e}. Using demo data.")
        return _demo_jobs("linkedin", job_title, location)

    return jobs if jobs else _demo_jobs("linkedin", job_title, location)


def _demo_jobs(source: str, title: str, location: str) -> List[Dict]:
    """Demo jobs used when scraping is unavailable."""
    return [
        {
            "title": f"Senior {title}",
            "company": "TCS Digital",
            "location": location,
            "experience": "3-5 years",
            "description": f"We are looking for a {title} with strong Python/Django skills. "
                           "Experience with REST APIs, PostgreSQL, and cloud platforms required.",
            "link": "https://www.naukri.com/demo",
            "source": source
        },
        {
            "title": f"{title}",
            "company": "Infosys BPM",
            "location": location,
            "experience": "2-4 years",
            "description": f"Seeking {title} for our growing team. "
                           "Must have hands-on experience with Python, SQL, and microservices.",
            "link": "https://www.naukri.com/demo2",
            "source": source
        },
        {
            "title": f"Junior {title}",
            "company": "Startup India Pvt Ltd",
            "location": location,
            "experience": "0-2 years",
            "description": f"Exciting opportunity for a {title}. "
                           "Looking for candidates with Python basics and eagerness to learn.",
            "link": "https://www.indeed.com/demo",
            "source": source
        }
    ]
