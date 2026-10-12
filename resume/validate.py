"""Regression checks for the resume.

Usage: python validate.py RESUME.docx [--pdf RESUME.pdf] [--report validation_report.md]

FAIL (exit 1)  a protected fact disappeared, a role's title/company/dates changed or moved,
               a technology or number appears that is not in facts/approved.json or the baseline,
               or the resume is longer than 2 pages.
WARN           a technology you have not confirmed yet ("assumed"), or the page count could not be measured.
INFO           what changed against the baseline, and how well the job description is covered.
"""
import argparse, difflib, json, re, sys, unicodedata
from pathlib import Path

from docx import Document

HERE = Path(__file__).parent
BASE = json.loads((HERE / "facts/baseline.json").read_text())
APPR = json.loads((HERE / "facts/approved.json").read_text())
BASELINE_TEXT = (HERE / "baseline_resume.txt").read_text()
MAX_PAGES = 2

HEADINGS = {"SUMMARY", "KEY ACHIEVEMENTS", "SKILLS", "SELECTED AI PROJECT", "SELECTED AI PROJECTS",
            "PROFESSIONAL EXPERIENCE", "EDUCATION AND TEACHING", "CERTIFICATIONS AND LANGUAGES"}

# Technologies the validator knows about. Anything here that shows up must be approved for that section.
TECH = ["Claude Agent SDK", "Claude Code", "Claude", "Sonnet", "Haiku", "Opus", "OpenAI", "GPT", "Gemini", "Llama", "Mistral",
        "LangGraph", "LangChain", "LlamaIndex", "CrewAI", "AutoGen", "Semantic Kernel", "Cursor", "GitHub Copilot",
        "FastMCP", "MCP", "RAG", "vector store", "vector database", "embeddings", "Pinecone", "Weaviate", "Qdrant", "pgvector",
        "Chroma", "Langfuse", "LangSmith", "OpenTelemetry", "Datadog", "Grafana", "Prometheus", "Hugging Face",
        "PyTorch", "TensorFlow", "scikit-learn", "BERT", "LogPAI", "whisper.cpp",
        "TypeScript", "JavaScript", "Python", "Java", "PHP", "Rust", "C#", ".NET", "Kotlin", "Scala",
        "Next.js", "Node.js", "React", "Angular", "Vue", "Express", "NestJS", "FastAPI", "Django", "Flask", "Spring",
        "Electron", "WordPress", "Drupal", "AEM", "GraphQL", "REST",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Aurora", "DynamoDB", "Elasticsearch", "SQL",
        "Snowflake", "BigQuery", "Databricks", "Kafka", "Spark",
        "AWS", "Azure", "GCP", "Google Cloud", "Vercel", "Fastly", "Cloudflare",
        "Docker", "Terraform", "Helm", "Kubernetes", "Ansible", "Jenkins", "GitHub Actions", "GitLab",
        "Zod", "Vitest", "Jest", "Playwright", "Cypress", "Selenium", "Gherkin", "TDD", "BDD",
        "NLP", "Cost Explorer", "J2EE", "Struts", "Hibernate", "Maven", "API-native",
        "PeopleSoft", "SAP", "OSS", "BSS", "Intelligent Network"]
TECH.sort(key=len, reverse=True)  # longest first, so "Claude Code" wins over "Claude"

# First public release year. A role that ended before this year can't have used the technology.
SINCE = {"Cypress": 2015, "Next.js": 2016, "Vercel": 2015, "TypeScript": 2012, "React": 2013, "Node.js": 2009,
         "Kubernetes": 2014, "Ansible": 2012, "GitHub Actions": 2019, "Spring": 2003, "Maven": 2004, "Hibernate": 2001,
         "J2EE": 1999, "Struts": 2000, "Gherkin": 2008, "BDD": 2006, "Claude": 2023, "Claude Code": 2025,
         "Claude Agent SDK": 2025, "MCP": 2024, "FastMCP": 2024, "Cursor": 2023, "GitHub Copilot": 2021,
         "OpenAI": 2020, "BERT": 2018, "PyTorch": 2016, "Fastly": 2011, "Aurora": 2014, "Cost Explorer": 2014,
         "GraphQL": 2015, "Zod": 2020, "LogPAI": 2016}

