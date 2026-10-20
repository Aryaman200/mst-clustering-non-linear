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

# ------------------------------------------------------------------ 1 INTRO
H1("1. Introduction", newpage=False)
H2("1.1 Background and Motivation")
P("Clustering is the unsupervised task of grouping a set of objects so that objects in the same group are more similar to each other than to those in other groups. It is a central tool in exploratory data analysis, with applications in image segmentation, customer segmentation, bioinformatics (grouping genes with similar expression profiles), anomaly detection, document organisation and astronomy. Jain's review of fifty years of clustering research [1] notes that, although thousands of algorithms have been proposed, K-Means and its relatives remain the most widely used because they are simple, fast and scale linearly with data size.")
P("The popularity of K-Means hides a strong assumption. K-Means minimises the within-cluster sum of squared distances to a set of k centroids. Its decision boundaries are therefore the perpendicular bisectors between centroids - straight lines in two dimensions and hyperplanes in higher dimensions - and each cluster is the convex Voronoi cell of its centroid. Gaussian Mixture Models relax spherical shape to ellipsoids but still describe each cluster by a single unimodal density. Both families can only separate clusters that are **linearly (or quadratically) separable**.")
P("Many natural data sets are not like this. Spiral galaxies, road networks, protein-interaction paths, handwritten strokes and trajectories form curved, chain-like or nested shapes. Two interleaved half-moons, or a small ring enclosed by a larger ring, cannot be separated by any hyperplane, yet a human immediately sees two groups because the points of each group form a **connected, continuous chain** with comparatively small gaps between neighbours, while the gap between groups is larger. This is the intuition behind connectivity-based clustering, and the Minimum Spanning Tree is its most economical mathematical embodiment.")
P("A spanning tree of a weighted graph connects all vertices with n-1 edges and no cycles; the MST is the spanning tree of minimum total weight. For points in space, with Euclidean distance as weight, the MST links every point to the rest through short edges. Within a cluster, MST edges are short (neighbouring points); between clusters, at least one MST edge must bridge the gap and it is therefore long. Deleting the longest edges thus splits the tree into the natural clusters - without making any assumption about cluster shape.")
H2("1.2 Problem Statement")
P("Given a set X of n points in d-dimensional space, whose underlying groups may be non-convex, nested, elongated or intertwined, design and implement a clustering approach based on the Euclidean Minimum Spanning Tree that recovers such non-linearly separable groups, and compare the resulting cluster structure quantitatively and visually with conventional partitioning methods (K-Means, Gaussian Mixture Models and Ward hierarchical clustering).")
H2("1.3 Objectives")
B([
    "To study the theory of the Euclidean MST and its relationship to single-linkage clustering and to Zahn's inconsistent-edge method.",
    "To implement an MST clustering library from first principles: MST construction, inconsistency measurement, edge cutting and label generation.",
    "To handle outliers and noise through a minimum-cluster-size rule and mutual-reachability distances.",
    "To benchmark the approach against K-Means, GMM, Ward, single-linkage and DBSCAN on synthetic non-linearly separable data sets and on real data sets.",
    "To compare the **cluster structure** produced by each method using external indices (ARI, NMI), internal indices (silhouette, convex-hull overlap), robustness to noise, sensitivity to parameters and run-time scaling.",
    "To document strengths, failure cases and recommendations honestly.",
])
H2("1.4 Scope and Contributions")
P("The project is restricted to numeric vector data and Euclidean geometry. The work is a mini project: the focus is on a clean, reproducible implementation and a transparent empirical comparison rather than on a new theoretical bound. The contributions are:")
B([
    "A compact, self-contained Python implementation (about 150 lines) of MST clustering with two cutting modes, available in Appendix A.",
    "A minimum-size admissibility rule that makes k-cut MST clustering robust to outlier links, in contrast to plain single linkage, which fails as soon as an isolated outlier becomes its own cluster.",
    "A Delaunay-based MST construction that reduces the cost from quadratic to near-linearithmic time for two-dimensional data.",
    "An empirical study that includes **negative results**: noise sensitivity, parameter sensitivity, failure on overlapping real data and the unreliability of internal validity indices on non-convex clusters.",
])
H2("1.5 Organisation of the Report")
P("Chapter 2 surveys related work. Chapter 3 presents the proposed methodology, including the high-level view, detailed architecture, operational diagram, algorithms and complexity analysis. Chapter 4 describes the implementation, the technology stack, the experimental results (figures and tables) and their analysis. Chapter 5 concludes and lists future work. References and the appendix (source code and full result tables) follow.")

