// Typed access to the resume pipeline's files. The site and the Word file read the same content.json.
import content from "@/resume/content.json";
import validation from "@/resume/validation.json";
import regressions from "@/resume/regressions.json";

export type Role = {
  key: string;
  title: string;
  dates: string;
  org: string;
  stack?: string;
  bullets?: string[];
};

export type Project = {
  key: string;
  title: string;
  dates: string;
  stack?: string;
  bullets: string[];
};

export type Resume = {
  name: string;
  headline: string;
  contact: string;
  summary: string;
  achievements: string[];
  skills: [string, string][];
  projects: Project[];
  experience: Role[];
  education: string[];
  certifications: string;
  languages: string;
};

export type Validation = {
  result: "PASS" | "FAIL";
  failures: string[];
  warnings: string[];
  pages: number | null;
  max_pages: number;
  pages_measured_with: string | null;
  checked: { protected_facts: number; roles: number; technology_mentions: number; numbers: number };
  coverage: { requirement: string; covered: boolean }[];
};

export type Regressions = {
  caught: number;
  total: number;
  cases: { name: string; planted: string; caught: boolean; message: string }[];
};

export const resume = content as Resume;
export const report = validation as Validation;
export const tests = regressions as Regressions;

export const REPO = "https://github.com/isedki/issam.sedki";
export const DOCX = "/Issam_Sedki_Resume.docx";

/** "a, b, c (d, e)" -> ["a", "b", "c (d, e)"]: split a stack line on top-level commas only. */
export function splitStack(stack: string): string[] {
  const out: string[] = [];
  let depth = 0;
  let cur = "";
  for (const ch of stack) {
    if (ch === "(") depth++;
    if (ch === ")") depth--;
    if (ch === "," && depth === 0) {
      out.push(cur.trim());
      cur = "";
    } else cur += ch;
  }
  if (cur.trim()) out.push(cur.trim());
  return out;
}

/** Splits "Company | detail | detail" into the company and the rest. */
export function splitOrg(org: string): { company: string; detail: string } {
  const [company, ...rest] = org.split(" | ");
  return { company, detail: rest.join(" · ") };
}

export const coverage = {
  covered: report.coverage.filter((c) => c.covered).length,
  total: report.coverage.length,
};