JD = [  # (requirement, list of alternatives; each alternative is a list of terms that must all appear)
    ("6+ years of experience", [["22 years"]]),
    ("Deploys a full app alone (front end, back end, DevOps)", [["React", "Node.js", "GitHub Actions"], ["Next.js", "Vercel", "AWS"]]),
    ("Production app at scale", [["100,000"], ["lower latency"]]),
    ("AI SDLC in production (AI coding tools)", [["Claude Code"], ["Cursor"], ["GitHub Copilot"]]),
    ("Prompt design", [["prompt"]]),
    ("Function / tool calling", [["tool calling"], ["tools"]]),
    ("Structured outputs", [["structured outputs"], ["valid JSON"]]),
    ("RAG", [["RAG"], ["retrieval"]]),
    ("Vector stores", [["vector"], ["embeddings"]]),
    ("Anthropic API", [["Claude"]]),
    ("OpenAI API", [["OpenAI"], ["GPT"]]),
    ("Evals as a core habit", [["eval"], ["LLM reviewer", "quality score"]]),
    ("Agentic systems end to end (plan, code, self-validate)", [["agents", "fail, fix"]]),
    ("Orchestration frameworks", [["LangGraph"], ["LlamaIndex"], ["AutoGen"], ["CrewAI"], ["Claude Agent SDK"]]),
    ("Opinion on frameworks vs thin harness", [["custom harness"], ["thin harness"]]),
    ("Reliability, cost control, observability", [["traced", "cost"], ["tracing", "cost"]]),
    ("Cloud data platform + SQL", [["SQL", "BigQuery"], ["SQL", "Snowflake"], ["SQL", "Databricks"], ["SQL", "Aurora"]]),
]


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("–", "-").replace("—", "-").replace("’", "'").replace("\t", " ")
    return re.sub(r"\s+", " ", s).strip().lower()


def docx_lines(path):
    return [p.text for p in Document(path).paragraphs if p.text.strip()]


def segment(lines):
    """Tag each line with the section it belongs to: a role key, a project key, 'phd', or 'global'."""
    roles = BASE["roles"]
    projects = APPR.get("projects", {})  # key -> text that identifies the project's header line
    tagged, section, key = [], "", "global"
    for line in lines:
        up = line.strip().upper()
        if up in HEADINGS:
            section, key = up, ("phd" if up.startswith("EDUCATION") else "global")
            tagged.append((key, line)); continue
        if section == "PROFESSIONAL EXPERIENCE":
            for r in roles:
                if norm(r["dates"]) in norm(line) and norm(line).startswith(norm(r["title"])):
                    key = r["key"]
        elif section.startswith("SELECTED AI PROJECT"):
            key = next((k for k, name in projects.items() if norm(name) in norm(line)), key)
        tagged.append((key, line))
    return tagged


def find_tech(text):
    found, masked = [], text
    for t in TECH:
        pat = r"(?<![\w.])" + re.escape(t) + r"s?(?![\w])"
        if re.search(pat, masked):
            found.append(t)
            masked = re.sub(pat, " ", masked)
    return found


def numbers(text):
    return set(re.findall(r"\d+(?:[,.]\d+)*", text))