# ------------------------------------------------------------------ 2 LIT SURVEY
H1("2. Literature Survey")
P("This chapter reviews the families of clustering algorithms that are relevant to non-linearly separable data and positions MST-based clustering among them.")
H2("2.1 Partitional Clustering")
P("MacQueen [2] introduced the term K-Means and Lloyd [3] described the iterative assign-and-update procedure now used in practice. The algorithm alternates between assigning each point to its nearest centroid and recomputing centroids as cluster means until convergence; each iteration costs O(nkd). K-Means is sensitive to initialisation, requires k in advance, favours clusters of similar size and spherical shape, and converges only to a local optimum. Arthur and Vassilvitskii's k-means++ seeding improves the quality of the starting centroids, and scikit-learn uses it by default [13].")
P("Gaussian Mixture Models, fitted by Expectation-Maximisation, model data as a weighted sum of Gaussian densities and so handle ellipsoidal clusters of different orientation and size. Nevertheless, a cluster that is not well approximated by one Gaussian - a ring, a moon, a spiral arm - will be split among several components or merged with its neighbour. Both families therefore fail on the benchmarks studied here, as will be confirmed in Chapter 4.")
H2("2.2 Hierarchical Clustering and Single Linkage")
P("Agglomerative hierarchical clustering starts with every point as its own cluster and repeatedly merges the closest pair, under a linkage criterion that defines inter-cluster distance. Ward's method [4] merges the pair that gives the minimum increase in within-cluster variance and thus behaves like a hierarchical K-Means, with the same preference for compact clusters. In **single linkage**, the distance between two clusters is the distance between their closest members; clusters can therefore grow along chains of points, which allows non-convex shapes but produces the well-known \"chaining\" effect, where a thin bridge of noise points merges two otherwise separate clusters.")
P("Gower and Ross [5] proved the fundamental connection used in this report: the single-linkage dendrogram can be read directly from the MST. Merging clusters in order of increasing distance is exactly Kruskal's algorithm, so the single-linkage partition into k clusters is obtained by deleting the k-1 longest MST edges. MST clustering and single linkage are consequently the same partitioning for the same k; the practical differences lie in what is done with the tree - inconsistency tests, size constraints, alternative edge weights - and in the efficiency of constructing it.")
H2("2.3 Density-Based and Spectral Clustering")
P("DBSCAN [6] defines clusters as maximal sets of density-connected points: a core point has at least minPts neighbours within radius eps, and clusters grow by transitive reachability. It finds arbitrarily shaped clusters and labels sparse points as noise, but requires eps and minPts, and it struggles when clusters have different densities because a single eps cannot suit all. HDBSCAN [7] removes the global eps by building a hierarchy over the **mutual reachability distance** and extracting stable clusters; its core step is precisely an MST computed on mutual-reachability weights, which is why the same weighting is offered as an option in this project.")
P("Spectral clustering [8][9] embeds points through the leading eigenvectors of a graph Laplacian built from a similarity graph and then applies K-Means in the embedding. It handles non-convex clusters well but requires an eigen-decomposition (O(n^3) in the dense case), a similarity-scale parameter, and the number of clusters. Other kernel-based and manifold-based approaches have similar costs. In comparison, the MST approach needs no eigen-decomposition and its dominant cost is the construction of the tree.")
H2("2.4 Graph-Theoretic and MST-Based Clustering")
P("Zahn [10] was the first to propose clustering with the MST. He defined an edge as **inconsistent** if its weight is significantly larger than the average weight of nearby edges on both sides, and removed inconsistent edges to produce clusters, also giving detectors of different gestalt types (separated, touching, linked, contiguous). The principal merit of the approach is that the criterion is local: a long edge inside a sparse cluster is not cut if its neighbouring edges are equally long, whereas a moderately long edge in a dense region is.")
P("Xu, Olman and Xu [11] used MST clustering for gene-expression data and proposed three objective functions - removing edges to minimise the total edge-weight deviation, a k-cluster formulation solvable by dynamic programming and a global-optimum formulation - demonstrating that MST clustering is competitive on biological data. Zhong, Miao and Wang [12] proposed a two-rounds MST algorithm in which a first MST is computed, its edges removed, and a second MST built on the remaining graph to expose hidden separations and reduce the effect of outliers; the method achieves better results than single-round variants on several benchmark sets. Karypis, Han and Kumar's CHAMELEON [14] likewise relies on graph partitioning of a k-nearest-neighbour graph followed by dynamic merging that considers inter-connectivity and closeness, and is known for strong performance on spiral-like data.")
P("For efficiency, Shamos and Hoey [15] showed that the Euclidean MST of a planar point set is a subgraph of its Delaunay triangulation, which has O(n) edges, giving an O(n log n) algorithm in two dimensions. For higher dimensions, March, Ram and Gray [16] developed a dual-tree Boruvka algorithm for fast Euclidean MST computation. These results make MST clustering practical for large data.")
H2("2.5 Research Gap and Summary of Related Work")
T(["Method", "Cluster shape", "Needs k?", "Outlier handling", "Main limitation"], [
    ["K-Means [2][3]", "Convex, similar size", "Yes", "None (sensitive)", "Linear boundaries"],
    ["GMM (EM)", "Ellipsoidal", "Yes", "Weak", "Unimodal components"],
    ["Ward [4]", "Compact", "Yes", "Weak", "Variance-minimising"],
    ["Single linkage [5]", "Arbitrary", "Yes (cut)", "Poor (chaining)", "Outlier clusters"],
    ["DBSCAN [6]", "Arbitrary", "No (eps)", "Noise label", "Single density scale"],
    ["Spectral [8][9]", "Arbitrary", "Yes", "Moderate", "O(n^3) eigen step"],
    ["Zahn MST [10]", "Arbitrary", "No (ratio)", "Via ratio test", "Threshold choice"],
    ["Proposed", "Arbitrary", "Either", "Min-size guard + optional mutual reachability", "Heavy overlap/noise"],
], widths=[3.2, 3.2, 2.3, 3.7, 3.6], caption="Table 2.1: Comparison of related clustering approaches", size=9)
P("The literature shows that MST clustering is theoretically well understood but, in practice, plain single-linkage cutting is brittle (outlier clusters, chaining) while ratio-based cutting needs a threshold. The gap addressed by this mini project is a transparent, reproducible comparison that (a) combines both cutting strategies with a minimum-size guard in one small implementation, and (b) quantifies where this approach wins against conventional partitioning and where it does not, including noise, parameter sensitivity and real data.")

