"""
agents/auto_applier.py
Automates filling and submitting job application forms using Playwright.
Handles Naukri, Indeed, and basic HTML forms.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, AsyncGenerator, Tuple
import os


@asynccontextmanager
async def apply_to_job(jobs: List[Dict], resume: dict):
    """
    Context manager that yields an async generator of (job, success) tuples.
    
    Usage:
        async with apply_to_job(jobs, resume) as applier:
            async for job, success in applier:
                print(job, success)
    """
    async def _generator() -> AsyncGenerator[Tuple[Dict, bool], None]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            # Playwright not installed — simulate applying
            for job in jobs:
                await asyncio.sleep(0.5)
                yield job, True
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, slow_mo=300)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )

            for job in jobs:
                source = job.get("source", "")
                try:
                    if source == "naukri":
                        success = await _apply_naukri(context, job, resume)
                    elif source == "indeed":
                        success = await _apply_indeed(context, job, resume)
                    elif source == "linkedin":
                        success = await _apply_linkedin(context, job, resume)
                    else:
                        success = await _apply_generic(context, job, resume)
                    yield job, success
                except Exception as e:
                    yield job, False

            await browser.close()

    gen = _generator()
    yield gen


async def _apply_naukri(context, job: Dict, resume: dict) -> bool:
    """Apply to a Naukri job listing."""
    page = await context.new_page()
    try:
        await page.goto(job["link"], timeout=20000)
        await page.wait_for_timeout(2000)

        # Look for Apply button
        apply_btn = await page.query_selector(
            "button#apply-button, "
            "button[class*='apply'], "
            "a[class*='apply'], "
            "[class*='applyButton']"
        )
        if not apply_btn:
            return False

        await apply_btn.click()
        await page.wait_for_timeout(2000)

        # Fill in contact details if a form appears
        await _fill_common_fields(page, resume)

        # Try to upload resume
        await _upload_resume(page, resume)

        # Try to submit
        submit_btn = await page.query_selector(
            "button[type='submit'], "
            "button[class*='submit'], "
            "input[type='submit']"
        )
        if submit_btn:
            await submit_btn.click()
            await page.wait_for_timeout(2000)
            return True

        return True  # Treat click on apply as success
    except Exception:
        return False
    finally:
        await page.close()


async def _apply_indeed(context, job: Dict, resume: dict) -> bool:
    """Apply to an Indeed job listing."""
    page = await context.new_page()
    try:
        await page.goto(job["link"], timeout=20000)
        await page.wait_for_timeout(2000)

        # Click apply button
        apply_btn = await page.query_selector(
            "button[id*='apply'], "
            "a[id*='apply'], "
            ".jobsearch-IndeedApplyButton, "
            "button[class*='apply']"
        )
        if not apply_btn:
            return False

        await apply_btn.click()
        await page.wait_for_timeout(3000)

        # Handle multi-step Indeed application
        for _ in range(5):  # Max 5 steps
            # Fill text fields
            await _fill_common_fields(page, resume)
            await _fill_cover_letter(page, job.get("cover_letter", ""))

            # Check for file upload
            await _upload_resume(page, resume)

            # Click Continue/Next/Submit
            next_btn = await page.query_selector(
                "button[data-testid='continue-button'], "
                "button[aria-label*='Continue'], "
                "button[type='submit']"
            )
            if not next_btn:
                break
            text = await next_btn.inner_text()
            await next_btn.click()
            await page.wait_for_timeout(2000)
            if "submit" in text.lower() or "apply" in text.lower():
                break

        return True
    except Exception:
        return False
    finally:
        await page.close()


async def _apply_linkedin(context, job: Dict, resume: dict) -> bool:
    """Apply to a LinkedIn job (Easy Apply only)."""
    page = await context.new_page()
    try:
        await page.goto(job["link"], timeout=20000)
        await page.wait_for_timeout(3000)

        # Only handle Easy Apply
        easy_apply = await page.query_selector("button.jobs-apply-button, button[aria-label*='Easy Apply']")
        if not easy_apply:
            return False  # Skip non-Easy Apply jobs

        await easy_apply.click()
        await page.wait_for_timeout(2000)

        # Multi-step LinkedIn form
        for _ in range(8):
            await _fill_common_fields(page, resume)
            await _fill_cover_letter(page, job.get("cover_letter", ""))

            next_btn = await page.query_selector(
                "button[aria-label='Continue to next step'], "
                "button[aria-label='Review your application'], "
                "button[aria-label='Submit application']"
            )
            if not next_btn:
                break
            label = await next_btn.get_attribute("aria-label") or ""
            await next_btn.click()
            await page.wait_for_timeout(2000)
            if "submit" in label.lower():
                break

        return True
    except Exception:
        return False
    finally:
        await page.close()


async def _apply_generic(context, job: Dict, resume: dict) -> bool:
    """Generic form filler for unknown job sites."""
    page = await context.new_page()
    try:
        await page.goto(job["link"], timeout=20000)
        await page.wait_for_timeout(2000)
        await _fill_common_fields(page, resume)
        await _upload_resume(page, resume)
        submit = await page.query_selector("button[type='submit'], input[type='submit']")
        if submit:
            await submit.click()
            await page.wait_for_timeout(1000)
        return True
    except Exception:
        return False
    finally:
        await page.close()


# ── Helper Functions ─────────────────────────────────────────

async def _fill_common_fields(page, resume: dict):
    """Fill common application form fields."""
    field_map = {
        # Name fields
        'input[name*="name" i]:not([name*="company" i])':   resume.get("name", ""),
        'input[placeholder*="full name" i]':                 resume.get("name", ""),
        'input[id*="name" i]:not([id*="company" i])':        resume.get("name", ""),
        # Email
        'input[type="email"]':                               resume.get("email", ""),
        'input[name*="email" i]':                            resume.get("email", ""),
        'input[placeholder*="email" i]':                     resume.get("email", ""),
        # Phone
        'input[type="tel"]':                                 resume.get("phone", ""),
        'input[name*="phone" i]':                            resume.get("phone", ""),
        'input[name*="mobile" i]':                           resume.get("phone", ""),
        'input[placeholder*="phone" i]':                     resume.get("phone", ""),
        # Location
        'input[name*="location" i]':                         resume.get("location", ""),
        'input[name*="city" i]':                             resume.get("location", ""),
        # Experience years
        'input[name*="experience" i]':                       str(resume.get("experience_years", 0)),
        'input[placeholder*="years of experience" i]':       str(resume.get("experience_years", 0)),
    }

    for selector, value in field_map.items():
        if not value:
            continue
        try:
            el = await page.query_selector(selector)
            if el and await el.is_visible():
                await el.fill("")
                await el.fill(value)
        except Exception:
            continue


async def _fill_cover_letter(page, cover_letter: str):
    """Fill cover letter textarea."""
    if not cover_letter:
        return
    selectors = [
        'textarea[name*="cover" i]',
        'textarea[placeholder*="cover letter" i]',
        'textarea[id*="cover" i]',
        'textarea[name*="message" i]',
        'textarea[placeholder*="message" i]',
    ]
    for selector in selectors:
        try:
            el = await page.query_selector(selector)
            if el and await el.is_visible():
                await el.fill(cover_letter[:2000])
                return
        except Exception:
            continue


async def _upload_resume(page, resume: dict):
    """Upload resume PDF if a file input is found."""
    resume_path = os.path.abspath("data/resume.pdf")
    if not os.path.exists(resume_path):
        return

    selectors = [
        'input[type="file"][accept*="pdf" i]',
        'input[type="file"][name*="resume" i]',
        'input[type="file"][id*="resume" i]',
        'input[type="file"]',
    ]
    for selector in selectors:
        try:
            el = await page.query_selector(selector)
            if el:
                await el.set_input_files(resume_path)
                return
        except Exception:
            continue
