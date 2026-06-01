#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
echo "Please start the backend first: scripts/dev_backend.sh"
python tests/run_backend_smoke.py
python tests/run_project_isolation.py
python tests/run_safety_checks.py
python tests/run_candidate_extraction_checks.py
python tests/run_llm_first_script_understanding_checks.py
python tests/run_prompt_template_checks.py
echo "All backend regression tests passed."