# ------------------------------------------------------------------ 3 METHODOLOGY
H1("3. Proposed Methodology")
H2("3.1 Mathematical Preliminaries")
P("Let X = {x_1, ..., x_n} be a set of points in R^d and G = (V, E, w) the complete weighted graph with V = X and w(x_i, x_j) = ||x_i - x_j||_2. A **spanning tree** T of G is an acyclic connected subgraph that contains all n vertices (and therefore n-1 edges). The **minimum spanning tree** minimises the total weight W(T), the sum of the weights of the edges of T. For distinct edge weights the MST is unique. Two properties are used throughout:")
B([
    "**Cut property.** For any partition of the vertices into two non-empty sets, the lightest edge crossing the partition belongs to the MST.",
    "**Cycle property.** For any cycle in G, the heaviest edge of the cycle does not belong to the MST (when it is unique).",
])
P("A consequence is the **bottleneck property**: the path between two points in the MST minimises the maximum edge weight along the path over all paths in G. Two points are therefore connected in the MST by a path whose longest hop is as short as possible, which is exactly the right notion of \"connected through a chain of close neighbours\" for non-convex clusters. Deleting an MST edge of weight w removes the connection between two parts and means that those parts cannot be linked by any path with all hops shorter than w.")
H3("Mutual-reachability distance")
P("To make the MST less influenced by sparse noise, the weight can be replaced by the mutual-reachability distance, d_mreach(a, b) = max(core_k(a), core_k(b), ||a - b||), where core_k(a) is the distance from a to its k-th nearest neighbour. Points in sparse regions have large core distances, which inflates every edge incident to them, so noise points are attached to the tree by heavy edges while edges inside dense clusters are unchanged. This is the weighting used by HDBSCAN [7].")
H3("Zahn's inconsistency ratio")
P("For an MST edge e = (u, v) with weight w_e, let N_u be the set of edges reachable from u within a depth of D hops without crossing e, and N_v the corresponding set on the side of v. The inconsistency ratio is r(e) = w_e / max(mean(N_u), mean(N_v)). Edges with r(e) above a threshold t (2 to 3 is typical [10]) are candidate cluster boundaries. Using the larger of the two side means is deliberately conservative: an edge is only cut if it is long relative to both neighbourhoods. Dividing by the local neighbourhood mean, rather than a global statistic, makes the criterion scale-free and adaptive to clusters of differing density.")
H2("3.2 High-Level View")
P("Figure 3.1 shows the high-level view of the system. Input data are standardised, a weighted graph is built, the MST is extracted, the edges are analysed, the cutting rule removes boundary edges subject to the size guard, and the connected components of the remaining forest are the clusters, which are then evaluated against baselines.")
F("figures/arch_high_level.png", "Figure 3.1: High-level view of the MST-based clustering pipeline", 16)
P("The key design idea is the separation of concerns: the **geometry** (tree construction) is computed once; the **decision** (which edges to cut) is a cheap operation on n-1 numbers and can be repeated for different k or thresholds without rebuilding the tree. This makes parameter exploration inexpensive, which is exploited in the sensitivity experiment of Section 4.4.")
H2("3.3 Detailed Architecture")
P("Figure 3.2 shows the layered architecture. Layer 1 prepares the data and the candidate graph; Layer 2 builds the tree and computes edge statistics; Layer 3 decides the cuts and evaluates the result.")
F("figures/arch_detailed.png", "Figure 3.2: Detailed layered architecture", 15.5)
H3("Layer 1 - Data and graph construction")
P("Features are standardised to zero mean and unit variance so that no coordinate dominates the Euclidean distance. For d > 2, or for n up to about 1,500, the complete distance matrix is computed and the weights optionally replaced by mutual-reachability distances. For two-dimensional data with larger n the candidate edge set is restricted to the edges of the Delaunay triangulation, which provably contains the Euclidean MST [15] and has only O(n) edges.")
H3("Layer 2 - MST core and edge analysis")
P("SciPy's compressed-sparse-graph routine computes the MST of the candidate graph (Kruskal-type union-find on sorted edges). The n-1 tree edges are stored as an array of (u, v, w) triples and an adjacency list with edge identifiers, which is used for neighbourhood queries (inconsistency ratio) and for component-size queries (min-size guard).")
H3("Layer 3 - Partitioning and evaluation")
P("The cut controller sorts candidate edges and examines them from heaviest to lightest. In **k mode** the candidates are all edges and the loop stops after k-1 accepted cuts. In **Zahn mode** the candidates are the edges with r(e) above the threshold and the loop runs until the candidate list is exhausted, so the number of clusters is an output. For every candidate the size guard tentatively removes the edge and checks, with a breadth-first search, that both resulting sub-trees contain at least m points; otherwise the edge is regarded as an outlier link and kept. The final labels are the connected components of the tree after removal of the accepted edges.")
H2("3.4 Operational Diagram")
P("Figure 3.3 gives the operational flow of the algorithm, including the decision between the two cutting modes and the size guard loop.")
F("figures/arch_flow.png", "Figure 3.3: Operational flow diagram of MST clustering", 11.5)
H2("3.5 Algorithms")
H3("Algorithm 1 - MST clustering (k-cut mode)")
CODE("""Input : X (n x d), number of clusters k, minimum cluster size m
Output: label vector y

1.  X <- standardise(X)
2.  T <- EuclideanMST(X)                  # n-1 edges (u, v, w)
3.  C <- edges of T sorted by w, descending
4.  R <- {}                               # removed edges
5.  for e = (u, v) in C:
6.      if |R| = k-1: break
7.      if size(component of u in T \\ (R + e)) >= m and
            size(component of v in T \\ (R + e)) >= m:
8.          R <- R + {e}
9.  y <- connected components of T \\ R
10. return y""", 9)
H3("Algorithm 2 - MST clustering (Zahn mode)")
CODE("""Input : X, ratio threshold t, depth D, minimum cluster size m
Output: label vector y (number of clusters found automatically)

1.  T <- EuclideanMST(standardise(X))
2.  for each edge e in T:  r(e) <- w(e) / max(mean(N_u(e, D)), mean(N_v(e, D)))
3.  C <- { e : r(e) > t } sorted by w, descending
4.  R <- {}
5.  for e = (u, v) in C:
6.      if both sub-trees of T \\ (R + e) contain >= m points: R <- R + {e}
7.  y <- connected components of T \\ R
8.  return y""", 9)
P("Algorithm 1 differs from plain single linkage only in line 7: the size guard. This one line changes the behaviour when the data contain isolated points: single linkage would spend a cut to isolate a lone outlier, because the outlier's incident MST edge is among the longest; the guard refuses it and moves on to the next-longest edge, which is the real cluster boundary. Section 4.4 demonstrates this on a data set with 25 injected outliers.")
H2("3.6 Complexity Analysis")
T(["Step", "Time", "Memory", "Remarks"], [
    ["Distance matrix (dense)", "O(n^2 d)", "O(n^2)", "Practical to n of a few thousand"],
    ["MST via Kruskal on dense graph", "O(n^2 log n)", "O(n^2)", "SciPy csgraph"],
    ["Delaunay triangulation (d = 2)", "O(n log n)", "O(n)", "EMST is a subgraph [15]"],
    ["MST on Delaunay edges", "O(n log n)", "O(n)", "~3n candidate edges"],
    ["Inconsistency ratios (depth D)", "O(n b^D)", "O(n)", "b: tree branching (small, ~2-3)"],
    ["Cut loop with size guard", "O(c n)", "O(n)", "c: candidate edges examined"],
    ["Label extraction", "O(n)", "O(n)", "Breadth-first search"],
], widths=[5.0, 2.8, 2.2, 5.4], caption="Table 3.1: Complexity of the main steps", size=9.5)
P("The overall cost is dominated by MST construction: quadratic for the dense route and O(n log n) for the Delaunay route. Our implementation of the cut loop does a fresh breadth-first search for each candidate, i.e. O(n) per candidate; this is adequate because only the heaviest few edges are examined in k mode, but could be replaced by subtree-size bookkeeping for very large inputs. K-Means costs O(nkd) per iteration and is faster in absolute terms, but the experiment in Section 4.4 shows that the MST route remains within a small constant factor for two-dimensional data.")
H2("3.7 Evaluation Methodology")
P("Because the compared algorithms produce different cluster shapes, no single metric is adequate. Four kinds of evidence are used:")
B([
    "**External indices** (ground truth is known for all data sets): the Adjusted Rand Index (ARI) [17], which is chance-corrected (0 for random labelling, 1 for identical partitions), and the Normalised Mutual Information (NMI).",
    "**Internal indices:** the silhouette coefficient [18], which rewards compact, well-separated clusters, and the **convex-hull overlap**, defined here as the fraction of all points that fall inside the convex hull of a cluster other than their own. The latter is a direct measure of \"interpenetration\" of clusters and is zero for linearly separable partitions.",
    "**Robustness:** ARI versus noise level (two moons, five random seeds per level) and ARI versus the Zahn ratio threshold.",
    "**Efficiency:** wall-clock time of MST construction and baselines for n from 500 to 16,000.",
])
P("The comparison of cluster **structure** is therefore both numerical (the indices above) and visual (scatter plots of assignments, the MST with the cut edges highlighted). The number of clusters passed to every algorithm that needs it is the ground-truth value; the Zahn mode and DBSCAN discover it themselves.")

