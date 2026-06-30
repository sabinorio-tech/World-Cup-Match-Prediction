from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "api_football"
BASE_URL = "https://v3.football.api-sports.io"
API_KEY_ENV = "API_FOOTBALL_KEY"


def get_api_key() -> str | None:
    """Load the API-Football token from the project .env file."""
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv(API_KEY_ENV)
    return api_key.strip() if api_key else None


class ApiFootballClient:
    """Small API-Football v3 client for proof-of-concept data pulls."""

    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL) -> None:
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise ValueError(f"Missing {API_KEY_ENV} environment variable.")
        self.base_url = base_url.rstrip("/")

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        endpoint = endpoint.strip("/")
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(
            url,
            headers={"x-apisports-key": self.api_key},
            params=params or {},
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"API-Football request failed for /{endpoint} "
                f"with status {response.status_code}: {response.text[:300]}"
            )
        return response.json()


def save_json(data: dict[str, Any], filename: str, output_dir: Path = RAW_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    print(f"Saved: {output_path}")
    return output_path


def load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
