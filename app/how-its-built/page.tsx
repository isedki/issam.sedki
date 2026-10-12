import type { Metadata } from "next";
import { coverage, REPO, report, tests } from "@/lib/resume";

export const metadata: Metadata = {
  title: "How this resume is built · Issam Sedki",
  description: "The resume is code: one source file, a validator that blocks regressions, and planted mistakes that prove the validator works.",
};

const src = (path: string) => `${REPO}/blob/main/${path}`;

export default function HowItsBuilt() {
  const c = report.checked;
  return (
    <main className="page">
      <h1 style={{ fontSize: "clamp(2rem, 4.5vw, 2.8rem)", margin: "0 0 12px", letterSpacing: "-0.02em" }}>
        How this resume is built
      </h1>
      <p className="lede">
        I treat my resume like an LLM system: rewording it is cheap, and a small change can quietly break a fact.
        So it runs through the same discipline I use for agents. One source of truth, a validator that acts as the
        eval suite, and planted mistakes that prove the validator catches what it should.
      </p>

      <ol className="pipeline" aria-label="Pipeline">
        <li><strong>Source</strong><span><a href={src("resume/content.json")}><code>content.json</code></a> holds every word, once.</span></li>
        <li><strong>Build</strong><span>The same file generates this site and the Word resume.</span></li>
        <li><strong>Validate</strong><span>Checks facts, dates, numbers and technologies against approved sources.</span></li>
        <li><strong>Test the tests</strong><span>{tests.total} planted mistakes; each one must be caught.</span></li>
        <li><strong>Deploy</strong><span>GitHub Actions publishes only if every check passes.</span></li>
      </ol>

      <section className="section">
        <h2>What it checks</h2>
        <div>
          <div className="checks">
            <div className="check">
              <span className="n">{c.protected_facts}</span>
              <p>Facts from the original resume that must survive every rewrite: clients, metrics, degrees, certifications.</p>
            </div>
            <div className="check">
              <span className="n">{c.roles}</span>
              <p>Roles whose title, company and dates can never change, kept in reverse-chronological order.</p>
            </div>
            <div className="check">
              <span className="n">{c.technology_mentions}</span>
              <p>Technology mentions, each approved for that specific role with a source, and none older than the tool itself.</p>
            </div>
            <div className="check">
              <span className="n">{c.numbers}</span>
              <p>Numbers, each traced to the original resume or to a source such as git history or the test suite.</p>
            </div>
          </div>
          <p style={{ marginTop: 16 }}>
            Sources: <a href={src("resume/validate.py")}>validate.py</a> ·{" "}
            <a href={src("resume/facts/baseline.json")}>baseline facts</a> ·{" "}
            <a href={src("resume/facts/approved.json")}>approved additions</a>
          </p>
        </div>
      </section>

      <section className="section">
        <h2>Testing the tests</h2>
        <div>
          <p className="plain">
            A validator that always passes proves nothing. <a href={src("resume/test_validate.py")}>test_validate.py</a>{" "}
            plants one mistake at a time and checks that the validator fails with the right message.
            Result: <strong>{tests.caught} of {tests.total} caught</strong>.
          </p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Mistake</th><th>What was planted</th><th>Validator said</th><th>Result</th></tr></thead>
              <tbody>
                {tests.cases.map((t) => (
                  <tr key={t.name}>
                    <td>{t.name}</td>
                    <td>{t.planted}</td>
                    <td className="msg">{t.message}</td>
                    <td className={t.caught ? "ok" : "no"}>{t.caught ? "✓ caught" : "✗ missed"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Job fit</h2>
        <div>
          <p className="plain">
            The validator also scores the resume against the requirements of the role I&apos;m targeting
            (Senior AI Engineer, AI Systems): <strong>{coverage.covered} of {coverage.total} covered</strong>.
          </p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Requirement</th><th>Covered</th></tr></thead>
              <tbody>
                {report.coverage.map((r) => (
                  <tr key={r.requirement}>
                    <td>{r.requirement}</td>
                    <td className={r.covered ? "ok" : "no"}>{r.covered ? "✓ yes" : "✗ not yet"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Why it matters</h2>
        <div>
          <p className="plain">
            The resume was rewritten with an AI assistant. That is fast, but a model will happily turn 40% into 60% or
            add a framework I never used. The fix is the same as for any agent in production: don&apos;t trust the
            output, measure it. Every fact has a source, every change runs the suite, and a failing check blocks the
            deploy.
          </p>
          <p className="plain">
            Last run: <span className="mono">{report.result}</span>, {report.failures.length} failures
            {report.pages ? `, ${report.pages} pages (measured with ${report.pages_measured_with})` : ""}.
          </p>
        </div>
      </section>
    </main>
  );
}