# ------------------------------------------------------------------ 4 IMPLEMENTATION
H1("4. Implementation Description")
H2("4.1 Requirements and Technology Stack")
P("The project runs on commodity hardware without a GPU. Table 4.1 lists the software and hardware needed to reproduce every result in this report, and Table 4.2 lists the technology stack used.")
T(["Category", "Requirement"], [
    ["Operating system", "Windows 10 / 11, Linux or macOS (64-bit)"],
    ["Language and runtime", "Python 3.10 or newer (3.12 used)"],
    ["Libraries", "NumPy, SciPy, scikit-learn, Matplotlib, pandas, NetworkX"],
    ["Documentation tools", "python-docx, LibreOffice (PDF export)"],
    ["Processor", "Dual-core 2 GHz or better (any modern laptop CPU)"],
    ["Memory", "4 GB RAM minimum; 8 GB recommended (dense MST on 4,000 points needs about 128 MB)"],
    ["Storage", "Under 200 MB including figures and results"],
    ["Display", "Any; figures are generated as PNG files"],
], widths=[4.2, 10.4], caption="Table 4.1: Software and hardware requirements", size=10)
T(["Component", "Tool / Version", "Purpose"], [
    ["Language", "Python 3.12", "Implementation of the algorithm and experiments"],
    ["Numerical computing", "NumPy 2.x", "Arrays, vector maths, distances"],
    ["Scientific computing", "SciPy 1.17", "csgraph.minimum_spanning_tree, Delaunay, distance_matrix"],
    ["Machine learning", "scikit-learn 1.4", "Baselines (KMeans, GMM, Agglomerative, DBSCAN), data generators, metrics"],
    ["Graph utilities", "NetworkX 3.x", "Optional MST cross-checks"],
    ["Visualisation", "Matplotlib 3.10", "Scatter plots, MST drawings, diagrams, charts"],
    ["Data handling", "pandas 2.x", "Result tables"],
    ["Report generation", "python-docx", "Automatic assembly of this report"],
    ["Platform", "Windows 10 (CPU only)", "All experiments reproducible without GPU"],
], widths=[4.0, 4.0, 7.4], caption="Table 4.2: Technology stack", size=10)
H2("4.2 Software Design")
P("The code is organised in two modules. **mst_clustering.py** contains the reusable library: build_mst constructs the tree (dense, Delaunay or mutual-reachability weighted), the private helpers _adjacency, _component_size, _labels_from_cuts and _inconsistency implement tree traversal, and the class MSTClusterer exposes a scikit-learn-style fit_predict interface with the parameters n_clusters, mode (k or zahn), min_size, ratio_thr, depth, mst_method and mreach_k. **experiments.py** runs all experiments and writes the figures and a results file.")
P("Key implementation decisions are as follows. (1) The tree is stored as an edge array plus adjacency list so that deleting an edge is a set insertion, not a graph mutation. (2) The size guard uses a breadth-first search that skips removed edges, which is simple and sufficiently fast for the data sizes used. (3) The Delaunay route is selected automatically for two-dimensional data when n exceeds 1,500. (4) All random operations use fixed seeds so that every table and figure in this report can be regenerated exactly. A listing of mst_clustering.py is given in Appendix A.")
H2("4.3 Datasets and Experimental Setup")
T(["Dataset", "n", "d", "k", "Description"], [
    ["Two Moons", "600", "2", "2", "Interleaved half-circles, noise std 0.06"],
    ["Concentric Circles", "600", "2", "2", "Ring inside ring, factor 0.4, noise 0.05"],
    ["Two Spirals", "800", "2", "2", "Two interleaved spiral arms, noise 0.03"],
    ["Anisotropic Blobs", "600", "2", "3", "Three Gaussian blobs after a shear transform"],
    ["Gaussian Blobs", "600", "2", "3", "Three compact spherical clusters"],
    ["Iris", "150", "4", "3", "Real: flower measurements"],
    ["Wine", "178", "13", "3", "Real: chemical analysis"],
    ["Digits (PCA-10)", "1797", "10", "10", "Real: handwritten digits reduced by PCA"],
], widths=[3.6, 1.3, 1.1, 1.1, 8.3], caption="Table 4.3: Datasets used in the experiments", size=10)
P("All data are standardised. The minimum cluster size is set to n/40 (at least 10), the Zahn depth to 3 and the ratio threshold to 3.0 for the main comparison; the choice of 3.0 was informed by the sensitivity analysis in Section 4.4 and is therefore not independent of the benchmark data - an honest caveat that is repeated in the analysis. K-Means uses 10 restarts and k-means++ seeding, GMM uses full covariance and 5 restarts, and Ward and single linkage are the scikit-learn agglomerative implementations.")
H2("4.4 Results (Screenshots / Figures)")
H3("4.4.1 Anatomy of MST clustering")
P("Figure 4.1 shows the MST of the two-moons data, the two cut edges (red) selected by the k-cut rule and the resulting clusters. The MST is a thin skeleton following each moon; the only long edge connecting the moons is the bridge, which is cut. Figures 4.2 and 4.3 show the same view for concentric circles and the two spirals.")
F("figures/mst_steps_two_moons.png", "Figure 4.1: MST, cut edge and resulting clusters - Two Moons", 16)
F("figures/mst_steps_concentric_circles.png", "Figure 4.2: MST, cut edge and resulting clusters - Concentric Circles", 16)
F("figures/mst_steps_two_spirals.png", "Figure 4.3: MST, cut edge and resulting clusters - Two Spirals", 16)
P("Figure 4.4 shows the distribution of MST edge weights. The histogram is strongly right-skewed: nearly all edges are short, local-neighbour links, and a few very long edges stand out. The sorted-weight plot shows the clear \"knee\" where the bridging edge separates from the intra-cluster edges; the position of such a gap is the visual basis for deciding the number of clusters.")
F("figures/edge_weights.png", "Figure 4.4: Distribution of MST edge weights (Two Moons)", 14)
H3("4.4.2 Comparison with conventional partitioning")
P("Figure 4.5 compares all methods on all five synthetic data sets in one grid; the ARI is printed above each panel. Table 4.4 gives the corresponding external indices.")
F("figures/comparison_grid.png", "Figure 4.5: Ground truth and cluster assignments of six methods on five data sets", 16)


