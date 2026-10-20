import json, sys, re, os
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

R = json.load(open("results.json"))


def load(name, default):
    return json.load(open(name)) if os.path.exists(name) else default


TOC_PAGES = load("toc_pages.json", {})      # key -> page string
PREV_HEADS = load("headings.json", [])      # list of {key, level, search}
PREV_CAPS = load("caps.json", [])           # list of {kind, label, title}

M = R["main"]
DS = list(M.keys())
METH = list(M[DS[0]].keys())
TITLE = "MST-BASED CLUSTERING FOR NON-LINEARLY SEPARABLE PATTERNS"
PERIOD = "July-December, 2026"
UNI = "Manav Rachna International Institute of Research and Studies"
GUIDE = "Dr. Aman Kumar"

doc = Document()
sec0 = doc.sections[0]
for s_ in (sec0,):
    s_.page_width, s_.page_height = Cm(21), Cm(29.7)
    s_.left_margin, s_.right_margin = Inches(1.5), Inches(1.0)
    s_.top_margin, s_.bottom_margin = Inches(1.0), Inches(1.0)
st = doc.styles["Normal"]
st.font.name = "Times New Roman"; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.line_spacing = 1.5
st.paragraph_format.space_after = Pt(6)
for name, size in (("Heading 1", 15), ("Heading 2", 12), ("Heading 3", 12)):
    h = doc.styles[name]
    h.font.name = "Times New Roman"; h.font.size = Pt(size); h.font.bold = True; h.font.italic = False
    h.font.color.rgb = RGBColor(0, 0, 0)
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    h.element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    h.element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if h.element.rPr.rFonts.get(qn(a)) is not None:
            del h.element.rPr.rFonts.attrib[qn(a)]
    h.paragraph_format.space_before = Pt(12); h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    h.paragraph_format.line_spacing = 1.15

HEADINGS = []   # (level, key, search_text)
CAPS = []       # dict(kind, label, title)


def roman(n):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s; n -= v
    return out


def H1(t, newpage=True):
    if newpage:
        doc.add_page_break()
    m = re.match(r"^(\d+)\. (.*)$", t)
    special = {"5. Conclusion and Future Work": "CONCLUSION AND FUTURE ENHANCEMENTS",
               "6. References": "REFERENCES", "7. Appendix": "APPENDICES"}
    if t.startswith("6.") or t.startswith("7."):
        p = doc.add_heading(special[t], 1); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        HEADINGS.append((1, t, special[t]))
        return p
    title = special.get(t, m.group(2).upper() if m else t.upper())
    p = doc.add_paragraph(style="Heading 1"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if m:
        p.add_run(f"CHAPTER {m.group(1)}"); p.add_run().add_break(); p.add_run(title)
        HEADINGS.append((1, t, f"CHAPTER {m.group(1)}"))
    else:
        p.add_run(title)
        HEADINGS.append((1, t, title))
    return p


def H2(t):
    HEADINGS.append((2, t, t.upper()))
    return doc.add_heading(t.upper(), 2)


def H3(t):
    return doc.add_heading(t, 3)


def P(t, align="j", bold=False, italic=False, size=None, after=None, spacing=None):
    p = doc.add_paragraph()
    p.alignment = {"j": WD_ALIGN_PARAGRAPH.JUSTIFY, "c": WD_ALIGN_PARAGRAPH.CENTER, "l": WD_ALIGN_PARAGRAPH.LEFT, "r": WD_ALIGN_PARAGRAPH.RIGHT}[align]
    for part in re.split(r"(\*\*.+?\*\*)", t):
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2]); r.bold = True
        else:
            r = p.add_run(part); r.bold = bold
        r.italic = italic
        if size: r.font.size = Pt(size)
    if after is not None: p.paragraph_format.space_after = Pt(after)
    if spacing: p.paragraph_format.line_spacing = spacing
    return p


