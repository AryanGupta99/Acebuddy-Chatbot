"""Minimal SalesIQ push helper used by the simplified Docker build.

This is a small, safe placeholder that implements a best-effort POST to the
SalesIQ conversations API. It keeps the same shape used elsewhere in the
project and avoids adding heavy dependencies or behavior.

In production you should replace this with a full implementation that handles
OAuth token refresh, retries, backoff, and robust error handling.
"""

import os
import logging
from typing import Optional, Dict, Any

import requests

def push_message(conv_id: str, message: str, metadata: Optional[Dict[str, Any]] = None, timeout: int = 8):
    """Post a message to a SalesIQ conversation (best-effort).

    Returns the response JSON on success or None on failure.
    """
    SALESIQ_API_BASE = os.getenv('SALESIQ_API_BASE')
    SALESIQ_ACCESS_TOKEN = os.getenv('SALESIQ_ACCESS_TOKEN')
    if not SALESIQ_API_BASE or not SALESIQ_ACCESS_TOKEN or not conv_id:
        logging.debug('SalesIQ push skipped: missing API base, token, or conv_id')
        return None

    url = f"{SALESIQ_API_BASE.rstrip('/')}/conversations/{conv_id}/messages"
    headers = {
        'Authorization': f'Zoho-oauthtoken {SALESIQ_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        'type': 'message',
        'source': 'bot',
        'message': message,
        'metadata': metadata or {}
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {'status_code': r.status_code, 'text': r.text}
    except Exception as e:
        logging.warning(f"SalesIQ push failed: {e}")
        return None

__all__ = ["push_message"]
"""
Helper functions to push bot messages into Zoho SalesIQ conversations.

Usage:
  from salesiq_push import send_message_to_salesiq
  send_message_to_salesiq(conversation_id, message, confidence)

This module reads the following environment variables:
  - SALESIQ_ACCESS_TOKEN   (Zoho OAuth access token or API token)
  - SALESIQ_API_BASE       (optional, default: https://www.zohoapis.com)

If `SALESIQ_ACCESS_TOKEN` is not provided, the function will do a dry-run and log the payload
instead of calling the Zoho API. This makes local testing possible without secrets.
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

SALESIQ_ACCESS_TOKEN = os.getenv("SALESIQ_ACCESS_TOKEN")
SALESIQ_API_BASE = os.getenv("SALESIQ_API_BASE", "https://www.zohoapis.com")


def send_message_to_salesiq(conversation_id: str, message: str, confidence: float = 1.0, should_escalate: bool = False, extra_metadata: Optional[dict] = None):
    """Send a bot message into a SalesIQ conversation.

    - conversation_id: Zoho conversation ID (or visitor_id - depends on your account)
    - message: textual message to send
    - confidence: float, used in metadata
    - should_escalate: whether this should trigger a handoff notice
    - extra_metadata: optional dict attached to message

    Returns: dict with API response or simulated payload when in dry-run mode.
    """

    payload = {
        "type": "message",
        "source": "bot",
        "message": message,
        "metadata": {
            "confidence": confidence,
        }
    }

    if extra_metadata:
        payload["metadata"].update(extra_metadata)

    # Add escalation note in metadata
    if should_escalate:
        payload["metadata"]["should_escalate"] = True

    # If no access token is set, do a dry-run (log and return payload)
    if not SALESIQ_ACCESS_TOKEN:
        logger.info("SALESIQ_ACCESS_TOKEN not set — dry-run mode. Would send:")
        logger.info(payload)
        return {"dry_run": True, "payload": payload}

    # Build API URL. The exact endpoint depends on Zoho account/region and API shape.
    # This is a generic endpoint pattern. Update if your account uses a different path.
    if not conversation_id:
        raise ValueError("conversation_id is required to push message to SalesIQ")

    api_url = f"{SALESIQ_API_BASE}/salesiq/v1/conversations/{conversation_id}/messages"

    headers = {
        "Authorization": f"Zoho-oauthtoken {SALESIQ_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        logger.info(f"Pushed message to SalesIQ conversation {conversation_id}: status={resp.status_code}")
        return {"status_code": resp.status_code, "response": resp.json() if resp.text else None}
    except requests.RequestException as e:
        logger.exception(f"Failed to push message to SalesIQ: {e}")
        return {"error": str(e)}