def mt(metric, caption, fmt="{:.2f}"):
    rows = []
    for d in DS:
        rows.append([d] + [fmt.format(M[d][m][metric]) for m in METH])
    T(["Dataset"] + METH, rows, widths=[3.2] + [2.0] * len(METH), caption=caption, size=8.5)


mt("ARI", "Table 4.4: Adjusted Rand Index (higher is better, 1 = perfect)")
mt("NMI", "Table 4.5: Normalised Mutual Information")
mt("Sil", "Table 4.6: Silhouette coefficient (internal index)")
mt("Overlap", "Table 4.7: Convex-hull overlap (fraction of points inside another cluster's hull; lower = more separable)")
H3("4.4.3 Robustness to noise")
P("Figure 4.6 shows ARI as a function of noise for two moons, averaged over five random seeds, for all methods, including DBSCAN and the mutual-reachability MST variant (MST-MR, k = 10).")
F("figures/noise_robustness.png", "Figure 4.6: Noise robustness on Two Moons (mean ARI, error bars: std over 5 seeds)", 12.5)
NR = R["noise"]["res"]; LV = R["noise"]["levels"]
rows = [[m] + [f"{a:.2f}" for a, b in v] for m, v in NR.items()]
T(["Method"] + [f"{l:.2f}" for l in LV], rows, widths=[3.6] + [1.9] * len(LV), caption="Table 4.8: Mean ARI versus noise standard deviation (Two Moons)", size=9)
H3("4.4.4 Parameter sensitivity")
P("Figure 4.7 shows the effect of the Zahn ratio threshold. A low threshold fragments the data into many small clusters, because ordinary random variation in edge length is classified as inconsistent; a threshold of 3 or more gives the true two clusters on all three data sets, and a very large threshold (4.0 on moons) merges everything into one cluster.")
F("figures/sensitivity.png", "Figure 4.7: Sensitivity of Zahn-mode MST clustering to the ratio threshold", 11.5)
SN = R["sens"]; rt = SN["rt"]
rows = [[n] + [f"{a:.2f} (K={k})" for a, k in v] for n, v in SN["res"].items()]
T(["Dataset"] + [f"t={t}" for t in rt], rows, widths=[3.4] + [2.1] * len(rt), caption="Table 4.9: ARI and number of clusters K found versus ratio threshold t", size=8.5)
H3("4.4.5 Outlier handling")
O = R["outl"]
P(f"Figure 4.8 adds 25 uniformly distributed outliers to the two-moons data. With the size guard (m = 20) the k-cut mode still returns the two moons, with ARI = {O['ARI_inliers_kcut']:.2f} on the inliers. In Zahn mode without the guard (m = 1) the method finds {O['zahn_min1_K']} clusters because each outlier cluster is cut off; with m = 20 it finds {O['zahn_min20_K']} clusters. This demonstrates the role of the size guard.")
F("figures/outliers.png", "Figure 4.8: Effect of the minimum-cluster-size guard on data with 25 outliers", 16)
H3("4.4.6 Scalability")
P("Figure 4.9 compares the time for MST construction (dense and Delaunay), Ward and K-Means for increasing n on the two-moons generator.")
F("figures/scalability.png", "Figure 4.9: Run-time versus number of points (log-log)", 11.5)
S = R["scal"]; sz = S["sizes"]
rows = []
for m, v in S["res"].items():
    rows.append([m] + ["-" if x is None else f"{x:.3f}" for x in v])
