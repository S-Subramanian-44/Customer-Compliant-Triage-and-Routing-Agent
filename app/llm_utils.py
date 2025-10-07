import os
import json
import logging
import requests
from . import config
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

# Default endpoints
DEFAULT_OPENAI_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
# GitHub Models URL (user can override with GITHUB_MODELS_URL env var)
DEFAULT_GITHUB_MODELS_URL = os.getenv("GITHUB_MODELS_URL", "https://models.github.ai/inference/chat/completions")
DEFAULT_GITHUB_API_VERSION = os.getenv('GITHUB_API_VERSION', '2022-11-28')


def _build_headers_and_url():
    """Return (url, headers) based on available tokens and env vars.

    Priority:
    - If config.GITHUB_TOKEN is set, use GITHUB_MODELS_URL and GitHub headers.
    - Otherwise use DEFAULT_OPENAI_URL and expect an OpenAI-style key in env LLM_API_KEY or OPENAI_API_KEY.
    """
    # If user set a GitHub token, prefer GitHub Models endpoint
    gh_token = getattr(config, 'GITHUB_TOKEN', None)
    if gh_token:
        url = getattr(config, 'GITHUB_MODELS_URL', DEFAULT_GITHUB_MODELS_URL)
        headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {gh_token}',
            'Content-Type': 'application/json',
            'X-GitHub-Api-Version': getattr(config, 'GITHUB_API_VERSION', DEFAULT_GITHUB_API_VERSION),
        }
        return url, headers

    # Fallback to OpenAI-style
    url = os.getenv('LLM_API_URL', DEFAULT_OPENAI_URL)
    api_key = os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    return url, headers