def B(items, style="List Bullet"):
    for t in items:
        p = doc.add_paragraph(style=style)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for part in re.split(r"(\*\*.+?\*\*)", t):
            if part.startswith("**"):
                p.add_run(part[2:-2]).bold = True
            else:
                p.add_run(part)


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def reg_caption(text):
    m = re.match(r"^(Table|Fig\.)\s+([A-Z0-9.]+):\s*(.*)$", text)
    if m:
        CAPS.append(dict(kind=m.group(1), label=f"{m.group(1)} {m.group(2)}", title=m.group(3)))


def T(header, rows, widths=None, caption=None, size=10):
    if caption:
        reg_caption(caption)
        p = P(caption, "c", bold=True, italic=True, size=11, after=2)
        p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(size)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].paragraph_format.line_spacing = 1.0
        shade(c, "D9D9D9")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER if i else WD_ALIGN_PARAGRAPH.LEFT
            cells[i].paragraphs[0].paragraph_format.line_spacing = 1.0
            cells[i].paragraphs[0].paragraph_format.space_after = Pt(2)
    if widths:
        tot = sum(widths); k = 14.6 / tot if tot > 14.6 else 1
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w * k)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def F(path, caption, width=15.5):
    caption = re.sub(r"^Figure ", "Fig. ", caption)
    reg_caption(caption)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True; p.paragraph_format.line_spacing = 1.0
    p.add_run().add_picture(path, width=Cm(min(width, 14.6)))
    P(caption, "c", bold=True, italic=True, size=10.5, after=10)


def CODE(text, size=8):
    for line in text.split("\n"):
        p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.0; p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Cm(0.3)
        r = p.add_run(line if line else " "); r.font.name = "Consolas"; r.font.size = Pt(size)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")


def add_field(par, instr):
    r = par.add_run()
    for typ, txt in (("begin", None), (None, instr), ("end", None)):
        if typ:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), typ); r._r.append(e)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)


def page_num_fmt(section, fmt, start=1):
    sp = section._sectPr
    for old in sp.findall(qn("w:pgNumType")):
        sp.remove(old)
    e = OxmlElement("w:pgNumType"); e.set(qn("w:fmt"), fmt); e.set(qn("w:start"), str(start)); sp.append(e)


def new_section(fmt):
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    s.footer.is_linked_to_previous = False
    s.different_first_page_header_footer = False
    fp = s.footer.paragraphs[0]
    for r in list(fp.runs):
        r._r.getparent().remove(r._r)
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(fp, "PAGE")
    page_num_fmt(s, fmt, 1)
    return s


def centered(text, size=12, bold=True, italic=False, after=6, align="c"):
    return P(text, align, bold=bold, italic=italic, size=size, after=after, spacing=1.15)


def toc_line(txt, page, lvl=0, bold=False):
    p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.15; p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.9 * lvl)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(14.9), alignment=2, leader=1)
    r = p.add_run(f"{txt}\t{page}"); r.bold = bold
    return p


# ============================================================ COVER (section 0, no page number)
centered("MINI PROJECT REPORT", 12, after=4)
centered("ON", 12, after=8)
centered(TITLE, 16, after=14)
centered("Submitted by:", 12, italic=True, after=6)
centered("ARYAMAN\n1/23/SET/BCS/364", 12, after=4)
centered("ADITYA\n1/23/SET/BCS/363", 12, after=10)
centered("Under the Guidance of", 12, italic=True, after=6)
centered("Dr. Aman Kumar\nAssociate Professor", 12, after=10)
centered("in partial fulfilment for the award of the degree of", 12, italic=True, after=10)
centered("BACHELOR OF TECHNOLOGY", 14, after=2)
centered("IN", 11, after=2)
centered("Computer Science & Engineering", 12, after=8)
lp = doc.add_paragraph(); lp.alignment = WD_ALIGN_PARAGRAPH.CENTER; lp.paragraph_format.space_after = Pt(4)
lp.add_run().add_picture("figures/logo.png", width=Cm(5.2))
centered("School of Engineering & Technology", 13, after=6)
centered("MANAV RACHNA INTERNATIONAL INSTITUTE OF RESEARCH AND STUDIES, Faridabad", 13, after=2)
centered("NAAC ACCREDITED ‘A++’ GRADE", 13, after=2)
centered(PERIOD, 12, after=0)

