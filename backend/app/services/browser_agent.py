"""Browser agent service for LinkedIn job search automation."""
import asyncio
import json
import re
import time
from typing import List, Dict, Optional, AsyncGenerator
from pathlib import Path
import random
from playwright.async_api import Error as PlaywrightError

from ..config import get_settings
from ..models import Job


class LinkedInBrowserAgent:
    """
    Agent for searching LinkedIn jobs using browser automation.
    Connects to existing Chrome browser via CDP.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.playwright = None
        self.browser = None
        self.page = None
        self.use_mcp = self.settings.use_playwright_mcp
        # Tunables for human-like interaction
        self.mouse_jitter_px = 6
        self.min_pause = 0.5
        self.max_pause = 1.2

    async def _safe_goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 60000) -> bool:
        """Navigate with retries to handle net::ERR_ABORTED or fast redirects."""
        attempts = [wait_until, "load"]
        for wu in attempts:
            try:
                await self.page.goto(url, wait_until=wu, timeout=timeout)
                return True
            except PlaywrightError as e:
                if "ERR_ABORTED" in str(e) or "ERR_BLOCKED_BY_CLIENT" in str(e):
                    await asyncio.sleep(1)
                    continue
                # other errors: give up
                return False
            except Exception:
                await asyncio.sleep(1)
                continue
        return False
    
    async def initialize(self):
        """
        Initialize browser by connecting to an existing Chrome instance.
        
        User must start Chrome with remote debugging enabled:
        macOS: open -a "Google Chrome" --args --remote-debugging-port=9222
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError("Playwright is not installed. Run: pip install playwright && playwright install chromium")
        
        self.playwright = await async_playwright().start()
        
        # Try to connect to existing Chrome browser via CDP
        cdp_url = "http://localhost:9222"
        
        try:
            print(f"🔗 Connecting to existing Chrome browser at {cdp_url}...")
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            
            # Get existing contexts or create new one
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
            else:
                context = await self.browser.new_context()
            
            # Create a new page (tab) in the existing browser
            self.page = await context.new_page()
            print("✅ Connected! New tab opened in your existing Chrome browser.")
            
        except Exception as e:
            print(f"❌ Could not connect to existing Chrome: {e}")
            print("\n" + "="*60)
            print("Please start Chrome with remote debugging enabled:")
            print("="*60)
            print("\nmacOS:")
            print('  open -a "Google Chrome" --args --remote-debugging-port=9222')
            print("="*60 + "\n")
            await self.playwright.stop()
            raise RuntimeError(
                "Cannot connect to Chrome. Please start Chrome with --remote-debugging-port=9222"
            )
        
        if self.page is None:
            raise RuntimeError("Browser page failed to initialize.")
    
    async def close(self):
        """Close browser resources."""
        if self.page:
            try:
                await self.page.close()
            except:
                pass
            self.page = None
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
            self.browser = None
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass
            self.playwright = None
    
    def is_connected(self) -> bool:
        """Check if browser connection is still valid."""
        if self.page is None or self.browser is None:
            return False
        try:
            return not self.page.is_closed()
        except:
            return False
    
    async def check_login_status(self) -> bool:
        """Check if user is logged into LinkedIn."""
        if self.page is None:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        # Use safe navigation to avoid ERR_ABORTED
        ok = await self._safe_goto("https://www.linkedin.com/feed/")
        if not ok:
            # fallback to homepage/login
            await self._safe_goto("https://www.linkedin.com/")
        await asyncio.sleep(3)
        
        # Check if redirected to login page
        current_url = self.page.url
        if "login" in current_url or "authwall" in current_url:
            return False
        
        return True
    
    async def search_jobs(
        self,
        keywords: str,
        location: str,
        experience: str = "entry",
        posted_time: str = "24h",
        job_type: str = "remote",
        max_jobs: int = 50
    ) -> AsyncGenerator[Dict, None]:
        """
        Search LinkedIn jobs and yield results as they're found.
        Yields progress updates and job data.
        Robust against minor LinkedIn UI changes (multiple selectors, scrolling, dedup).
        """
        # Map experience levels
        exp_map = {
            "internship": "1",
            "entry": "2",
            "mid": "3,4",
            "senior": "5,6"
        }
        
        # Map posted time
        time_map = {
            "24h": "r86400",
            "week": "r604800",
            "month": "r2592000"
        }
        
        # Map job type
        type_map = {
            "remote": "2",
            "onsite": "1",
            "hybrid": "3"
        }
        
        # Build search URL
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = [
            f"keywords={keywords.replace(' ', '%20')}",
            f"location={location.replace(' ', '%20')}",
            f"f_E={exp_map.get(experience, '2')}",
            f"f_TPR={time_map.get(posted_time, 'r86400')}",
            f"f_WT={type_map.get(job_type, '2')}"
        ]
        search_url = base_url + "&".join(params)
        
        yield {"type": "progress", "message": f"Navigating to LinkedIn Jobs..."}

        # Use safe navigation - LinkedIn often triggers ERR_ABORTED during redirects
        await self._safe_goto(search_url)
        await asyncio.sleep(5)  # Give extra time for dynamic content

        # Report where we actually landed (helps debug authwall/login redirects)
        try:
            yield {"type": "progress", "message": f"Current page: {self.page.url}"}
        except Exception:
            pass

        # Small human-like wiggle to ensure focus inside the tab
        try:
            await self.page.mouse.move(200, 200)
            await self.page.mouse.move(210, 210)
        except Exception:
            pass

        jobs_found = []
        seen_ids = set()
        page_num = 0

        # Helper to find a viable selector for job list
        async def _wait_for_job_list() -> Optional[str]:
            selectors = [
                "ul.jobs-search__results-list",
                "li.jobs-search-results__list-item",
                "div.jobs-search-results-list",
                "[data-test-job-card]"
            ]
            for sel in selectors:
                try:
                    await self.page.wait_for_selector(sel, timeout=12000)
                    return sel
                except Exception:
                    continue
            return None

        async def _human_pause():
            await asyncio.sleep(random.uniform(self.min_pause, self.max_pause))

        async def _hover_and_click(element):
            try:
                box = await element.bounding_box()
                if box:
                    target_x = box["x"] + box["width"] / 2 + random.uniform(-self.mouse_jitter_px, self.mouse_jitter_px)
                    target_y = box["y"] + box["height"] / 2 + random.uniform(-self.mouse_jitter_px, self.mouse_jitter_px)
                    await self.page.mouse.move(target_x, target_y, steps=8)
                    await asyncio.sleep(0.2)
                await element.click()
            except Exception:
                await element.click()

        empty_page_retries = 0

        while len(jobs_found) < max_jobs:
            yield {"type": "progress", "message": f"Scanning page {page_num + 1}..."}

            selector = await _wait_for_job_list()
            if selector is None:
                yield {"type": "progress", "message": "No more job listings found."}
                break

            # Collect job cards with multiple fallbacks
            job_cards = await self.page.query_selector_all(
                "li.jobs-search-results__list-item, li.jobs-search__results-list li, [data-test-job-card], li[data-occludable-job-id], li.ember-view.jobs-search-results__list-item"
            )
            if not job_cards:
                empty_page_retries += 1
                yield {"type": "progress", "message": f"Job list empty (attempt {empty_page_retries}), retrying scroll..."}
                if empty_page_retries >= 2:
                    break
                await asyncio.sleep(1)
                continue
            empty_page_retries = 0

            # Scroll results list to force lazy-loaded cards (do a couple passes)
            for _ in range(3):
                try:
                    await self.page.evaluate(
                        "() => { const list = document.querySelector('ul.jobs-search__results-list'); if (list) list.scrollTop = list.scrollHeight; window.scrollBy(0, window.innerHeight * 0.9); }"
                    )
                    await asyncio.sleep(0.8)
                except Exception:
                    break
            # final small scroll to top so first cards are in view before clicking
            try:
                await self.page.evaluate(
                    "() => { const list = document.querySelector('ul.jobs-search__results-list'); if (list) list.scrollTop = 0; window.scrollTo({top:0}); }"
                )
            except Exception:
                pass

            # Refresh job_cards after scrolling in case new nodes appeared
            job_cards = await self.page.query_selector_all(
                "li.jobs-search-results__list-item, li.jobs-search__results-list li, [data-test-job-card], li[data-occludable-job-id], li.ember-view.jobs-search-results__list-item"
            )
            if not job_cards:
                yield {"type": "progress", "message": "Still no job cards after scrolls."}
                break

            for i, card in enumerate(job_cards):
                if len(jobs_found) >= max_jobs:
                    break

                try:
                    job_id_hint = await card.get_attribute("data-occludable-job-id")
                    if not job_id_hint:
                        job_id_hint = await card.get_attribute("data-job-id")

                    # Skip duplicates early
                    if job_id_hint and job_id_hint in seen_ids:
                        continue

                    await card.scroll_into_view_if_needed()
                    await _human_pause()
                    await _hover_and_click(card)
                    await asyncio.sleep(2.5)  # Give detail pane time

                    job_data = await self._extract_job_info(job_id_hint)
                    if job_data:
                        job_id = job_data.get("id")
                        if job_id and job_id in seen_ids:
                            continue
                        seen_ids.add(job_id)
                        jobs_found.append(job_data)
                        yield {"type": "job", "data": job_data}

                except Exception as e:
                    print(f"Error extracting job {i}: {e}")
                    continue

                # Rate limiting between jobs
                await _human_pause()

            # Try to go to next page (LinkedIn paginated buttons)
            page_num += 1
            try:
                next_button = await self.page.query_selector(
                    f'button[aria-label="Page {page_num + 1}"], li[data-test-pagination-page-btn] button[aria-label="Page {page_num + 1}"], button[aria-label="Next"]'
                )
                if next_button:
                    await next_button.scroll_into_view_if_needed()
                    await _human_pause()
                    await _hover_and_click(next_button)
                    await asyncio.sleep(3.2)
                else:
                    yield {"type": "progress", "message": "No next page button; stopping pagination."}
                    break
            except Exception:
                yield {"type": "progress", "message": "Pagination failed; stopping."}
                break

        yield {"type": "complete", "total": len(jobs_found)}
    
    async def _extract_job_info(self, job_id_hint: Optional[str] = None) -> Optional[Dict]:
        """Extract job information from the detail panel with resilient selectors."""
        try:
            # Wait for detail panel
            await self.page.wait_for_selector(
                ".jobs-unified-top-card, .jobs-search__job-details--container, [data-test-id=job-details]",
                timeout=7000
            )

            # Extract title
            title_selectors = [
                "h1.top-card-layout__title",
                ".jobs-unified-top-card__job-title",
                "[data-test-job-title]"
            ]
            title = "Unknown Title"
            for sel in title_selectors:
                el = await self.page.query_selector(sel)
                if el:
                    title = (await el.inner_text()).strip()
                    break

            # Extract company
            company_selectors = [
                "a.topcard__org-name-link",
                ".jobs-unified-top-card__company-name",
                "[data-test-company-name]"
            ]
            company = "Unknown Company"
            for sel in company_selectors:
                el = await self.page.query_selector(sel)
                if el:
                    company = (await el.inner_text()).strip()
                    break

            # Extract location
            location_selectors = [
                "span.topcard__flavor.topcard__flavor--bullet",
                ".jobs-unified-top-card__bullet",
                "[data-test-job-location]"
            ]
            location = ""
            for sel in location_selectors:
                el = await self.page.query_selector(sel)
                if el:
                    location = (await el.inner_text()).strip()
                    break

            # Extract posted time
            posted_selectors = [
                "span.posted-time-ago__text",
                ".jobs-unified-top-card__posted-date",
                "[data-test-posted-date]"
            ]
            posted_time = ""
            for sel in posted_selectors:
                el = await self.page.query_selector(sel)
                if el:
                    posted_time = (await el.inner_text()).strip()
                    break

            # Extract description
            desc_selectors = [
                "div.show-more-less-html__markup",
                ".jobs-description-content__text",
                "[data-test-description-text]"
            ]
            description = ""
            for sel in desc_selectors:
                el = await self.page.query_selector(sel)
                if el:
                    description = (await el.inner_text()).strip()
                    break

            # Get job URL
            url = self.page.url

            # Generate ID from URL or hint
            job_id = None
            if url:
                job_id_match = re.search(r"/view/(\d+)", url)
                if job_id_match:
                    job_id = job_id_match.group(1)
            if not job_id:
                job_id = job_id_hint or str(hash(url))

            return {
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "salary": None,  # LinkedIn often hides this
                "posted_time": posted_time,
                "description": description[:2000],  # Limit length
                "url": url,
                "logo_initial": company[0].upper() if company else "?"
            }

        except Exception as e:
            print(f"Error extracting job info: {e}")
            return None


# Singleton instance
_agent_instance: Optional[LinkedInBrowserAgent] = None


async def get_browser_agent() -> LinkedInBrowserAgent:
    """Get or create browser agent instance. Reconnects if connection was lost."""
    global _agent_instance
    
    # Check if existing instance is still valid
    if _agent_instance is not None:
        if not _agent_instance.is_connected():
            print("🔄 Browser connection lost, reconnecting...")
            await _agent_instance.close()
            _agent_instance = None
    
    # Create new instance if needed
    if _agent_instance is None:
        _agent_instance = LinkedInBrowserAgent()
        await _agent_instance.initialize()
    
    return _agent_instance


async def reset_browser_agent():
    """Force reset the browser agent."""
    global _agent_instance
    if _agent_instance is not None:
        await _agent_instance.close()
        _agent_instance = None
