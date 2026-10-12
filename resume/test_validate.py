"""Proves the validator catches regressions: each case plants one mistake and expects a specific failure.

Usage: python test_validate.py [--json results.json]
"""
import argparse, copy, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
CONTENT = json.loads((HERE / "content.json").read_text())


def exp(c, key):
    return next(e for e in c["experience"] if e["key"] == key)


def replace_in(c, key, old, new):
    e = exp(c, key)
    e["bullets"] = [b.replace(old, new) for b in e["bullets"]]


# (name, the mistake planted, how to plant it, text the validator must report)
CASES = [
    ("Changed date", "IBM start date moved from 2018 to 2017",
     lambda c: exp(c, "ibm").update(dates="01/2017 – 08/2020"), "Role header changed"),
    ("Inflated metric", "Guide to Iceland cost cut raised from 40% to 60%",
     lambda c: replace_in(c, "hygraph", "40% cut", "60% cut"), "Missing metrics fact: \"40%\""),
    ("Dropped client", "ExxonMobil replaced by \"Energy client\"",
     lambda c: replace_in(c, "ibm", "ExxonMobil: end", "Energy client: end"), "Missing clients fact: \"ExxonMobil\""),
    ("Invented framework", "LangGraph added to the Hygraph stack",
     lambda c: exp(c, "hygraph").update(stack=exp(c, "hygraph")["stack"] + ", LangGraph"), "not approved for hygraph"),
    ("Technology in the wrong role", "Claude Agent SDK added to IBM (2018–2020)",
     lambda c: exp(c, "ibm").update(stack="Kubernetes, Claude Agent SDK"), "not approved for ibm"),
    ("Invented skill", "\"RAG with Pinecone\" added to skills",
     lambda c: c["skills"][0].__setitem__(1, c["skills"][0][1] + " RAG with Pinecone."), "Unapproved technology"),
    ("Unsourced number", "\"Served 3,000,000 requests per day\" added",
     lambda c: c["achievements"].append("Served 3,000,000 requests per day."), "New number '3,000,000'"),
    ("Roles out of order", "IBM moved to the top of the experience list",
     lambda c: c["experience"].insert(0, c["experience"].pop(3)), "reverse-chronological"),
    ("Certification dropped", "PMI-ACP removed",
     lambda c: c.__setitem__("certifications", c["certifications"].replace("PMI-ACP, ", "")), "PMI-ACP"),
    ("Plural slips through", "\"vector stores\" added to IBM",
     lambda c: exp(c, "ibm").update(stack="Kubernetes, vector stores"), "not approved for ibm"),
    ("Framework in a project", "LangChain added to the Moroccan law RAG project",
     lambda c: c["projects"][1]["bullets"].append("Orchestrated with LangChain."), "not approved for lawrag"),
    ("Removed technology returns", "Electron added back to Pilote Billing",
     lambda c: c["projects"][0].update(stack=c["projects"][0]["stack"] + ", Electron"), "asked to remove"),
    ("Old stack in an AI role", "Struts added to Hygraph",
     lambda c: exp(c, "hygraph").update(stack=exp(c, "hygraph")["stack"] + ", Struts"), "not approved for hygraph"),
    ("Anachronism", "Kubernetes (2014) added to Amadeus (2004–2007)",
     lambda c: exp(c, "amadeus").update(stack="Java, Kubernetes"), "released 2014"),
    ("Placeholder left in", "\"TODO add numbers\" added",
     lambda c: c["achievements"].append("TODO add numbers"), "Placeholder"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="also write the results to this path")
    a = ap.parse_args()

    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, planted, mutate, expected in CASES:
            c = copy.deepcopy(CONTENT)
            mutate(c)
            cj, dx = Path(tmp, "c.json"), Path(tmp, "r.docx")
            cj.write_text(json.dumps(c, ensure_ascii=False))
            subprocess.run(["node", str(HERE / "build.js"), str(dx), str(cj)], check=True, capture_output=True)
            r = subprocess.run([sys.executable, str(HERE / "validate.py"), str(dx), "--no-word",
                                "--report", str(Path(tmp, "r.md"))], capture_output=True, text=True)
            caught = r.returncode == 1 and expected in r.stdout
            message = next((l.strip()[5:] for l in r.stdout.splitlines() if expected in l), "")
            results.append({"name": name, "planted": planted, "caught": caught, "message": message})
            print(f"{'caught ' if caught else 'MISSED '} {name}")
            if not caught:
                print(r.stdout)

    n = sum(r["caught"] for r in results)
    print(f"\n{n}/{len(results)} planted regressions caught")
    if a.json:
        Path(a.json).write_text(json.dumps({"caught": n, "total": len(results), "cases": results},
                                           indent=2, ensure_ascii=False) + "\n")
    sys.exit(0 if n == len(results) else 1)


if __name__ == "__main__":
    main()