T(["Method (seconds)"] + [str(s) for s in sz], rows, widths=[3.8] + [1.9] * len(sz), caption="Table 4.10: Run-time in seconds (a dash means not run: memory / time)", size=9)
H3("4.4.7 Real data sets")
RL = R["real"]
rows = []
for d, v in RL.items():
    rows.append([d] + [f"{v[m]['ARI']:.2f}" for m in METH])
T(["Dataset"] + METH, rows, widths=[3.2] + [2.0] * len(METH), caption="Table 4.11: ARI on real data sets", size=8.5)
H2("4.5 Analysis")
H3("4.5.1 Non-convex benchmarks")
km = M["Two Moons"]["K-Means"]["ARI"]; gm = M["Two Moons"]["GMM"]["ARI"]; wd = M["Two Moons"]["Ward"]["ARI"]
P(f"On the three non-convex data sets, the MST k-cut method recovers the ground truth exactly (ARI = 1.00). K-Means, GMM and Ward give ARI of {km:.2f}, {gm:.2f} and {wd:.2f} on two moons and about 0.00 on the concentric circles and spirals. The reason is geometrical (Figure 4.5): K-Means partitions space with a straight line between two centroids, which cuts both moons across; on concentric circles any line through the common centre splits both rings into halves, so the result is independent of the true structure. GMM and Ward fail for the same reason because their cluster model is compact and unimodal. The MST, which only looks at local connectivity, is blind to global shape and therefore insensitive to curvature or nesting.")
P(f"The Zahn automatic mode with threshold 3.0 also gives ARI = 1.00 on moons and circles and {M['Two Spirals']['MST (Zahn)']['ARI']:.2f} on the spirals, where it splits one arm into an extra small cluster ({M['Two Spirals']['MST (Zahn)']['K']} clusters found). It therefore discovers the number of clusters automatically on these data, but it does so only after the threshold has been set appropriately, and this setting was informed by the same data (Table 4.9), so the result is optimistic.")
H3("4.5.2 Compact clusters")
P("On the Gaussian and anisotropic blobs, all methods, including MST, reach ARI of about 1.00 because the clusters are well separated. The MST therefore does not sacrifice accuracy on easy data. A practical consequence is that the MST can be used as a general-purpose method when the cluster shape is unknown, provided that the clusters are separated by a gap.")
H3("4.5.3 MST k-cut is single linkage - what does the size guard add?")
P("In Table 4.4, the MST k-cut column equals the single-linkage column, as theory predicts [5]. The difference becomes visible under noise and outliers (Table 4.8, Figure 4.8). At noise 0.15 the MST with size guard reaches ARI of 0.92 whereas plain single linkage collapses to 0.00, because the noisy points create chains and isolated points whose cutting wastes the cut budget. The guard is therefore the practical contribution that makes MST clustering usable on imperfect data. The mutual-reachability variant brings a small further improvement at 0.20 (0.27 versus 0.13), but with a standard deviation of 0.15 across seeds this difference should not be regarded as statistically significant; it is not claimed as a robust gain.")
H3("4.5.4 Limits under noise and overlap")
P("Above noise 0.20 all methods fail, MST included (Figure 4.6): when the two moons overlap, no gap exists, so the bridge edge is no longer the longest, and the tree contains many bridging edges. In this regime, conventional methods retain an ARI of about 0.45 only because their prediction of a straight split correlates weakly with the label, not because they find the structure. DBSCAN, which is the closest competitor for non-convex data, falls to ARI of 0.20 at noise 0.10 and to zero beyond, because a single eps cannot adapt; the MST with size guard is more stable up to 0.15. The Zahn mode is the least robust of the MST variants (Table 4.8), since high noise produces many spuriously inconsistent edges.")
H3("4.5.5 Internal indices are misleading for non-convex clusters")
P(f"A notable observation from Tables 4.6 and 4.7 is that the **correct** MST partition has the **lower** silhouette ({M['Two Moons']['MST (k-cut)']['Sil']:.2f}) than the wrong K-Means partition ({M['Two Moons']['K-Means']['Sil']:.2f}) on two moons, and a hull overlap of {M['Two Moons']['MST (k-cut)']['Overlap']:.2f} versus {M['Two Moons']['K-Means']['Overlap']:.2f}. For concentric circles the figures are {M['Concentric Circles']['MST (k-cut)']['Sil']:.2f} versus {M['Concentric Circles']['K-Means']['Sil']:.2f} for the silhouette and {M['Concentric Circles']['MST (k-cut)']['Overlap']:.2f} versus {M['Concentric Circles']['K-Means']['Overlap']:.2f} for the hull overlap. Both indices are built on the assumption of compactness and convexity and so reward precisely the kind of partition that the study shows to be wrong. This is a structural difference between the two families of method: conventional partitioning optimises a compactness objective, so it scores well on compactness indices by construction, whereas the MST clusters are defined by connectivity. Practitioners should not use silhouette alone to choose between methods when non-convex structure is possible; connectivity-aware indices (such as density-based cluster validity) are preferable.")
H3("4.5.6 Cluster structure: summary of differences")
T(["Aspect", "Conventional partitioning", "MST-based clustering"], [
    ["Cluster model", "Centroid / Gaussian: one prototype per cluster", "Connected chain of near neighbours; no prototype"],
    ["Decision boundary", "Linear / quadratic, Voronoi-like", "Arbitrary; follows data gaps"],
    ["Cluster shape", "Convex, similar size", "Any shape, any size"],
    ["Hull overlap of clusters", "Zero by construction (convex cells)", "May be large (nested, interleaved)"],
    ["Number of clusters", "Must be given", "Given (k-cut) or discovered (Zahn)"],
    ["Outliers", "Pulled into nearest cluster", "Isolated by size guard or kept as tiny components"],
    ["Cost", "O(nkd) per iteration", "O(n^2) dense, O(n log n) planar"],
    ["Failure mode", "Non-convex data", "Overlapping, noisy or high-dimensional data"],
], widths=[3.4, 6.0, 6.0], caption="Table 4.12: Structure of clusters produced by the two families", size=9.5)
H3("4.5.7 Real data: where the MST does not win")
P(f"On the real data sets the MST is **not** competitive. On Iris, GMM obtains ARI of {RL['Iris']['GMM']['ARI']:.2f} and K-Means {RL['Iris']['K-Means']['ARI']:.2f}, against {RL['Iris']['MST (k-cut)']['ARI']:.2f} for MST k-cut; on Wine, K-Means obtains {RL['Wine']['K-Means']['ARI']:.2f} against {RL['Wine']['MST (k-cut)']['ARI']:.2f}. On Digits the MST k-cut ({RL['Digits (PCA-10)']['MST (k-cut)']['ARI']:.2f}) is roughly on a par with K-Means ({RL['Digits (PCA-10)']['K-Means']['ARI']:.2f}) and Ward ({RL['Digits (PCA-10)']['Ward']['ARI']:.2f}). The Zahn mode with threshold 3.0 finds a single cluster on all three real data sets, i.e. no edge is inconsistent enough. These data have overlapping classes and no clear gaps; in high dimensions distances concentrate, and the MST edges become more uniform, which erodes the contrast between within-cluster and between-cluster edges. The negative result is important: MST clustering is a specialist for gap-separated, arbitrarily shaped clusters, not a replacement for K-Means or GMM.")
H3("4.5.8 Efficiency")
P(f"The dense MST route is quadratic: {S['res']['MST dense'][3]:.2f} s for 4,000 points, and would need roughly 2 GB for the distance matrix at 16,000. The Delaunay route is dramatically faster ({S['res']['MST Delaunay'][-1]:.3f} s for 16,000 points) and scales almost linearly in the plotted range. For two-dimensional data the MST approach is therefore practical on large sets. In higher dimensions, approximations (k-nearest-neighbour graphs, dual-tree Boruvka [16]) would be required. Note that the reported times for the MST route are for tree construction only; the pure-Python tree traversal for the size guard adds an overhead that is acceptable for the sizes tested but would be the next target for optimisation. The first K-Means timing in the raw output (about 1.5 s) includes library warm-up and should not be compared with the others.")
H3("4.5.9 Threats to validity")
B([
    "Synthetic benchmarks were generated with fixed seeds; the Zahn threshold was selected using the same data used for reporting. A held-out tuning protocol would be needed for an unbiased estimate.",
    "ARI differences below about 0.1 on noisy data are within the seed-to-seed standard deviation (Table 4.8) and are not claimed as significant.",
    "Only Euclidean distance and two-dimensional non-convex data were studied; no claims are made for high-dimensional manifolds.",
    "Baseline hyper-parameters (e.g. DBSCAN eps) were set by a simple rule and not tuned exhaustively; DBSCAN could be improved with a per-case search.",
])