# ============================================================ FRONT MATTER (roman)
new_section("lowerRoman")

# ---- Acknowledgement
centered("Acknowledgement", 14, after=14)
P("We would like to express our sincere gratitude to our supervisor **Dr. Aman Kumar, Associate Professor, Dept. of CSE (SET, MRIIRS)**, for giving us the opportunity to work on this topic. It would never have been possible for us to take this project to this level without his innovative ideas and relentless support and encouragement.", spacing=1.5)
P("We express our deepest thanks to **Dr. Nitasha Soni, Dr. Kritika Soni, Dr. Ashok and Ms. Swati** for taking part in useful decisions and giving necessary advice and guidance, and for arranging all facilities to make our work easier. We choose this moment to acknowledge their contribution gratefully.", spacing=1.5)
P("We take immense pleasure in thanking **Dr. Suresh Kumar**, Head of Department of Computer Science and Engineering, SET, MRIIRS. His tolerance of having discussions and sacrificing personal time is extremely insightful and greatly appreciated.", spacing=1.5)
for _ in range(3): P("", "l")
P("ARYAMAN, 1/23/SET/BCS/364", "l", spacing=1.15, after=2)
P("ADITYA, 1/23/SET/BCS/363", "l", spacing=1.15)

# ---- Declaration
doc.add_page_break()
centered("DECLARATION", 14, after=14)
P("We hereby declare that this Mini Project Report entitled “**MST-BASED CLUSTERING FOR NON-LINEARLY SEPARABLE PATTERNS**” by **ARYAMAN (1/23/SET/BCS/364)** and **ADITYA (1/23/SET/BCS/363)**, being submitted in partial fulfilment of the requirements for the degree of Bachelor of Technology in Computer Science and Engineering under School of Engineering & Technology of Manav Rachna International Institute of Research and Studies, Faridabad, during the academic year July-December, 2026, is a bonafide record of our original work carried out under the guidance and supervision of **Dr. Aman Kumar, Associate Professor, Dept. of CSE (SET, MRIIRS)** and has not been presented elsewhere.", spacing=1.5)
for _ in range(3): P("", "l")
P("ARYAMAN, 1/23/SET/BCS/364", "l", spacing=1.15, after=2)
P("ADITYA, 1/23/SET/BCS/363", "l", spacing=1.15)

# ---- Certificate
doc.add_page_break()
lp = doc.add_paragraph(); lp.alignment = WD_ALIGN_PARAGRAPH.CENTER; lp.paragraph_format.space_after = Pt(2)
lp.add_run().add_picture("figures/logo.png", width=Cm(4.0))
centered("Manav Rachna International Institute of Research and Studies,\nFaridabad", 13, after=2)
centered("School of Engineering & Technology", 13, after=2)
centered("Department of Computer Science & Engineering", 13, after=6)
P(PERIOD, "r", spacing=1.15)
centered("Certificate", 14, after=10)
P("This is to certify that this project report entitled “**MST-BASED CLUSTERING FOR NON-LINEARLY SEPARABLE PATTERNS**” by **ARYAMAN (Roll Number 1/23/SET/BCS/364)** and **ADITYA (Roll Number 1/23/SET/BCS/363)**, submitted in partial fulfilment of the requirements for the degree of Bachelor of Technology in **Computer Science and Engineering** under School of Engineering & Technology of Manav Rachna International Institute of Research and Studies, Faridabad, during the academic year July-December, 2026, is a bonafide record of work carried out under my guidance and supervision.", spacing=1.5)
P("", "l")
P("**(Signature of Vertical Mentor)**\n**Dr. Aman Kumar**\n**Associate Professor**\nDepartment of Computer Science & Engineering\nSchool of Engineering & Technology\nManav Rachna International Institute of Research and Studies, Faridabad", "l", spacing=1.15)
P("", "l")
P("**Dr. Suresh Kumar**\n**Professor and Head of Department**\nDepartment of Computer Science & Engineering\nSchool of Engineering & Technology\nManav Rachna International Institute of Research and Studies, Faridabad", "l", spacing=1.15)

