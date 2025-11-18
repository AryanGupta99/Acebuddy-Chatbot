"""
fetch_salesiq_transcripts.py

Flexible SalesIQ transcript fetcher (API-first).

Usage:
  1) Add these entries to your `.env` in the project root:
     SALESIQ_API_MODE=api                # or 'scrape' (scrape fallback not implemented automatically)
     SALESIQ_ACCESS_TOKEN=<your_oauth_access_token_or_api_key>
     SALESIQ_BASE_URL=<base_api_url>     # e.g. https://www.zohoapis.com/salesiq or the domain your account uses
     SALESIQ_LIST_ENDPOINT=/restapi/v1.0/chats
     SALESIQ_TRANSCRIPT_ENDPOINT_TEMPLATE=/restapi/v1.0/chats/{chat_id}/transcript

  2) Run from project root:
     python scripts/fetch_salesiq_transcripts.py

This script is intentionally flexible because SalesIQ accounts and APIs vary by region and auth method.
You must supply a working API endpoint and token. The script will:
  - fetch pages of chats filtered by status=closed
  - fetch transcript for each chat (by id) using the template endpoint
  - save output to `data/raw_transcripts_salesiq.json`
  - optionally call existing ingest script to push to Chroma (set --ingest)

Security: keep your tokens secret. This script writes transcripts to disk; remove or encrypt if sensitive.
"""

import os
import json
import time
import math
import hashlib
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(OUT_DIR, exist_ok=True)

ACCESS_TOKEN = os.getenv("SALESIQ_ACCESS_TOKEN")
BASE_URL = os.getenv("SALESIQ_BASE_URL", "https://salesiq.zoho.com")
# screen name is the account screen name (example: zylker)
SCREEN_NAME = os.getenv("SALESIQ_SCREEN_NAME")
# Default to API v2 endpoints used by SalesIQ docs
LIST_ENDPOINT = os.getenv("SALESIQ_LIST_ENDPOINT", "/api/v2/{screen_name}/conversations")
TRANSCRIPT_ENDPOINT_TEMPLATE = os.getenv("SALESIQ_TRANSCRIPT_ENDPOINT_TEMPLATE", "/api/v2/{screen_name}/conversations/{conversation_id}/messages")
PAGE_SIZE = int(os.getenv("SALESIQ_PAGE_SIZE", "20"))

HEADERS = {}
if ACCESS_TOKEN:
    # Prefer OAuth access token header format
    HEADERS["Authorization"] = f"Zoho-oauthtoken {ACCESS_TOKEN}"


def build_url(path: str, **fmt) -> str:
    # allow templates with {screen_name} and {conversation_id}
    if fmt:
        try:
            path = path.format(**fmt)
        except Exception:
            pass
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")


def fetch_closed_conversations(page: int = 1, limit: int = PAGE_SIZE, from_time: Optional[str] = None, to_time: Optional[str] = None):
    if not SCREEN_NAME:
        raise RuntimeError("Please set SALESIQ_SCREEN_NAME in your .env (example: zylker)")
    url = build_url(LIST_ENDPOINT, screen_name=SCREEN_NAME)
    params = {
        "status": "closed",
        "page": page,
        "limit": limit,
    }
    if from_time:
        params["from_time"] = from_time
    if to_time:
        params["to_time"] = to_time
    print(f"Requesting conversation list page {page} -> {url} (params={params})")
    rsp = http_get_with_retry(url, headers=HEADERS, params=params)
    return rsp.json()


def http_get_with_retry(url, headers=None, params=None, max_retries=5, backoff_base=0.5):
    attempt = 0
    while True:
        try:
            resp = requests.get(url, headers=headers or {}, params=params or None, timeout=60)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            attempt += 1
            if attempt > max_retries:
                raise
            sleep_for = backoff_base * (2 ** (attempt - 1)) + (attempt * 0.1)
            print(f"Request failed (attempt {attempt}/{max_retries}): {e}. Retrying in {sleep_for:.1f}s...")
            time.sleep(sleep_for)


def fetch_transcript(conversation_id: str, limit: int = None, from_time: Optional[str] = None, to_time: Optional[str] = None) -> Optional[dict]:
    if not SCREEN_NAME:
        raise RuntimeError("Please set SALESIQ_SCREEN_NAME in your .env (example: zylker)")
    endpoint = TRANSCRIPT_ENDPOINT_TEMPLATE.format(screen_name=SCREEN_NAME, conversation_id=conversation_id)
    url = build_url(endpoint)
    params = {}
    if limit:
        params["limit"] = limit
    if from_time:
        params["from_time"] = from_time
    if to_time:
        params["to_time"] = to_time
    print(f"Fetching transcript for conversation {conversation_id} -> {url} (params={params})")
    try:
        rsp = http_get_with_retry(url, headers=HEADERS, params=params)
        return rsp.json()
    except requests.RequestException as e:
        # When repeated retries fail, log and continue
        txt = getattr(e.response, 'text', None) if hasattr(e, 'response') else None
        print(f"Failed to fetch transcript for {conversation_id}: {e} - {txt}")
        return None


