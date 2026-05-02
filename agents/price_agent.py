"""CrewAI Agent definition — the Price Watchdog reasoning agent."""
from crewai import Agent, LLM

from agents.tools import (
    check_history_tool,
    compare_price_tool,
    extract_product_info_tool,
    save_price_check_tool,
    scrape_page_tool,
    send_notification_tool,
    validate_url_tool,
)
from config import GEMINI_API_KEY

_llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=GEMINI_API_KEY,
    temperature=0.1,   # low temp for consistent, factual extraction
)

price_watchdog_agent = Agent(
    role="E-commerce Price Intelligence Analyst",
    goal=(
        "Accurately track product prices across Pakistani e-commerce platforms. "
        "Visit the product URL, extract the MAIN product's price (ignoring related/sidebar items), "
        "detect variants, compare against the target price, and alert the user on price drops."
    ),
    backstory=(
        "You are an expert e-commerce analyst specialising in the Pakistani online retail market. "
        "You know sites like PriceOye, Daraz, Sapphire, and Khaadi well. "
        "Product pages contain many prices — main product, related items, ads, bundles — "
        "and your specialty is identifying the CORRECT main product price. "
        "You always explain your reasoning clearly so users understand exactly which price "
        "you extracted and why."
    ),
    tools=[
        validate_url_tool,
        scrape_page_tool,
        extract_product_info_tool,
        compare_price_tool,
        check_history_tool,
        save_price_check_tool,
        send_notification_tool,
    ],
    llm=_llm,
    verbose=True,
    allow_delegation=False,
    max_iter=12,
    max_retry_limit=2,
)
