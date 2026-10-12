# Issam Sedki — resume as code

My resume is a small software project. One source file generates both the website and the Word resume,
and a validator blocks any change that breaks a fact. It is the same discipline I use for LLM agents:
don't trust generated output, measure it.

## How it works

```
resume/content.json ──► build.js ──► Word resume (.docx)
        │                └────────► website (Next.js)
        ▼
validate.py ── facts/baseline.json   facts from the original resume that must survive every rewrite
        │   └─ facts/approved.json   every addition (technology, number) with its source
        ▼
test_validate.py   plants 15 mistakes and checks that each one is caught
        ▼
GitHub Actions     deploys to Vercel only when everything passes
```

The validator fails when:

- a protected fact disappears (client, metric, degree, certification)
- a role's title, company or dates change, or roles fall out of order
- a technology appears that isn't approved for that specific role, or is older than the tool itself
- a number appears without a source
- the resume is longer than 2 pages

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r resume/requirements.txt
npm install
npm run resume:check   # build, validate, and test the validator
npm run dev            # site on http://localhost:3000
```

On macOS with Microsoft Word installed, the page count is measured by Word. In CI it is measured with
LibreOffice and Carlito, a font metric-compatible with Calibri.

`resume/line_fit.py` (macOS + Word fonts) shows which paragraphs spill onto an extra line, to help keep the
resume at 2 pages.