def main(ingest: bool = False, limit: Optional[int] = None, from_time: Optional[str] = None, to_time: Optional[str] = None):
    # Parameters for large fetches
    shard_size = int(os.getenv("SALESIQ_SHARD_SIZE", "5000"))
    max_chats = int(os.getenv("SALESIQ_MAX_CHATS", "0"))  # 0 means no limit
    resume_file = os.getenv("SALESIQ_RESUME_FILE", os.path.join(OUT_DIR, "salesiq_resume.json"))

    processed_ids = set()
    if os.path.exists(resume_file):
        try:
            with open(resume_file, "r", encoding="utf-8") as rf:
                processed_ids = set(json.load(rf))
        except Exception:
            processed_ids = set()

    all_transcripts = []
    shard_index = 1
    saved_count = 0
    page = 1
    total_fetched = 0
    while True:
        data = fetch_closed_conversations(page=page, limit=limit, from_time=from_time, to_time=to_time)
        # Expect the API to return a list in a top-level key or directly
        chats = None
        if isinstance(data, dict):
            # Common patterns: { 'data': [...], 'meta': {...} } or directly list
            if "data" in data and isinstance(data["data"], list):
                chats = data["data"]
            elif "chats" in data and isinstance(data["chats"], list):
                chats = data["chats"]
            elif isinstance(data.get("response"), dict) and isinstance(data["response"].get("result"), list):
                chats = data["response"]["result"]
            elif isinstance(data.get("items"), list):
                chats = data["items"]
            elif isinstance(data, list):
                chats = data
            else:
                # try to discover any list in the dict
                for v in data.values():
                    if isinstance(v, list):
                        chats = v
                        break
        elif isinstance(data, list):
            chats = data

        if not chats:
            print("No conversations found on page", page)
            break

        print(f"Found {len(chats)} conversations on page {page}")
        for conv in chats:
            # Try common id keys for conversation list
            conv_id = str(conv.get("conversation_id") or conv.get("id") or conv.get("conversationId") or conv.get("chat_id") or conv.get("id"))
            if not conv_id:
                # Some APIs return visitor id only
                print("Could not determine conversation id for entry, saving raw record")
                all_transcripts.append({"meta": conv, "transcript": None})
                continue
            if conv_id in processed_ids:
                # skip already processed conversation
                continue
            transcript = fetch_transcript(conv_id, limit=limit, from_time=from_time, to_time=to_time)
            record = {"conversation_id": conv_id, "meta": conv, "transcript": transcript}
            all_transcripts.append(record)
            processed_ids.add(conv_id)
            total_fetched += 1
            # be polite
            time.sleep(0.2)

            # shard save logic
            if shard_size > 0 and len(all_transcripts) >= shard_size:
                out_shard = os.path.join(OUT_DIR, f"raw_transcripts_salesiq_shard_{shard_index:04d}.json")
                with open(out_shard, "w", encoding="utf-8") as sf:
                    json.dump(all_transcripts, sf, indent=2, ensure_ascii=False)
                print(f"Saved shard {out_shard} ({len(all_transcripts)} records)")
                shard_index += 1
                saved_count += len(all_transcripts)
                all_transcripts = []
                # write resume file
                try:
                    with open(resume_file, "w", encoding="utf-8") as rf:
                        json.dump(list(processed_ids), rf)
                except Exception as e:
                    print(f"Warning: failed to write resume file: {e}")

            # optional max limit
            if max_chats and total_fetched >= max_chats:
                print(f"Reached requested max_chats={max_chats}")
                break

        # Pagination decisions: if returned less than page size, likely done
        if len(chats) < PAGE_SIZE:
            break
        page += 1

    # write remaining records in the current shard
    if all_transcripts:
        out_shard = os.path.join(OUT_DIR, f"raw_transcripts_salesiq_shard_{shard_index:04d}.json")
        with open(out_shard, "w", encoding="utf-8") as sf:
            json.dump(all_transcripts, sf, indent=2, ensure_ascii=False)
        print(f"Saved final shard {out_shard} ({len(all_transcripts)} records)")
        saved_count += len(all_transcripts)

    # write resume file final
    try:
        with open(resume_file, "w", encoding="utf-8") as rf:
            json.dump(list(processed_ids), rf)
    except Exception as e:
        print(f"Warning: failed to write resume file: {e}")

    print(f"Total transcripts saved across shards: {saved_count}")

    if ingest:
        # Try to call existing ingestion script if present
        ingest_script = os.path.join(PROJECT_ROOT, "scripts", "ingest_data.py")
        if os.path.exists(ingest_script):
            print("Calling existing ingestion pipeline to index transcripts into Chroma...")
            os.system(f"python \"{ingest_script}\" --source {out_path}")
        else:
            print("Ingest script not found; run scripts/ingest_data.py manually to index the file")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch SalesIQ closed chat transcripts and save to disk")
    parser.add_argument("--ingest", action="store_true", help="Call ingest_data.py after fetching to index into Chroma")
    parser.add_argument("--limit", type=int, default=None, help="limit per messages request (overrides env)")
    parser.add_argument("--from-time", dest="from_time", default=None, help="from_time (epoch ms) filter for conversations/messages")
    parser.add_argument("--to-time", dest="to_time", default=None, help="to_time (epoch ms) filter for conversations/messages")
    args = parser.parse_args()
    main(ingest=args.ingest, limit=args.limit, from_time=args.from_time, to_time=args.to_time)