# ------------------------------------------------------------------ 5 CONCLUSION
H1("5. Conclusion and Future Work")
P("This mini project developed and evaluated an MST-based clustering approach for non-linearly separable data. The principal findings are:")
B([
    "On interleaved, nested and spiral clusters, MST clustering recovers the ground truth (ARI = 1.00) where K-Means, GMM and Ward fail (ARI between about 0.00 and 0.62), because it defines clusters by connectivity and not by distance to a prototype.",
    "On compact Gaussian clusters, the MST matches the conventional methods, so there is little accuracy cost in using it when cluster shape is unknown.",
    "The minimum-cluster-size guard is what separates a usable method from plain single linkage: it keeps ARI near 0.92 at noise 0.15, where single linkage drops to 0.00.",
    "The Zahn inconsistency rule provides automatic discovery of the number of clusters, but requires a suitable threshold and is the least robust variant under noise or on real data.",
    "Silhouette and convex-hull-based indices favour the wrong, convex partitions of non-convex data and should not be used alone for model selection.",
    "For two-dimensional data the Delaunay-based construction makes the approach scale to tens of thousands of points in a fraction of a second.",
    "MST clustering fails on heavy overlap, strong noise and (in our experiments) on overlapping real data with moderate dimension, where GMM and K-Means perform better.",
])
H3("Future work")
B([
    "Replace the per-candidate breadth-first search by subtree-size bookkeeping (a single rooted traversal) for O(n log n) cutting.",
    "Use approximate k-nearest-neighbour graphs or dual-tree Boruvka for the MST in high dimensions.",
    "Select the number of clusters or the ratio threshold automatically, for example by the largest gap in the sorted edge weights or by cluster stability under resampling.",
    "Implement the two-rounds MST of Zhong et al. [12] and compare it with the guard-based approach.",
    "Use connectivity-aware validity indices (e.g. density-based validation) in the comparison.",
    "Evaluate on real non-convex data such as trajectories, image segmentation graphs and astronomical catalogues, and provide a web interface for interactive edge cutting.",
])

