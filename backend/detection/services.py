"""
Gemini AI integration service for misinformation detection.

Uses the google-generativeai SDK for multimodal analysis (text + image).
Prompts are engineered to return structured JSON that the API can parse reliably.
"""

import json
import os
import re
import logging
import requests

from django.conf import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# ── Gemini Client ──────────────────────────────────────────────────────────────

_client = None


def _get_client():
    """Lazy-initialise the Gemini client so settings are loaded first."""
    global _client
    if _client is None:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in environment or settings.")
        _client = genai.Client(api_key=api_key)
    return _client


MODEL_NAME = "gemini-2.5-flash-preview-04-17"


# ── Search helper ──────────────────────────────────────────────────────────────


def fetch_search_results(query: str, num_results: int = 10) -> list[dict]:
    """Fetch supporting results from Google Custom Search API."""
    api_key = settings.SEARCH_ENGINE_API_KEY
    cx = settings.SEARCH_ENGINE_CX
    if not api_key or not cx:
        logger.warning("Search Engine API key or CX not configured — skipping search.")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": cx, "q": query, "num": num_results}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        items = response.json().get("items", [])
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
            }
            for item in items
        ]
    except Exception as exc:
        logger.error("Search API error: %s", exc)
        return []


# ── Prompt builders ────────────────────────────────────────────────────────────


def _build_text_prompt(news_text: str, search_results: list[dict]) -> str:
    prompt = (
        "You are an expert fact-checker. Analyze the following news claim using "
        "your knowledge and the supporting search results provided.\n\n"
        f'Claim: "{news_text}"\n\n'
    )

    if search_results:
        prompt += "Supporting search results:\n"
        for i, r in enumerate(search_results, 1):
            prompt += f'{i}. Title: {r["title"]}\n   Snippet: {r["snippet"]}\n   Link: {r["link"]}\n\n'

    prompt += (
        "Respond STRICTLY in the following JSON format (no markdown, no extra text):\n"
        "{\n"
        '  "title": "short descriptive title for this analysis",\n'
        '  "truth_score": <integer 0-100>,\n'
        '  "verdict": "Likely True" | "Possibly Fake" | "Unverifiable",\n'
        '  "reason": "detailed explanation of your analysis",\n'
        '  "evidence_links": ["url1", "url2"]\n'
        "}"
    )
    return prompt


def _build_image_prompt(claim_text: str, search_results: list[dict]) -> str:
    prompt = (
        "You are an expert media forensics analyst. Analyze this image along "
        "with the claim and search results to determine its authenticity.\n\n"
        f'Claim: "{claim_text or "No text claim provided"}"\n\n'
    )

    if search_results:
        prompt += "News articles for context:\n"
        for i, r in enumerate(search_results, 1):
            prompt += f'{i}. {r["title"]}\n   Snippet: {r["snippet"]}\n   Link: {r["link"]}\n\n'

    prompt += (
        "Respond STRICTLY in the following JSON format (no markdown, no extra text):\n"
        "{\n"
        '  "title": "short descriptive title for this analysis",\n'
        '  "truth_score": <integer 0-100>,\n'
        '  "verdict": "Likely True" | "Possibly Fake" | "Unverifiable",\n'
        '  "reason": "detailed explanation of your analysis",\n'
        '  "evidence_links": ["url1", "url2"]\n'
        "}"
    )
    return prompt


def _build_social_prompt(claim_text: str, search_results: list[dict]) -> str:
    prompt = (
        "You are an expert social-media fact-checker. Analyze the following "
        "social media claim together with the search results.\n\n"
        f'Claim: "{claim_text or "No text claim provided"}"\n\n'
    )

    if search_results:
        prompt += "News articles for context:\n"
        for i, r in enumerate(search_results, 1):
            prompt += f'{i}. {r["title"]}\n   Snippet: {r["snippet"]}\n   Link: {r["link"]}\n\n'

    prompt += (
        "Respond STRICTLY in the following JSON format (no markdown, no extra text):\n"
        "{\n"
        '  "title": "short descriptive title for this analysis",\n'
        '  "truth_score": <integer 0-100>,\n'
        '  "verdict": "Likely True" | "Possibly Fake" | "Unverifiable",\n'
        '  "reason": "detailed explanation of your analysis",\n'
        '  "evidence_links": ["url1", "url2"]\n'
        "}"
    )
    return prompt


# ── JSON extractor ─────────────────────────────────────────────────────────────


def _extract_json(text: str) -> dict:
    """Try to parse the model output as JSON, falling back to regex extraction."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    logger.error("Failed to extract JSON from Gemini response: %s", text[:500])
    return {
        "title": "Error",
        "truth_score": 0,
        "verdict": "Error",
        "reason": "Could not parse AI response.",
        "evidence_links": [],
    }


# ── Analysis functions ─────────────────────────────────────────────────────────


def analyze_text(news_text: str) -> dict:
    """Analyze a text claim for misinformation."""
    search_results = fetch_search_results(news_text)
    prompt = _build_text_prompt(news_text, search_results)

    client = _get_client()
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return _extract_json(response.text)


def analyze_image(image_path: str, claim_text: str) -> dict:
    """Analyze a local image file for misinformation."""
    ext = os.path.splitext(image_path)[-1][1:].lower()
    if ext == "jpg":
        ext = "jpeg"
    if ext not in ("jpeg", "png", "webp", "gif"):
        ext = "jpeg"

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    search_results = fetch_search_results(claim_text) if claim_text else []
    prompt = _build_image_prompt(claim_text, search_results)

    client = _get_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=f"image/{ext}"),
            prompt,
        ],
    )
    return _extract_json(response.text)


def analyze_social(url: str, claim: str) -> dict:
    """Analyze a social media post URL for misinformation."""
    from bs4 import BeautifulSoup

    try:
        page = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        page.raise_for_status()
    except Exception as exc:
        logger.error("Failed to fetch social URL %s: %s", url, exc)
        return {
            "title": "Error",
            "truth_score": 0,
            "verdict": "Error",
            "reason": f"Could not fetch the URL: {exc}",
            "evidence_links": [],
        }

    soup = BeautifulSoup(page.text, "html.parser")
    title = soup.title.string if soup.title else ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_content = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""
    full_claim = f"{title}\n{meta_content}\n{claim}"

    # Attempt to get an OG image for multimodal analysis
    image_tag = soup.find("meta", property="og:image") or soup.find("img")
    image_url = None
    if image_tag:
        image_url = image_tag.get("content") or image_tag.get("src")

    search_results = fetch_search_results(full_claim)

    client = _get_client()

    if image_url:
        try:
            img_resp = requests.get(image_url, timeout=15)
            img_resp.raise_for_status()
            image_bytes = img_resp.content

            raw_ext = os.path.splitext(image_url.split("?")[0])[-1][1:].lower()
            if raw_ext == "jpg":
                raw_ext = "jpeg"
            if raw_ext not in ("jpeg", "png", "webp", "gif"):
                raw_ext = "jpeg"

            prompt = _build_social_prompt(full_claim, search_results)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=f"image/{raw_ext}"),
                    prompt,
                ],
            )
            return _extract_json(response.text)
        except Exception as exc:
            logger.warning("Image fetch failed for social analysis, continuing text-only: %s", exc)

    # Text-only fallback
    prompt = _build_social_prompt(full_claim, search_results)
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return _extract_json(response.text)
