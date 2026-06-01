from functools import lru_cache
from pathlib import Path


PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


@lru_cache(maxsize=16)
def load_prompt_template(name: str) -> str:
    path = PROMPT_DIR / name
    return path.read_text(encoding="utf-8")
