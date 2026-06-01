@echo off
setlocal
cd /d "%~dp0\.."
echo Please start the backend first: scripts\dev_backend.bat
python tests\run_backend_smoke.py || exit /b 1
python tests\run_project_isolation.py || exit /b 1
python tests\run_safety_checks.py || exit /b 1
python tests\run_candidate_extraction_checks.py || exit /b 1
python tests\run_llm_first_script_understanding_checks.py || exit /b 1
python tests\run_prompt_template_checks.py || exit /b 1
echo All backend regression tests passed.