def word_pages(docx_path):
    """Page count as laid out by Microsoft Word (macOS). Returns None if Word is unavailable."""
    import shutil, subprocess, uuid
    box = Path.home() / "Library/Containers/com.microsoft.Word/Data/Documents"
    if not box.exists():
        return None
    tmp = box / f"resume-check-{uuid.uuid4().hex[:8]}.docx"
    shutil.copy(docx_path, tmp)
    script = f'''tell application "Microsoft Word"
        open POSIX file "{tmp}"
        set d to document "{tmp.name}"
        set n to compute statistics d statistic statistic pages
        close d saving no
        return n
    end tell'''
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=120)
        return int(r.stdout.strip()) if r.returncode == 0 else None
    except (subprocess.TimeoutExpired, ValueError):
        return None
    finally:
        tmp.unlink(missing_ok=True)
        (box / ("~$" + tmp.name[2:])).unlink(missing_ok=True)  # Word's lock file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("resume")
    ap.add_argument("--pdf")
    ap.add_argument("--report", default=str(HERE / "validation_report.md"))
    ap.add_argument("--no-word", action="store_true", help="skip the page count through Microsoft Word")
    ap.add_argument("--json", help="also write a JSON summary to this path")
    a = ap.parse_args()

    lines = docx_lines(a.resume)
    full = "\n".join(lines)
    nfull = norm(full)
    fails, warns, infos = [], [], []
    removals = {norm(x["fact"]) for x in BASE["allowed_removals"]}

    # 1. Protected facts
    for cat in ["identity", "summary", "clients", "metrics", "claims", "education", "certifications", "languages"]:
        for fact in BASE[cat]:
            if norm(fact) not in nfull and norm(fact) not in removals:
                fails.append(f"Missing {cat} fact: \"{fact}\"")

    # 2. Roles: title, company, dates unchanged and in the same order
    positions = []
    for r in BASE["roles"]:
        idx = next((i for i, l in enumerate(lines)
                    if norm(r["dates"]) in norm(l) and norm(l).startswith(norm(r["title"]))), None)
        if idx is None:
            fails.append(f"Role header changed or missing: {r['title']} ({r['dates']})"); continue
        if not any(norm(r["company"]) in norm(l) for l in lines[idx:idx + 2]):
            fails.append(f"Company '{r['company']}' not right under {r['title']} ({r['dates']})")
        positions.append(idx)
    if positions != sorted(positions):
        fails.append("Roles are no longer in reverse-chronological order")

    # 3. Technologies, per section
    approved_any = {}
    for key, v in APPR["tech"].items():
        for t in v["confirmed"]: approved_any.setdefault(t, set()).add("confirmed")
        for t in v["assumed"]: approved_any.setdefault(t, set()).add("assumed")
    base_seg = {}
    for key, line in segment(BASELINE_TEXT.splitlines()):
        base_seg.setdefault(key, set()).update(find_tech(line))
    base_all = set(find_tech(BASELINE_TEXT))
    assumed = {}  # section -> technologies still waiting for your confirmation
    for key, line in segment(lines):
        for t in find_tech(line):
            if key == "global":
                if t in base_all or "confirmed" in approved_any.get(t, set()):
                    continue
                if "assumed" not in approved_any.get(t, set()):
                    fails.append(f"Unapproved technology '{t}' in: \"{line[:90]}…\""); continue
                section = "summary or skills"
            else:
                appr = APPR["tech"].get(key, {"confirmed": {}, "assumed": {}})
                if t in appr["confirmed"] or t in base_seg.get(key, set()):
                    continue
                if t not in appr["assumed"]:
                    fails.append(f"Technology '{t}' is not approved for {key}: \"{line[:90]}…\""); continue
                section = key
            assumed.setdefault(section, [])
            if t not in assumed[section]:
                assumed[section].append(t)
    for section, techs in assumed.items():
        warns.append(f"Please confirm for {section}: {', '.join(techs)}")

    # 3a. Timeline: no technology in a role that ended before it was released
    end_year = {r["key"]: int(r["dates"][-4:]) for r in BASE["roles"]}
    for key, line in segment(lines):
        for t in find_tech(line):
            if key in end_year and SINCE.get(t, 0) > end_year[key]:
                fails.append(f"'{t}' (released {SINCE[t]}) listed under {key}, which ended in {end_year[key]}")

    # 3b. Technologies you asked to remove
    for t in APPR.get("removed", {}):
        if t in find_tech(full):
            fails.append(f"'{t}' is back, but you asked to remove it")

    # 4. Numbers: nothing new unless approved
    allowed_nums = numbers(BASELINE_TEXT) | numbers(" ".join(APPR["numbers"]))
    for n in sorted(numbers(full) - allowed_nums):
        ctx = next(l for l in lines if n in l)
        fails.append(f"New number '{n}' not in baseline or approved list: \"{ctx[:90]}…\"")

    # 5. Length
    pages, source = None, ""
    if a.pdf:
        import pdfplumber
        with pdfplumber.open(a.pdf) as pdf:
            pages, source = len(pdf.pages), "PDF"
    elif not a.no_word:
        pages, source = word_pages(a.resume), "Microsoft Word"
    if pages is None:
        warns.append("Page count not measured (give --pdf, or install Microsoft Word)")
    else:
        (fails if pages > MAX_PAGES else infos).append(f"Page count: {pages} (limit {MAX_PAGES}, measured with {source})")

    # 6. Hygiene
    for i, l in enumerate(lines):
        if re.search(r"\b(TODO|TBD|lorem|XXX)\b", l, re.I): fails.append(f"Placeholder text: \"{l[:80]}\"")
        if "  " in l.replace("\t", " "): warns.append(f"Double space: \"{l[:80]}\"")

    # 7. Diff against the baseline (informational)
    base_lines = [l for l in BASELINE_TEXT.splitlines() if len(l) > 40]
    new_norm = [norm(l) for l in lines]
    reworded = []
    for bl in base_lines:
        nb = norm(bl)
        if any(nb in nl for nl in new_norm): continue
        best = max(difflib.SequenceMatcher(None, nb, nl).ratio() for nl in new_norm)
        reworded.append((best, bl))
    added = [l for l in lines if len(l) > 40 and
             max(difflib.SequenceMatcher(None, norm(l), norm(b)).ratio() for b in base_lines) < 0.6]

    # 8. Job description coverage
    cov = []
    for req, alts in JD:
        ok = any(all(norm(t) in nfull for t in alt) for alt in alts)
        cov.append((req, ok))

    # Report
    out = ["# Resume validation report", "", f"File: `{Path(a.resume).name}`", "",
           f"**Result: {'FAIL' if fails else 'PASS'}** — {len(fails)} failure(s), {len(warns)} warning(s)", ""]
    out += ["## Failures", ""] + ([f"- {f}" for f in fails] or ["- None"]) + [""]
    out += ["## Warnings", ""] + ([f"- {w}" for w in warns] or ["- None"]) + [""]
    out += ["## Info", ""] + [f"- {i}" for i in infos] + [""]
    out += ["## Job description coverage", "", "| Requirement | Covered |", "|---|---|"]
    out += [f"| {r} | {'yes' if ok else '**no**'} |" for r, ok in cov] + [""]
    out += ["## Baseline lines that were reworded", "",
            "Wrapped or edited lines from the original PDF. Protected facts are checked separately above.", ""]
    out += [f"- ({s:.0%} similar) {l}" for s, l in sorted(reworded)] + [""]
    out += ["## New content", ""] + [f"- {l}" for l in added] + [""]
    Path(a.report).write_text("\n".join(out))

    if a.json:  # machine-readable summary, shown on the website
        fact_cats = ["identity", "summary", "clients", "metrics", "claims", "education", "certifications", "languages"]
        Path(a.json).write_text(json.dumps({
            "result": "FAIL" if fails else "PASS",
            "failures": fails,
            "warnings": warns,
            "pages": pages, "max_pages": MAX_PAGES, "pages_measured_with": source or None,
            "checked": {
                "protected_facts": sum(len(BASE[c]) for c in fact_cats),
                "roles": len(BASE["roles"]),
                "technology_mentions": sum(len(find_tech(l)) for l in lines),
                "numbers": len(numbers(full)),
            },
            "coverage": [{"requirement": r, "covered": ok} for r, ok in cov],
        }, indent=2, ensure_ascii=False) + "\n")

    print(f"{'FAIL' if fails else 'PASS'}: {len(fails)} failure(s), {len(warns)} warning(s)")
    for f in fails: print("  FAIL", f)
    for w in warns: print("  WARN", w)
    for i in infos: print("  INFO", i)
    print("  Coverage:", sum(ok for _, ok in cov), "/", len(cov), "requirements;",
          "missing:", ", ".join(r for r, ok in cov if not ok) or "none")
    print("  Report:", a.report)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
