import json
from pathlib import Path


def normalize_email(email: str) -> str:
    return email.strip().lower()


def save_payload(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
