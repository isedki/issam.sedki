"""Shows how many lines each paragraph takes in Calibri 10pt, and how much room is left on its last line.
Paragraphs that spill onto a new line by only a few words are the cheapest to trim.

Usage: python line_fit.py RESUME.docx
"""
import sys
from docx import Document
from PIL import ImageFont

FONTS = "/Applications/Microsoft Word.app/Contents/Resources/DFonts/"
SCALE = 20  # measure at 200pt for precision, divide back
reg = ImageFont.truetype(FONTS + "Calibri.ttf", 10 * SCALE)
bold = ImageFont.truetype(FONTS + "Calibrib.ttf", 10 * SCALE)
ital = ImageFont.truetype(FONTS + "Calibrii.ttf", 10 * SCALE)
TEXT_W = (11906 - 1440) / 20  # points
BULLET_INDENT = 220 / 20

total = 0
for p in Document(sys.argv[1]).paragraphs:
    if not p.text.strip():
        continue
    width = TEXT_W - (BULLET_INDENT if p._p.pPr is not None and p._p.pPr.numPr is not None else 0)
    words = []
    for r in p.runs:
        f = bold if r.bold else ital if r.italic else reg
        words += [(w, f) for w in r.text.replace("\t", " ").split(" ") if w]
    lines, cur = 1, 0.0
    space = reg.getlength(" ") / SCALE
    for w, f in words:
        wl = f.getlength(w) / SCALE
        if cur and cur + space + wl > width:
            lines, cur = lines + 1, wl
        else:
            cur = cur + (space if cur else 0) + wl
    total += lines
    spare = width - cur
    flag = "  <- spills by a little" if lines > 1 and cur < 0.25 * width else ""
    print(f"{lines}  last line {cur/width:4.0%}  {p.text[:70]}{flag}")
print("total lines:", total)