# ------------------------------------------------------------------ 6 REFERENCES
H1("6. References")
REFS = [
    "A. K. Jain, \"Data clustering: 50 years beyond K-means,\" Pattern Recognition Letters, vol. 31, no. 8, pp. 651-666, 2010.",
    "J. MacQueen, \"Some methods for classification and analysis of multivariate observations,\" in Proc. 5th Berkeley Symposium on Mathematical Statistics and Probability, vol. 1, pp. 281-297, 1967.",
    "S. P. Lloyd, \"Least squares quantization in PCM,\" IEEE Transactions on Information Theory, vol. 28, no. 2, pp. 129-137, 1982.",
    "J. H. Ward, \"Hierarchical grouping to optimize an objective function,\" Journal of the American Statistical Association, vol. 58, no. 301, pp. 236-244, 1963.",
    "J. C. Gower and G. J. S. Ross, \"Minimum spanning trees and single linkage cluster analysis,\" Journal of the Royal Statistical Society, Series C, vol. 18, no. 1, pp. 54-64, 1969.",
    "M. Ester, H.-P. Kriegel, J. Sander and X. Xu, \"A density-based algorithm for discovering clusters in large spatial databases with noise,\" in Proc. KDD, pp. 226-231, 1996.",
    "R. J. G. B. Campello, D. Moulavi and J. Sander, \"Density-based clustering based on hierarchical density estimates,\" in Advances in Knowledge Discovery and Data Mining (PAKDD), pp. 160-172, 2013.",
    "U. von Luxburg, \"A tutorial on spectral clustering,\" Statistics and Computing, vol. 17, no. 4, pp. 395-416, 2007.",
    "A. Y. Ng, M. I. Jordan and Y. Weiss, \"On spectral clustering: analysis and an algorithm,\" in Advances in Neural Information Processing Systems 14, 2001.",
    "C. T. Zahn, \"Graph-theoretical methods for detecting and describing Gestalt clusters,\" IEEE Transactions on Computers, vol. C-20, no. 1, pp. 68-86, 1971.",
    "Y. Xu, V. Olman and D. Xu, \"Clustering gene expression data using a graph-theoretic approach: an application of minimum spanning trees,\" Bioinformatics, vol. 18, no. 4, pp. 536-545, 2002.",
    "C. Zhong, D. Miao and R. Wang, \"A graph-theoretical clustering method based on two rounds of minimum spanning trees,\" Pattern Recognition, vol. 43, no. 3, pp. 752-766, 2010.",
    "F. Pedregosa et al., \"Scikit-learn: machine learning in Python,\" Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011.",
    "G. Karypis, E.-H. Han and V. Kumar, \"CHAMELEON: hierarchical clustering using dynamic modeling,\" IEEE Computer, vol. 32, no. 8, pp. 68-75, 1999.",
    "M. I. Shamos and D. Hoey, \"Closest-point problems,\" in Proc. 16th Annual Symposium on Foundations of Computer Science, pp. 151-162, 1975.",
    "W. B. March, P. Ram and A. G. Gray, \"Fast Euclidean minimum spanning tree: algorithm, analysis, and applications,\" in Proc. ACM KDD, pp. 603-612, 2010.",
    "L. Hubert and P. Arabie, \"Comparing partitions,\" Journal of Classification, vol. 2, no. 1, pp. 193-218, 1985.",
    "P. J. Rousseeuw, \"Silhouettes: a graphical aid to the interpretation and validation of cluster analysis,\" Journal of Computational and Applied Mathematics, vol. 20, pp. 53-65, 1987.",
    "R. C. Prim, \"Shortest connection networks and some generalizations,\" Bell System Technical Journal, vol. 36, no. 6, pp. 1389-1401, 1957.",
    "J. B. Kruskal, \"On the shortest spanning subtree of a graph and the traveling salesman problem,\" Proceedings of the American Mathematical Society, vol. 7, no. 1, pp. 48-50, 1956.",
    "P. Virtanen et al., \"SciPy 1.0: fundamental algorithms for scientific computing in Python,\" Nature Methods, vol. 17, pp. 261-272, 2020.",
]
for i, r in enumerate(REFS, 1):
    p = P(f"[{i}]  {r}", "j", after=4); p.paragraph_format.left_indent = Cm(1.0); p.paragraph_format.first_line_indent = Cm(-1.0)
    p.paragraph_format.line_spacing = 1.15

# ------------------------------------------------------------------ 7 APPENDIX
H1("7. Appendix")
H2("Appendix A - Source code: mst_clustering.py")
CODE(open("mst_clustering.py", encoding="utf-8").read(), 7.5)
H2("Appendix B - Detailed results per dataset and method")
BN = 0
for d in DS:
    rows = [[m, f"{M[d][m]['ARI']:.3f}", f"{M[d][m]['NMI']:.3f}", f"{M[d][m]['Sil']:.3f}", f"{M[d][m]['Overlap']:.3f}", M[d][m]["K"], f"{M[d][m]['time']:.3f}"] for m in METH]
    BN += 1
    T(["Method", "ARI", "NMI", "Silhouette", "Hull overlap", "K found", "Time (s)"], rows, widths=[3.4, 1.9, 1.9, 2.2, 2.4, 1.8, 1.9], caption=f"Table B.{BN}: Results on {d}", size=9)
H2("Appendix C - Reproducing the experiments")
CODE("""pip install numpy scipy scikit-learn matplotlib pandas python-docx
python experiments.py     # generates figures/*.png and results.json
python diagrams.py        # architecture / flow diagrams
python build_report.py    # assembles this report (.docx)

# minimal usage
from mst_clustering import MSTClusterer
labels = MSTClusterer(n_clusters=2, mode="k", min_size=15).fit_predict(X)
labels = MSTClusterer(mode="zahn", ratio_thr=3.0, min_size=15).fit_predict(X)""", 9)
H2("Appendix D - Glossary")
B([
    "**MST** - Minimum Spanning Tree: acyclic connected subgraph of minimum total edge weight.",
    "**ARI** - Adjusted Rand Index, chance-corrected agreement between two partitions.",
    "**NMI** - Normalised Mutual Information between two labellings.",
    "**Silhouette** - Internal index comparing mean intra-cluster distance with nearest-other-cluster distance.",
    "**Delaunay triangulation** - Triangulation in which no point lies inside the circumcircle of any triangle; contains the Euclidean MST.",
    "**Inconsistent edge** - Edge much longer than the edges in its neighbourhood in the tree.",
    "**Mutual reachability** - Distance max(core(a), core(b), d(a, b)) used to discount sparse regions.",
])
doc.save("MST_Clustering_Mini_Project_Report.docx")
json.dump([dict(level=l, key=k, search=s) for l, k, s in HEADINGS], open("headings.json", "w"))
json.dump(CAPS, open("caps.json", "w"))
print("saved")
