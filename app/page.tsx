import Link from "next/link";
import { coverage, report, resume, splitOrg, splitStack, tests, type Project, type Role } from "@/lib/resume";

function Contact({ line }: { line: string }) {
  const parts = line.split(" | ");
  return (
    <p className="contact">
      {parts.map((p, i) => (
        <span key={p}>
          {i > 0 && " · "}
          <a href={p.includes("@") ? `mailto:${p}` : `https://${p}`}>{p}</a>
        </span>
      ))}
    </p>
  );
}

function Stack({ stack }: { stack?: string }) {
  if (!stack) return null;
  return (
    <ul className="chips" aria-label="Stack">
      {splitStack(stack).map((s) => <li key={s}>{s}</li>)}
    </ul>
  );
}

function RoleEntry({ role }: { role: Role }) {
  const { company, detail } = splitOrg(role.org);
  return (
    <article className="role">
      <div className="role-head">
        <h3>{role.title}</h3>
        <span className="dates">{role.dates}</span>
      </div>
      <p className="org"><strong>{company}</strong>{detail && ` · ${detail}`}</p>
      <Stack stack={role.stack} />
      {role.bullets && <ul>{role.bullets.map((b) => <li key={b}>{b}</li>)}</ul>}
    </article>
  );
}

function ProjectEntry({ project }: { project: Project }) {
  return (
    <article className="project">
      <div className="role-head">
        <h3>{project.title}</h3>
        {project.dates && <span className="dates">{project.dates}</span>}
      </div>
      <div style={{ height: 10 }} />
      <Stack stack={project.stack} />
      <ul>{project.bullets.map((b) => <li key={b}>{b}</li>)}</ul>
    </article>
  );
}

export default function Home() {
  const r = resume;
  return (
    <main className="page">
      <section className="hero">
        <div>
          <h1>{r.name}</h1>
          <p className="headline">{r.headline}</p>
          <Contact line={r.contact} />
          <p className="summary">{r.summary}</p>
        </div>
        <aside className="status" aria-labelledby="status-title">
          <h2 id="status-title">Last validation</h2>
          <span className={`pill ${report.result === "PASS" ? "" : "fail"}`}>
            {report.result === "PASS" ? "✓ PASS" : "✗ FAIL"}
          </span>
          <dl>
            <div><dt>Facts protected</dt><dd>{report.checked.protected_facts}</dd></div>
            <div><dt>Planted regressions caught</dt><dd>{tests.caught}/{tests.total}</dd></div>
            <div><dt>Job requirements covered</dt><dd>{coverage.covered}/{coverage.total}</dd></div>
            {report.pages && <div><dt>Pages</dt><dd>{report.pages}/{report.max_pages}</dd></div>}
          </dl>
          <Link href="/how-its-built">How this resume is tested →</Link>
        </aside>
      </section>

      <section className="section">
        <h2>Key achievements</h2>
        <ul>{r.achievements.map((a) => <li key={a}>{a}</li>)}</ul>
      </section>

      <section className="section">
        <h2>AI projects</h2>
        <div>{r.projects.map((p) => <ProjectEntry key={p.key} project={p} />)}</div>
      </section>

      <section className="section">
        <h2>Experience</h2>
        <div>{r.experience.map((e) => <RoleEntry key={e.key} role={e} />)}</div>
      </section>

      <section className="section">
        <h2>Skills</h2>
        <dl className="skills">
          {r.skills.map(([label, text]) => (
            <div key={label}><dt>{label}</dt><dd>{text}</dd></div>
          ))}
        </dl>
      </section>

      <section className="section">
        <h2>Education</h2>
        <ul>{r.education.map((e) => <li key={e}>{e}</li>)}</ul>
      </section>

      <section className="section">
        <h2>Certifications</h2>
        <div>
          <p className="plain">{r.certifications}</p>
          <p className="plain"><strong>Languages:</strong> {r.languages}</p>
        </div>
      </section>
    </main>
  );
}
