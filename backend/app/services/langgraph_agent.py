"""
LangGraph Agent for LinkedIn Job Search.

This module implements a state machine-based agent that uses LLM to dynamically
analyze LinkedIn pages and extract job information intelligently.

Architecture:
    START → analyze_page → validate_selectors → browse_jobs → validate_data
                ↑              ↓ (failure)              ↓
                └──────────────┘                   pagination
                                                       ↓
                                              (has_next) → analyze_page
                                              (no_next)  → END
"""

import asyncio
import json
import re
import random
from typing import TypedDict, List, Dict, Optional, Annotated, Any
from operator import add

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from ..config import get_settings


# =============================================================================
# State Definition
# =============================================================================

class AgentState(TypedDict):
    """State for the LangGraph job scraping agent."""
    # Browser state
    page_html: str                    # Current page HTML content
    page_url: str                     # Current page URL
    
    # Extraction state
    extracted_jobs: List[Dict]        # Accumulated jobs (not using add to avoid duplication)
    selectors: Dict[str, str]         # LLM-identified CSS selectors
    current_job_cards_html: List[str] # HTML of individual job cards
    job_card_elements: List[Any]      # Playwright element handles for job cards
    current_job_index: int            # Index of current job being browsed
    
    # Control flow
    current_step: str                 # Current step name
    error_count: int                  # Retry counter
    max_errors: int                   # Max retries before giving up
    has_next_page: bool               # Whether pagination continues
    page_number: int                  # Current page number
    max_pages: int                    # Max pages to scrape
    
    # Progress tracking
    messages: Annotated[List[str], add]  # Progress messages for SSE
    
    # Search parameters
    search_params: Dict[str, str]     # keywords, location, etc.
    max_jobs: int                     # Max jobs to collect
    
    # Browser agent reference (passed in)
    browser_agent: Any                # LinkedInBrowserAgent instance


# =============================================================================
# Helper Functions
# =============================================================================

def get_llm() -> ChatOpenAI:
    """Get configured LLM client."""
    settings = get_settings()
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        api_key=settings.openai_api_key
    )


async def safe_get_page_content(page, max_retries: int = 3) -> str:
    """Safely get page content with retries for navigation timing issues."""
    for attempt in range(max_retries):
        try:
            # Wait for page to be stable
            await asyncio.sleep(1)
            
            # Try to wait for network to be idle
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass
            
            # Get content
            content = await page.content()
            if content and len(content) > 1000:
                return content
        except Exception as e:
            if "navigating" in str(e).lower():
                await asyncio.sleep(2)
                continue
            raise e
    
    # Final attempt
    await asyncio.sleep(2)
    return await page.content()


async def human_like_delay():
    """Add random human-like delay."""
    await asyncio.sleep(random.uniform(0.5, 1.5))


# =============================================================================
# Node 1: Page Analyzer (analyze_page)
# =============================================================================

