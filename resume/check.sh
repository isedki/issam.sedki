#!/bin/sh
# Builds the resume, validates it, and proves the validator still catches planted regressions.
# Writes resume/validation.json and resume/regressions.json, which the website displays.
set -e
cd "$(dirname "$0")/.."
PY=${PYTHON:-$([ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)}
DOCX=resume/Issam_Sedki_Resume_EN_AI_Engineer.docx

node resume/build.js "$DOCX"
PAGES=""
if command -v soffice >/dev/null 2>&1; then   # CI: measure pages with LibreOffice (+ Carlito, metric-compatible with Calibri)
  soffice --headless --convert-to pdf --outdir resume "$DOCX" >/dev/null
  PAGES="--pdf ${DOCX%.docx}.pdf"
fi
$PY resume/validate.py "$DOCX" $PAGES --json resume/validation.json
$PY resume/test_validate.py --json resume/regressions.json