def call_llm(prompt: str, system: str = None, temperature: float = 0.0, max_tokens: int = 512):
    url, headers = _build_headers_and_url()

    # Global cooldown to avoid hammering provider after a hard rate-limit
    if getattr(call_llm, '_cooldown_until', None):
        if datetime.utcnow() < call_llm._cooldown_until:
            logger.warning("LLM global cooldown active until %s, skipping call", call_llm._cooldown_until)
            return None

    # If no auth header present, warn and fall back
    if 'Authorization' not in headers:
        logger.warning("No LLM authorization header found; falling back to local heuristics")
        return None

    payload = {
        "model": config.LLM_MODEL,
        "messages": [],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if system:
        payload["messages"].append({"role": "system", "content": system})
    payload["messages"].append({"role": "user", "content": prompt})

    # Try with limited retries for transient 429s
    max_retries = 3
    backoff = 1.0
    attempt = 0
    while True:
        attempt += 1
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=config.LLM_TIMEOUT)
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as he:
                status = resp.status_code
                text = resp.text
            # Handle auth errors with helpful guidance
            if status == 401:
                token = headers.get('Authorization', '')
                # token may look like 'Bearer github_p...'
                if 'github_' in token and 'openai' in url:
                    logger.error("401 Unauthorized: looks like you're using a GitHub token against an OpenAI-style URL. Set GITHUB_MODELS_URL (for GitHub Models) or LLM_API_URL (for OpenAI) correctly. Response: %s", text)
                elif token.startswith('Bearer sk-') and ('github' in url or 'models.github' in url or 'models.github.ai' in url):
                    logger.error("401 Unauthorized: looks like you're using an OpenAI key against a GitHub Models URL. Use the matching provider+url (set GITHUB_TOKEN for GitHub Models or LLM_API_KEY/OPENAI_API_KEY for OpenAI). Response: %s", text)
                else:
                    logger.error("LLM call failed: 401 Unauthorized. Response: %s", text)
                return None

            # Handle rate limits (429) - parse Retry-After header or provider message
            if status == 429:
                # Rate limit reached. Try to determine cooldown from Retry-After header or provider message.
                retry_after = None
                ra = resp.headers.get('Retry-After') if resp is not None else None
                if ra:
                    try:
                        retry_after = int(ra)
                    except Exception:
                        retry_after = None

                if not retry_after:
                    # attempt to parse seconds from JSON body message
                    try:
                        body = resp.json()
                        # Example provider body: {"error": {"message": "Please wait 71085 seconds"}}
                        msg = ''
                        if isinstance(body, dict):
                            # search for nested messages
                            if 'error' in body and isinstance(body['error'], dict):
                                msg = body['error'].get('message', '') or body['error'].get('details', '')
                            else:
                                # try flatten
                                msg = json.dumps(body)
                        if isinstance(msg, str) and msg:
                            import re
                            m = re.search(r"(\d{3,6})\s*seconds", msg)
                            if m:
                                retry_after = int(m.group(1))
                    except Exception:
                        retry_after = None

                # If we still don't know, default to a conservative cooldown (1 hour)
                if not retry_after:
                    retry_after = 3600

                cooldown_until = datetime.utcnow() + timedelta(seconds=retry_after)
                # attach cooldown to the call_llm function to avoid further calls until reset
                call_llm._cooldown_until = cooldown_until
                logger.error("LLM rate limit reached: status=429, setting global cooldown until %s (retry_after=%s)", cooldown_until, retry_after)
                return None

            # If model unknown (GitHub/OpenAI returns 404 with unknown_model), try alternate model names
            if status == 404 and text and 'unknown_model' in text.lower():
                logger.warning("Model unknown response from LLM provider: %s. Attempting model-name fallbacks.", text)
                # Try a few variations
                tried = []
                original_model = payload.get('model')
                variants = []
                if isinstance(original_model, str):
                    # If model specified with provider prefix, try variants without/with openai/
                    if original_model.startswith('github/'):
                        name = original_model.split('/', 1)[1]
                        variants.append(name)
                        variants.append('openai/' + name)
                    elif original_model.startswith('openai/'):
                        name = original_model.split('/', 1)[1]
                        variants.append(original_model)
                        variants.append(name)
                    else:
                        variants.append(original_model)
                        variants.append('openai/' + original_model)
                        variants.append(original_model.replace('github/', ''))
                        variants.append('gpt-4o-mini')

                for m in variants:
                    if not m or m in tried:
                        continue
                    tried.append(m)
                    payload['model'] = m
                    logger.info("Retrying LLM request with model variant: %s", m)
                    try:
                        r2 = requests.post(url, headers=headers, json=payload, timeout=config.LLM_TIMEOUT)
                        r2.raise_for_status()
                        data = r2.json()
                        # success on retry
                        resp = r2
                        break
                    except requests.exceptions.RequestException:
                        logger.warning("Variant %s failed", m)
                        continue
                else:
                    logger.error("All model variants failed; please set LLM_MODEL to a valid model name for your provider.")
                    return None
            else:
                logger.error("LLM HTTP error %s: %s", status, text)
                return None
        except requests.exceptions.RequestException as e:
            # If it's a rate limit (requests may surface 429 as HTTPError above), handle here as well
            logger.exception("LLM call failed on attempt %s: %s", attempt, e)
            if attempt >= max_retries:
                return None
            time.sleep(backoff)
            backoff *= 2
            continue

        data = resp.json()
        # OpenAI/GitHub-compatible response path: prefer choices[0].message.content
        if isinstance(data, dict) and 'choices' in data and len(data['choices']) > 0:
            choice = data['choices'][0]
            # OpenAI shape
            if isinstance(choice, dict) and 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
            # GitHub might nest differently; try to find 'content'
            if isinstance(choice, dict) and 'content' in choice:
                return choice['content']
        # If provider returns text directly
        if isinstance(data, dict) and 'text' in data:
            return data['text']
        # Last resort: return full JSON string
        return json.dumps(data)
    # end while loop


def classify_complaint(text: str):
    prompt = (
        "You are a customer complaint classification AI. "
        "Classify the complaint text into one or more categories from the list:"
        " [\"Billing Issue\", \"Product Defect\", \"Refund Request\", \"Technical Issue\","
        " \"Delivery Problem\", \"Service Quality\", \"Others\"].\n"
        "Return only a JSON object exactly like: {\"categories\": [..], \"confidence\": 0.0}"
        "\nComplaint:\n" + text
    )
    resp = call_llm(prompt)
    if not resp:
        # fallback heuristic: keyword based
        categories = []
        low = text.lower()
        if any(w in low for w in ["bill", "invoice", "charge"]):
            categories.append("Billing Issue")
        # detect product defects including phrases like 'stopped working'
        if any(w in low for w in ["broken", "defect", "not working", "malfunction", "stopped working", "stopped"]):
            categories.append("Product Defect")
        if any(w in low for w in ["refund", "money back"]):
            categories.append("Refund Request")
        if any(w in low for w in ["error", "bug", "crash", "unable to", "fail"]):
            categories.append("Technical Issue")
        if any(w in low for w in ["deliver", "shipment", "late", "missing"]):
            categories.append("Delivery Problem")
        if any(w in low for w in ["rude", "bad service", "support", "experience"]):
            categories.append("Service Quality")
        if not categories:
            categories = ["Others"]
        return {"categories": categories, "confidence": 0.5}

    # try parse JSON out of resp
    try:
        obj = json.loads(resp)
        return obj
    except Exception:
        # try to extract JSON substring
        try:
            start = resp.index("{")
            end = resp.rindex("}")
            obj = json.loads(resp[start:end+1])
            return obj
        except Exception:
            logger.exception("Failed to parse LLM classification response")
            return {"categories": ["Others"], "confidence": 0.0}


def severity_and_routing(text: str, categories: list[str], sentiment: str = None, keywords: list[str] = None):
    # Build a richer prompt including sentiment and keywords if available
    prompt = (
        "Based on this complaint text, assign a severity level (Low, Medium, High, Urgent)"
        " and choose the best routing department from the mapping. Return JSON like:"
        " {\"severity\": \"High\", \"routed_department\": \"Logistics\", \"justification\": \"...\"}\n"
        "Complaint:\n" + text + "\nCategories:" + ",".join(categories)
    )
    if sentiment:
        prompt += "\nDetected sentiment:" + sentiment
    if keywords:
        prompt += "\nDetected keywords:" + ",".join(keywords)

    resp = call_llm(prompt)
    if not resp:
        # fallback based on keywords and sentiment rules (deterministic)
        low = text.lower()
        severity = "Low"

        # If explicit urgent words appear, immediately escalate to Urgent
        urgent_terms = ['urgent', 'asap', 'immediately', 'need it urgently']
        text_has_urgent = any(t in low for t in urgent_terms)
        keywords_l = [k.lower() for k in (keywords or [])]
        keywords_has_urgent = any(t in keywords_l for t in urgent_terms)
        if text_has_urgent or keywords_has_urgent:
            severity = 'Urgent'

        # Use sentiment as a secondary signal
        if severity != 'Urgent':
            if sentiment == 'Negative':
                severity = 'High'
            elif sentiment == 'Neutral':
                severity = 'Medium'
            elif sentiment == 'Positive':
                severity = 'Low'

        # Heuristics for categories and critical phrases
        # Product defects that indicate failure are high priority; if customer explicitly asks urgency, escalate to Urgent
        defect_indicators = ["not working", "stopped working", "stopped", "broken", "malfunction", "won't spin", "won't start"]
        billing_indicators = ['refund', 'charged', 'overcharged', 'double charge', 'fraud']

        if any(d in low for d in defect_indicators) or any(d in keywords_l for d in defect_indicators):
            # If already marked Urgent, keep it; otherwise escalate to High
            severity = severity if severity == 'Urgent' else max_severity(severity, 'High')

        if any(b in low for b in billing_indicators) or any(b in keywords_l for b in billing_indicators):
            severity = severity if severity == 'Urgent' else max_severity(severity, 'High')

        # Late delivery is medium priority unless urgent requested
        if any(w in low for w in ["late", "delay", "missing", "not here"]):
            severity = severity if severity == 'Urgent' else max_severity(severity, 'Medium')

        # Safety-critical words
        if any(w in low for w in ["life-threatening", "danger", "hazard"]):
            severity = 'Urgent'

        department = config.DEPARTMENT_MAP.get(categories[0], "General Support") if categories else "General Support"
        justification = "Fallback heuristic: urgency and category rules"
        return {"severity": severity, "routed_department": department, "justification": justification}

    try:
        obj = json.loads(resp)
        return obj
    except Exception:
        try:
            start = resp.index("{")
            end = resp.rindex("}")
            obj = json.loads(resp[start:end+1])
            return obj
        except Exception:
            logger.exception("Failed to parse LLM routing response")
            department = config.DEPARTMENT_MAP.get(categories[0], "General Support") if categories else "General Support"
            return {"severity": "Medium", "routed_department": department, "justification": "Parsing fallback"}


def max_severity(current: str, candidate: str) -> str:
    order = {"Low": 1, "Medium": 2, "High": 3, "Urgent": 4}
    return current if order.get(current, 0) >= order.get(candidate, 0) else candidate