async def analyze_page(state: AgentState) -> dict:
    """
    Analyze the LinkedIn page HTML and identify CSS selectors for job extraction.
    """
    browser_agent = state["browser_agent"]
    page = browser_agent.page
    
    # Wait for page to stabilize and get fresh HTML
    try:
        await asyncio.sleep(2)
        
        # Wait for job list to appear
        job_list_selectors = [
            "ul.jobs-search__results-list",
            ".jobs-search-results-list",
            "[data-job-id]"
        ]
        
        for sel in job_list_selectors:
            try:
                await page.wait_for_selector(sel, timeout=10000)
                break
            except:
                continue
        
        # Scroll to load more content
        await page.evaluate("window.scrollBy(0, 500)")
        await asyncio.sleep(1)
        
        page_html = await safe_get_page_content(page)
        page_url = page.url
        
    except Exception as e:
        return {
            **state,
            "error_count": state["error_count"] + 1,
            "current_step": "analyze_page",
            "messages": [f"⚠️ Page load error: {str(e)[:80]}"]
        }
    
    llm = get_llm()
    
    # Truncate HTML to avoid token limits
    html_sample = page_html[:25000]
    
    prompt = f"""Analyze this LinkedIn Jobs page HTML and identify CSS selectors for job extraction.

Find selectors for:
1. job_card_container: The <li> or <div> containing each job card (usually has data-occludable-job-id attribute)
2. job_title: The job title element inside a card
3. company_name: The company name element
4. location: Job location element
5. next_page_button: Pagination button

Important LinkedIn patterns to look for:
- li[data-occludable-job-id] - job card containers
- .jobs-search-results__list-item - job list items
- .job-card-container - newer card container
- h3 or a elements for titles
- [data-job-id] attributes

HTML SAMPLE:
```html
{html_sample}
```

Respond with ONLY valid JSON:
{{
    "job_card_container": "li[data-occludable-job-id], .jobs-search-results__list-item",
    "job_title": "selector",
    "company_name": "selector",
    "location": "selector",
    "next_page_button": "selector",
    "confidence": 0.0-1.0
}}"""

    try:
        response = await llm.ainvoke([
            SystemMessage(content="You are a web scraping expert. Analyze LinkedIn HTML and provide accurate CSS selectors. Respond only with valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        result = json.loads(content.strip())
        
        return {
            **state,
            "page_html": page_html,
            "page_url": page_url,
            "selectors": result,
            "current_step": "validate_selectors",
            "messages": [f"📊 Page analyzed. Confidence: {result.get('confidence', 'N/A')}"]
        }
        
    except Exception as e:
        return {
            **state,
            "page_html": page_html,
            "page_url": page_url,
            "error_count": state["error_count"] + 1,
            "current_step": "analyze_page",
            "messages": [f"❌ Analysis error: {str(e)[:80]}"]
        }


# =============================================================================
# Node 2: Selector Validator (validate_selectors)
# =============================================================================

async def validate_selectors(state: AgentState) -> dict:
    """
    Validate selectors and collect job card elements for browsing.
    """
    browser_agent = state["browser_agent"]
    selectors = state.get("selectors", {})
    
    if not selectors or not browser_agent:
        return {
            **state,
            "error_count": state["error_count"] + 1,
            "current_step": "analyze_page",
            "messages": ["⚠️ No selectors, re-analyzing..."]
        }
    
    try:
        page = browser_agent.page
        
        # Try multiple selectors for job cards
        job_card_selectors = [
            selectors.get("job_card_container", ""),
            "li[data-occludable-job-id]",
            ".jobs-search-results__list-item",
            "li.ember-view.jobs-search-results__list-item",
            ".job-card-container",
            "[data-job-id]"
        ]
        
        cards = []
        used_selector = ""
        for sel in job_card_selectors:
            if not sel:
                continue
            try:
                found = await page.query_selector_all(sel)
                if len(found) > 0:
                    cards = found
                    used_selector = sel
                    break
            except:
                continue
        
        if len(cards) >= 1:
            # Store element handles for later browsing
            return {
                **state,
                "job_card_elements": cards,
                "current_job_index": 0,
                "current_step": "browse_jobs",
                "messages": [f"✅ Found {len(cards)} job cards using: {used_selector[:50]}"]
            }
        else:
            return {
                **state,
                "error_count": state["error_count"] + 1,
                "current_step": "analyze_page",
                "messages": ["⚠️ No job cards found, re-analyzing..."]
            }
            
    except Exception as e:
        return {
            **state,
            "error_count": state["error_count"] + 1,
            "current_step": "analyze_page",
            "messages": [f"❌ Validation error: {str(e)[:80]}"]
        }


# =============================================================================
# Node 3: Browse Jobs (browse_jobs) - Click and extract each job
# =============================================================================

async def browse_jobs(state: AgentState) -> dict:
    """
    Browse through job cards one by one, clicking each to load details,
    then extract job information from the detail panel.
    """
    browser_agent = state["browser_agent"]
    page = browser_agent.page
    job_cards = state.get("job_card_elements", [])
    extracted_jobs = state.get("extracted_jobs", []).copy()  # Copy to avoid mutation
    max_jobs = state.get("max_jobs", 50)
    
    if not job_cards:
        return {
            **state,
            "current_step": "pagination_handler",
            "messages": ["⚠️ No job cards to browse"]
        }
    
    llm = get_llm()
    jobs_this_page = []
    seen_ids = {job.get("id") for job in extracted_jobs if job.get("id")}
    
    # Process each job card
    for i, card in enumerate(job_cards):
        if len(extracted_jobs) + len(jobs_this_page) >= max_jobs:
            break
        
        try:
            # Get job ID from card to avoid duplicates
            job_id = None
            try:
                job_id = await card.get_attribute("data-occludable-job-id")
                if not job_id:
                    job_id = await card.get_attribute("data-job-id")
            except:
                pass
            
            if job_id and job_id in seen_ids:
                continue
            
            # Scroll card into view
            try:
                await card.scroll_into_view_if_needed()
            except:
                pass
            
            await human_like_delay()
            
            # Click the job card to load details
            try:
                await card.click()
            except Exception as e:
                # Try clicking inner element
                try:
                    inner = await card.query_selector("a, div[role='button']")
                    if inner:
                        await inner.click()
                except:
                    continue
            
            # Wait for detail panel to load
            await asyncio.sleep(2)
            
            # Wait for description to appear
            desc_selectors = [
                "div.jobs-description",
                ".jobs-unified-description",
                ".jobs-description-content",
                "div.show-more-less-html__markup"
            ]
            
            for sel in desc_selectors:
                try:
                    await page.wait_for_selector(sel, timeout=5000)
                    break
                except:
                    continue
            
            # Extract job details from detail panel
            job_data = await extract_job_from_detail_panel(page, llm, job_id)
            
            if job_data and job_data.get("title") and job_data.get("company"):
                if job_data["id"] not in seen_ids:
                    jobs_this_page.append(job_data)
                    seen_ids.add(job_data["id"])
            
            await human_like_delay()
            
        except Exception as e:
            print(f"Error browsing job {i}: {e}")
            continue
    
    # Combine with existing jobs
    all_jobs = extracted_jobs + jobs_this_page
    
    return {
        **state,
        "extracted_jobs": all_jobs,
        "current_step": "validate_data",
        "messages": [f"👁️ Browsed {len(jobs_this_page)} jobs on page {state.get('page_number', 1)}. Total: {len(all_jobs)}"]
    }


async def extract_job_from_detail_panel(page, llm, job_id_hint: Optional[str] = None) -> Optional[Dict]:
    """Extract job information from the detail panel using multiple strategies."""
    
    try:
        # Strategy 1: Direct selector extraction
        job_data = {}
        
        # Title
        title_selectors = [
            "h1.t-24.t-bold.inline",
            ".jobs-unified-top-card__job-title",
            "h2.t-24.t-bold",
            ".job-details-jobs-unified-top-card__job-title",
            "h1.topcard__title"
        ]
        for sel in title_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    job_data["title"] = (await el.inner_text()).strip()
                    break
            except:
                continue
        
        # Company
        company_selectors = [
            ".jobs-unified-top-card__company-name a",
            ".jobs-unified-top-card__company-name",
            ".job-details-jobs-unified-top-card__company-name",
            "a.topcard__org-name-link"
        ]
        for sel in company_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    job_data["company"] = (await el.inner_text()).strip()
                    break
            except:
                continue
        
        # Location
        location_selectors = [
            ".jobs-unified-top-card__bullet",
            ".job-details-jobs-unified-top-card__primary-description-container span",
            ".topcard__flavor--bullet"
        ]
        for sel in location_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    job_data["location"] = (await el.inner_text()).strip()
                    break
            except:
                continue
        
        # Posted time
        posted_selectors = [
            ".jobs-unified-top-card__posted-date",
            "span.posted-time-ago__text",
            ".job-details-jobs-unified-top-card__primary-description-container"
        ]
        for sel in posted_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if "ago" in text.lower() or "hour" in text.lower() or "day" in text.lower():
                        job_data["posted_time"] = text
                        break
            except:
                continue
        
        # Description
        desc_selectors = [
            "div.jobs-description__content",
            "div.show-more-less-html__markup",
            ".jobs-description-content__text"
        ]
        for sel in desc_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    job_data["description"] = (await el.inner_text()).strip()[:2000]
                    break
            except:
                continue
        
        # Get URL and extract ID
        url = page.url
        job_id = job_id_hint
        if not job_id:
            match = re.search(r'/view/(\d+)', url)
            if match:
                job_id = match.group(1)
            else:
                match = re.search(r'currentJobId=(\d+)', url)
                if match:
                    job_id = match.group(1)
        
        if not job_id:
            job_id = str(hash(job_data.get("title", "") + job_data.get("company", "")))
        
        # If we got basic info, return it
        if job_data.get("title") and job_data.get("company"):
            return {
                "id": job_id,
                "title": job_data.get("title", "Unknown"),
                "company": job_data.get("company", "Unknown"),
                "location": job_data.get("location", ""),
                "posted_time": job_data.get("posted_time", ""),
                "description": job_data.get("description", ""),
                "salary": None,
                "url": url,
                "logo_initial": job_data.get("company", "?")[0].upper()
            }
        
        # Strategy 2: Use LLM if direct extraction failed
        try:
            detail_html = await page.evaluate("""
                () => {
                    const panel = document.querySelector('.jobs-unified-top-card, .job-details-jobs-unified-top-card');
                    return panel ? panel.outerHTML : '';
                }
            """)
            
            if detail_html and len(detail_html) > 100:
                prompt = f"""Extract job information from this LinkedIn job detail HTML:

{detail_html[:8000]}

Return JSON:
{{"title": "...", "company": "...", "location": "...", "posted_time": "..."}}"""

                response = await llm.ainvoke([
                    SystemMessage(content="Extract job data from HTML. Return only valid JSON."),
                    HumanMessage(content=prompt)
                ])
                
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                llm_data = json.loads(content.strip())
                
                return {
                    "id": job_id or str(hash(llm_data.get("title", "") + llm_data.get("company", ""))),
                    "title": llm_data.get("title", "Unknown"),
                    "company": llm_data.get("company", "Unknown"),
                    "location": llm_data.get("location", ""),
                    "posted_time": llm_data.get("posted_time", ""),
                    "description": job_data.get("description", ""),
                    "salary": None,
                    "url": url,
                    "logo_initial": llm_data.get("company", "?")[0].upper()
                }
        except:
            pass
        
        return None
        
    except Exception as e:
        print(f"Extract error: {e}")
        return None


# =============================================================================
# Node 4: Data Validator (validate_data)
# =============================================================================

async def validate_data(state: AgentState) -> dict:
    """Validate extracted data quality."""
    all_jobs = state.get("extracted_jobs", [])
    max_jobs = state.get("max_jobs", 50)
    
    if not all_jobs:
        return {
            **state,
            "current_step": "pagination_handler",
            "messages": ["⚠️ No jobs extracted, checking next page..."]
        }
    
    # Filter valid jobs
    valid_jobs = [j for j in all_jobs if j.get("title") and j.get("company")]
    
    # Check if done
    if len(valid_jobs) >= max_jobs:
        return {
            **state,
            "extracted_jobs": valid_jobs[:max_jobs],
            "current_step": "done",
            "messages": [f"🎯 Reached target: {max_jobs} jobs!"]
        }
    
    return {
        **state,
        "extracted_jobs": valid_jobs,
        "current_step": "pagination_handler",
        "messages": [f"✅ Validated {len(valid_jobs)} total jobs"]
    }


# =============================================================================
# Node 5: Pagination Handler
# =============================================================================

async def pagination_handler(state: AgentState) -> dict:
    """Handle pagination to next page."""
    browser_agent = state["browser_agent"]
    page_number = state.get("page_number", 1)
    max_pages = state.get("max_pages", 5)
    max_jobs = state.get("max_jobs", 50)
    total_jobs = len(state.get("extracted_jobs", []))
    
    if page_number >= max_pages:
        return {
            **state,
            "has_next_page": False,
            "current_step": "done",
            "messages": [f"📄 Reached max pages ({max_pages})"]
        }
    
    if total_jobs >= max_jobs:
        return {
            **state,
            "has_next_page": False,
            "current_step": "done",
            "messages": [f"✅ Collected {total_jobs} jobs"]
        }
    
    try:
        page = browser_agent.page
        
        # Try pagination buttons
        next_selectors = [
            f'button[aria-label="Page {page_number + 1}"]',
            'button[aria-label="Next"]',
            f'li[data-test-pagination-page-btn="{page_number + 1}"] button',
            '.artdeco-pagination__button--next'
        ]
        
        clicked = False
        for sel in next_selectors:
            try:
                button = await page.query_selector(sel)
                if button:
                    await button.scroll_into_view_if_needed()
                    await human_like_delay()
                    await button.click()
                    clicked = True
                    break
            except:
                continue
        
        if clicked:
            # Wait for new content
            await asyncio.sleep(4)
            
            # Wait for page to stabilize
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                await asyncio.sleep(2)
            
            return {
                **state,
                "page_number": page_number + 1,
                "has_next_page": True,
                "current_step": "analyze_page",
                "job_card_elements": [],  # Reset for new page
                "messages": [f"📄 Navigated to page {page_number + 1}"]
            }
        else:
            return {
                **state,
                "has_next_page": False,
                "current_step": "done",
                "messages": ["📄 No more pages"]
            }
            
    except Exception as e:
        return {
            **state,
            "has_next_page": False,
            "current_step": "done",
            "messages": [f"❌ Pagination error: {str(e)[:80]}"]
        }


# =============================================================================
# Graph Router
# =============================================================================

def should_continue(state: AgentState) -> str:
    """Determine next node based on state."""
    current_step = state.get("current_step", "analyze_page")
    error_count = state.get("error_count", 0)
    max_errors = state.get("max_errors", 3)
    
    if error_count >= max_errors:
        return "done"
    
    if current_step == "done":
        return END
    
    return current_step


# =============================================================================
# Build Graph
# =============================================================================

def create_job_scraper_graph():
    """Create the LangGraph state machine."""
    
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("analyze_page", analyze_page)
    graph.add_node("validate_selectors", validate_selectors)
    graph.add_node("browse_jobs", browse_jobs)
    graph.add_node("validate_data", validate_data)
    graph.add_node("pagination_handler", pagination_handler)
    graph.add_node("done", lambda state: {**state, "current_step": "done"})
    
    graph.set_entry_point("analyze_page")
    
    # Edges
    graph.add_conditional_edges(
        "analyze_page",
        should_continue,
        {
            "validate_selectors": "validate_selectors",
            "analyze_page": "analyze_page",
            "done": "done",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "validate_selectors",
        should_continue,
        {
            "browse_jobs": "browse_jobs",
            "analyze_page": "analyze_page",
            "done": "done",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "browse_jobs",
        should_continue,
        {
            "validate_data": "validate_data",
            "done": "done",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "validate_data",
        should_continue,
        {
            "pagination_handler": "pagination_handler",
            "done": "done",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "pagination_handler",
        should_continue,
        {
            "analyze_page": "analyze_page",
            "done": "done",
            END: END
        }
    )
    
    graph.add_edge("done", END)
    
    return graph.compile()


# =============================================================================
# Main Agent Class
# =============================================================================

class LangGraphJobAgent:
    """LangGraph-based LinkedIn Job Scraping Agent."""
    
    def __init__(self, browser_agent):
        self.browser_agent = browser_agent
        self.graph = create_job_scraper_graph()
    
    async def run(
        self,
        keywords: str,
        location: str,
        experience: str = "entry",
        posted_time: str = "24h",
        job_type: str = "remote",
        max_jobs: int = 50,
        max_pages: int = 5
    ):
        """Run the job scraping agent with intelligent browsing."""
        
        # Build search URL
        exp_map = {"internship": "1", "entry": "2", "mid": "3,4", "senior": "5,6"}
        time_map = {"24h": "r86400", "week": "r604800", "month": "r2592000"}
        type_map = {"remote": "2", "onsite": "1", "hybrid": "3"}
        
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = [
            f"keywords={keywords.replace(' ', '%20')}",
            f"location={location.replace(' ', '%20')}",
            f"f_E={exp_map.get(experience, '2')}",
            f"f_TPR={time_map.get(posted_time, 'r86400')}",
            f"f_WT={type_map.get(job_type, '2')}"
        ]
        search_url = base_url + "&".join(params)
        
        yield {"type": "progress", "message": "🚀 Starting LangGraph Agent..."}
        
        page = self.browser_agent.page
        
        # Navigate with retry
        for attempt in range(3):
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)
                break
            except Exception as e:
                if attempt < 2:
                    yield {"type": "progress", "message": f"⚠️ Retry navigation ({attempt + 1})..."}
                    await asyncio.sleep(2)
                else:
                    yield {"type": "progress", "message": f"❌ Navigation failed: {str(e)[:50]}"}
        
        yield {"type": "progress", "message": f"📍 On: {page.url[:60]}..."}
        
        # Wait for initial load
        await asyncio.sleep(3)
        
        # Get initial content safely
        try:
            page_html = await safe_get_page_content(page)
            page_url = page.url
        except Exception as e:
            yield {"type": "progress", "message": f"❌ Content error: {str(e)[:50]}"}
            yield {"type": "complete", "total": 0}
            return
        
        # Initialize state
        initial_state: AgentState = {
            "page_html": page_html,
            "page_url": page_url,
            "extracted_jobs": [],
            "selectors": {},
            "current_job_cards_html": [],
            "job_card_elements": [],
            "current_job_index": 0,
            "current_step": "analyze_page",
            "error_count": 0,
            "max_errors": 5,
            "has_next_page": True,
            "page_number": 1,
            "max_pages": max_pages,
            "messages": [],
            "search_params": {
                "keywords": keywords,
                "location": location,
                "experience": experience,
                "posted_time": posted_time,
                "job_type": job_type
            },
            "max_jobs": max_jobs,
            "browser_agent": self.browser_agent
        }
        
        yield {"type": "progress", "message": "🧠 LangGraph initialized - starting intelligent browsing"}
        
        # Run graph
        try:
            final_jobs = []
            async for event in self.graph.astream(initial_state):
                for node_name, node_state in event.items():
                    # Yield messages
                    for msg in node_state.get("messages", []):
                        yield {"type": "progress", "message": msg}
                    
                    # Track jobs
                    current_jobs = node_state.get("extracted_jobs", [])
                    if len(current_jobs) > len(final_jobs):
                        for job in current_jobs[len(final_jobs):]:
                            yield {"type": "job", "data": job}
                        final_jobs = current_jobs
                    
                    # Check completion
                    if node_state.get("current_step") == "done":
                        yield {"type": "progress", "message": f"✅ Completed! Total: {len(final_jobs)} jobs"}
                        yield {"type": "complete", "total": len(final_jobs)}
                        return
                        
        except Exception as e:
            yield {"type": "progress", "message": f"❌ Error: {str(e)[:100]}"}
            yield {"type": "complete", "total": len(final_jobs) if 'final_jobs' in dir() else 0}