# ---- Table of contents
doc.add_page_break()
centered("TABLE OF CONTENTS", 14, after=10)
FRONT = [("Acknowledgement", "i"), ("Declaration", "ii"), ("Certificate", "iii"), ("Table of Contents", "iv"),
         ("List of Figures", "v"), ("List of Tables", "vi"), ("Abstract", "vii")]
for k, v in FRONT:
    toc_line(k, TOC_PAGES.get("front:" + k, v))
p = toc_line("Chapter", "Page No.", 0, True); p.paragraph_format.space_before = Pt(8)
for h in PREV_HEADS:
    if h["level"] == 0:
        continue
    if h["level"] == 1:
        key = h["key"]
        m = re.match(r"^(\d+)\. (.*)$", key)
        label = key.upper() if m and not key.startswith(("6.", "7.")) else h["search"] if key.startswith(("6.", "7.")) else key
        if key.startswith("5."):
            label = "5. CONCLUSION AND FUTURE ENHANCEMENTS"
        toc_line(label, TOC_PAGES.get(key, ""), 0, True)
    else:
        toc_line(h["key"], TOC_PAGES.get(h["key"], ""), 1)

# ---- List of figures
doc.add_page_break()
centered("LIST OF FIGURES", 14, after=10)
toc_line("Figure", "Page No.", 0, True)
for c in PREV_CAPS:
    if c["kind"] == "Fig.":
        toc_line(f"{c['label']}  {c['title']}", TOC_PAGES.get("cap:" + c["label"], ""), 0)

# ---- List of tables
doc.add_page_break()
centered("LIST OF TABLES", 14, after=10)
toc_line("Table", "Page No.", 0, True)
for c in PREV_CAPS:
    if c["kind"] == "Table":
        toc_line(f"{c['label']}  {c['title']}", TOC_PAGES.get("cap:" + c["label"], ""), 0)

# ---- Abstract (double spaced, one page)
doc.add_page_break()
HEADINGS.append((0, "Abstract", "ABSTRACT"))
centered("ABSTRACT", 14, after=10)
ABS = [
    "Conventional partitioning algorithms such as K-Means and Gaussian Mixture Models assume that clusters are compact and separable by linear or quadratic boundaries. Real data often contain curved, nested or interleaved groups, and on such non-linearly separable patterns centroid-based methods return partitions unrelated to the true structure. This mini project develops a clustering approach based on the Euclidean Minimum Spanning Tree (MST), which keeps the chains of near neighbours that define a natural cluster, and separates clusters by removing unusually long edges.",
    "The implementation in Python provides an exact MST builder (with a Delaunay-accelerated mode for large 2-D data), a k-cut rule and an automatic Zahn inconsistency-ratio rule for cutting edges, a minimum-cluster-size guard against outliers, and an optional mutual-reachability weighting. It is compared with K-Means, GMM, Ward, single linkage and DBSCAN on five synthetic and three real data sets using ARI, NMI, silhouette and convex-hull overlap.",
    "The MST recovers the ground truth exactly (ARI = 1.00) on moons, circles and spirals, where K-Means, GMM and Ward reach at most 0.62, and matches them on compact clusters. The study also reports limits: sensitivity to heavy noise, a tuned threshold for the automatic mode, weaker results on Iris and Wine, and silhouette scores that wrongly favour convex partitions.",
]
for a in ABS:
    P(a, spacing=2.0, after=0)
P("**Keywords:** minimum spanning tree, graph-based clustering, non-linear separability, Zahn algorithm, cluster validity.", spacing=1.5)

# ============================================================ MAIN MATTER (arabic)
new_section("decimal")
