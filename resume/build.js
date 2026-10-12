// Builds the AI-targeted resume (.docx) from content.json.
// Layout matches the current resume: A4, Calibri 10pt, 0.5" margins.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, TabStopType, LevelFormat, BorderStyle, AlignmentType,
} = require("docx");

// Usage: node build.js [out.docx] [content.json]
const c = JSON.parse(fs.readFileSync(process.argv[3] || path.join(__dirname, "content.json"), "utf8"));
const out = process.argv[2] || path.join(__dirname, "Issam_Sedki_Resume_EN_AI_Engineer.docx");

const MARGIN = 720;                 // 0.5"
const TEXT_WIDTH = 11906 - 2 * MARGIN;
const pt = (n) => n * 2;            // docx sizes are half-points
const after = (n) => ({ spacing: { after: n * 20, before: 0 } });

const run = (text, o = {}) => new TextRun({ text, font: "Calibri", size: pt(o.size || 10), bold: o.bold, italics: o.italics });

const heading = (text) => new Paragraph({
  children: [run(text.toUpperCase(), { bold: true, size: 11 })],
  spacing: { before: 100, after: 30 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "808080", space: 1 } },
});

const bullet = (children) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: typeof children === "string" ? [run(children)] : children,
  ...after(0.5),
});

const labelled = (label, text) => bullet([run(label + ": ", { bold: true }), run(text)]);

const roleHeader = (title, dates) => new Paragraph({
  tabStops: [{ type: TabStopType.RIGHT, position: TEXT_WIDTH }],
  children: [run(title, { bold: true, size: 10.5 }), run("\t" + dates, { bold: true, size: 10 })],
  spacing: { before: 70, after: 0 },
  keepNext: true,
});

const italicLine = (text) => new Paragraph({ children: [run(text, { italics: true })], ...after(1), keepNext: true });

const stackLine = (text) => new Paragraph({
  children: [run("Stack: ", { bold: true }), run(text)],
  ...after(1.5),
  keepNext: true,
});

const body = [];
body.push(new Paragraph({ children: [run(c.name, { bold: true, size: 17 })], ...after(0) }));
body.push(new Paragraph({ children: [run(c.headline, { bold: true, size: 11 })], ...after(0) }));
body.push(new Paragraph({ children: [run(c.contact)], ...after(2) }));

body.push(heading("Summary"));
body.push(new Paragraph({ children: [run(c.summary)], alignment: AlignmentType.LEFT, ...after(2) }));

body.push(heading("Key achievements"));
c.achievements.forEach((a) => body.push(bullet(a)));

body.push(heading("Skills"));
c.skills.forEach(([label, text]) => body.push(labelled(label, text)));

body.push(heading(c.projects.length > 1 ? "Selected AI projects" : "Selected AI project"));
c.projects.forEach((p) => {
  body.push(roleHeader(p.title, p.dates));
  if (p.stack) body.push(stackLine(p.stack));
  p.bullets.forEach((b) => body.push(bullet(b)));
});

body.push(heading("Professional experience"));
c.experience.forEach((e) => {
  body.push(roleHeader(e.title, e.dates));
  // Short stacks share the company line to save space.
  if (e.stack && (e.org + e.stack).length < 105) {
    body.push(new Paragraph({
      children: [run(e.org, { italics: true }), run(" | Stack: ", { bold: true }), run(e.stack)],
      ...after(1), keepNext: true,
    }));
  } else {
    body.push(italicLine(e.org));
    if (e.stack) body.push(stackLine(e.stack));
  }
  (e.bullets || []).forEach((b) => body.push(bullet(b)));
});

body.push(heading("Education and teaching"));
c.education.forEach((e) => body.push(bullet(e)));

body.push(heading("Certifications and languages"));
body.push(new Paragraph({ children: [run(c.certifications)], ...after(1) }));
body.push(new Paragraph({ children: [run("Languages: ", { bold: true }), run(c.languages)] }));

const doc = new Document({
  creator: "Issam Sedki",
  title: "Issam Sedki — Resume (AI Engineer)",
  styles: { default: { document: { run: { font: "Calibri", size: pt(10) }, paragraph: { spacing: { line: 240 } } } } },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 220, hanging: 180 } } } }],
    }],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    children: body,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("wrote", out); });
