from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from zipfile import ZipFile

from common import REPORT_DIR


FORBIDDEN_PREFIXES = [
    "frontend/node_modules/",
    "frontend/dist/",
    "frontend/unpackage/dist/",
    "backend/__pycache__/",
    "backend/.venv/",
    "backend/venv/",
    ".idea/",
    ".vscode/",
    ".git/",
]

FORBIDDEN_CONTAINS = [
    "/__pycache__/",
    "/.venv/",
    "/venv/",
]

FORBIDDEN_EXACT = {
    ".env",
    ".DS_Store",
    "Thumbs.db",
    "backend/fantasy_role_ai.db",
}

REQUIRED_PREFIXES = [
    "backend/",
    "frontend/",
    "docs/",
    "tests/",
    "scripts/",
]

REQUIRED_FILES = [
    "README.md",
    "VERSION.md",
    ".gitignore",
    ".env.example",
    "docs/MVP交付说明.md",
    "docs/甲方验收清单.md",
    "docs/开发者继续开发指南.md",
    "docs/部署前检查清单.md",
    "docs/自动化测试与回归验收设计.md",
    "tests/README.md",
    "tests/run_backend_smoke.py",
    "tests/run_project_isolation.py",
    "tests/run_safety_checks.py",
    "tests/run_candidate_extraction_checks.py",
    "tests/run_llm_first_script_understanding_checks.py",
    "tests/run_prompt_template_checks.py",
    "tests/run_package_check.py",
    "tests/test_data/sample_script.txt",
    "tests/test_data/sample_script_b.txt",
    "tests/test_data/sample_upload.txt",
    "scripts/dev_backend.bat",
    "scripts/dev_backend.sh",
    "scripts/dev_frontend_h5.bat",
    "scripts/dev_frontend_h5.sh",
    "scripts/run_tests.bat",
    "scripts/run_tests.sh",
    "scripts/package_check.sh",
]

ALLOWED_UPLOAD_ENTRY = "backend/app/uploads/.gitkeep"
HIGH_RISK_NAME_MARKERS = ("secret", "key", "token", "password")
HIGH_RISK_CONFIG_SUFFIXES = (".txt", ".json", ".env", ".yaml", ".yml")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check delivery zip safety.")
    parser.add_argument("--zip", required=True, help="Path to delivery zip file")
    args = parser.parse_args()
    zip_path = Path(args.zip)
    if not zip_path.exists():
        raise SystemExit(f"Zip not found: {zip_path}")

    failures: list[dict[str, str]] = []
    with ZipFile(zip_path) as zf:
        names = zf.namelist()

    for prefix in FORBIDDEN_PREFIXES:
        matches = [name for name in names if name.startswith(prefix)]
        if matches:
            failures.append({"check": f"forbidden prefix {prefix}", "detail": matches[0]})

    for needle in FORBIDDEN_CONTAINS:
        matches = [name for name in names if needle in name]
        if matches:
            failures.append({"check": f"forbidden path segment {needle}", "detail": matches[0]})

    for exact in FORBIDDEN_EXACT:
        if exact in names:
            failures.append({"check": f"forbidden file {exact}", "detail": exact})

    for name in names:
        basename = Path(name).name
        lower_basename = basename.lower()
        if name.endswith(".env") or name.endswith(".pyc") or name.endswith(".pyo"):
            failures.append({"check": "forbidden sensitive/cache suffix", "detail": name})
        if basename in {".DS_Store", "Thumbs.db"}:
            failures.append({"check": "forbidden system cache file", "detail": name})
        if (
            name != ".env.example"
            and lower_basename.endswith(HIGH_RISK_CONFIG_SUFFIXES)
            and any(marker in lower_basename for marker in HIGH_RISK_NAME_MARKERS)
        ):
            failures.append({"check": "high-risk secret-like config filename", "detail": name})
        if name.startswith("backend/app/uploads/") and name != ALLOWED_UPLOAD_ENTRY:
            failures.append({"check": "real uploaded file included", "detail": name})
        if name.startswith("tests/reports/"):
            failures.append({"check": "test report directory included", "detail": name})

    for prefix in REQUIRED_PREFIXES:
        if not any(name.startswith(prefix) for name in names):
            failures.append({"check": f"required prefix {prefix}", "detail": "missing"})

    for file_name in REQUIRED_FILES:
        if file_name not in names:
            failures.append({"check": f"required file {file_name}", "detail": "missing"})

    total_checks = (
        len(FORBIDDEN_PREFIXES)
        + len(FORBIDDEN_CONTAINS)
        + len(FORBIDDEN_EXACT)
        + len(REQUIRED_PREFIXES)
        + len(REQUIRED_FILES)
        + 4
    )
    report = {
        "name": "package_check",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "zip": str(zip_path),
        "total": total_checks,
        "passed": max(total_checks - len(failures), 0),
        "failed": len(failures),
        "failed_cases": failures,
        "entry_count": len(names),
        "has_upload_gitkeep": ALLOWED_UPLOAD_ENTRY in names,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "package_check_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if failures:
        print("[FAIL] Package check failed")
        for failure in failures:
            print(f"  - {failure['check']}: {failure['detail']}")
        print(f"Report written: {report_path}")
        return 1

    print("[PASS] Package check passed")
    print(f"Report written: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
