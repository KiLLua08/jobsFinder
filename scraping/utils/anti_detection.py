"""
Anti-detection utilities for web scraping.

Websites detect bots by looking at patterns:
- Same User-Agent on every request
- Requests arriving at exact intervals (no human does that)
- Missing browser fingerprints

These utilities help us look more like a real human browsing.
"""

import random
import time


# A pool of real browser User-Agent strings.
# We rotate through these so each request looks like a different browser.
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def get_random_user_agent():
    """Pick a random User-Agent string from our pool.

    WHY: If every request uses the same User-Agent, the website knows
    it's a bot. By rotating, each request looks like a different person.
    """
    return random.choice(USER_AGENTS)


def random_delay(min_seconds=2, max_seconds=5):
    """Wait a random amount of time between actions.

    WHY: Real humans don't click links at exact 1-second intervals.
    Random delays between 2-5 seconds mimic natural browsing speed
    and reduce the chance of getting blocked.

    Args:
        min_seconds: Minimum wait time (default 2s)
        max_seconds: Maximum wait time (default 5s)
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay
