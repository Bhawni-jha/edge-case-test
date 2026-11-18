"""Optional AI step: asks an LLM for extra, domain-specific edge cases (Groq API).
If there is no key, no description, or anything fails, it returns [] and the app keeps working."""
import json
import logging
import os
import re

import requests

log = logging.getLogger("llm")
URL = "https://api.groq.com/openai/v1/chat/completions"


def suggest_cases(name: str, ftype: str, description: str, limit: int = 6) -> list[tuple]:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key or not description.strip():
        return []
    prompt = (
        f"Field: {name} (type {ftype}). Description: {description}\n"
        f"List up to {limit} tricky edge-case test values that a QA engineer should try for this field. "
        'Reply with ONLY a JSON array like [{"label":"short name","value":"test value","expected":"valid|invalid|sanitise"}].'
    )
    try:
        r = requests.post(
            URL,
            headers={"Authorization": f"Bearer {key}"},
            json={"model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), "temperature": 0.2,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        data = json.loads(re.search(r"\[.*\]", text, re.S).group(0))
        out = []
        for item in data[:limit]:
            expected = item.get("expected") if item.get("expected") in ("valid", "invalid", "sanitise") else "invalid"
            value = item.get("value")
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            out.append((f"AI: {str(item.get('label', 'case'))[:60]}", value, expected, "ai"))
        return out
    except Exception as exc:  # network, auth, parsing: never break the app
        log.warning("AI suggestions skipped: %s", exc)
        return []
