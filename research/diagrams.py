import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon


def box(ax, x, y, w, h, text, fc="#dbeafe", ec="#1e40af", fs=8.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p, q, text=None):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, lw=1.2, color="#374151"))
    if text:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.12, text, ha="center", fontsize=7)


# 1. high level
fig, ax = plt.subplots(figsize=(10, 2.6)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 2.6)
labels = ["Input data\n(n x d)", "Pre-processing\n(standard scaling)", "MST construction\n(dense / Delaunay)", "Edge analysis\n(weights, ratios)", "Edge cutting\n+ min-size rule", "Cluster labels\n+ evaluation"]
cols = ["#fef3c7", "#dbeafe", "#dcfce7", "#dcfce7", "#fee2e2", "#ede9fe"]
for i, (t, c) in enumerate(zip(labels, cols)):
    box(ax, 0.1 + i * 1.65, 0.8, 1.35, 1.0, t, fc=c)
    if i:
        arrow(ax, (0.1 + i * 1.65 - 0.3, 1.3), (0.1 + i * 1.65, 1.3))
ax.text(5, 2.2, "High-level view of the proposed MST-based clustering pipeline", ha="center", fontsize=10, weight="bold")
plt.savefig("figures/arch_high_level.png", bbox_inches="tight", dpi=150); plt.close()

# 2. detailed architecture
fig, ax = plt.subplots(figsize=(10, 6.6)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 6.6)
ax.text(5, 6.35, "Detailed architecture", ha="center", fontsize=11, weight="bold")
ax.add_patch(FancyBboxPatch((0.15, 4.6), 9.7, 1.5, boxstyle="round,pad=0.02", fc="#f9fafb", ec="#9ca3af", ls="--"))
ax.text(0.3, 5.9, "Layer 1: Data & graph construction", fontsize=8, style="italic")
box(ax, 0.4, 4.8, 1.8, 0.9, "Dataset loader\n(synthetic + real)", "#fef3c7")
box(ax, 2.6, 4.8, 1.8, 0.9, "StandardScaler\nzero mean, unit var", "#dbeafe")
box(ax, 4.8, 4.8, 2.2, 0.9, "Distance weights\nEuclidean or\nmutual-reachability", "#dcfce7")
box(ax, 7.4, 4.8, 2.2, 0.9, "Candidate graph\ncomplete (d>2) or\nDelaunay (2-D, large n)", "#dcfce7")
for a, b in [(2.2, 2.6), (4.4, 4.8), (7.0, 7.4)]:
    arrow(ax, (a, 5.25), (b, 5.25))
ax.add_patch(FancyBboxPatch((0.15, 2.7), 9.7, 1.6, boxstyle="round,pad=0.02", fc="#f9fafb", ec="#9ca3af", ls="--"))
ax.text(0.3, 4.1, "Layer 2: MST core & edge analysis", fontsize=8, style="italic")
box(ax, 0.4, 2.9, 2.2, 1.0, "Kruskal / Prim MST\n(SciPy csgraph)\nn-1 edges (u, v, w)", "#dcfce7")
box(ax, 3.0, 2.9, 2.2, 1.0, "Tree adjacency\nlist + edge ids", "#dcfce7")
box(ax, 5.6, 2.9, 1.9, 1.0, "Zahn inconsistency\nratio  w / mean(w_nbr)\ndepth = 3", "#fee2e2")
box(ax, 7.8, 2.9, 1.8, 1.0, "Edge ranking\n(descending weight)", "#fee2e2")
for a, b in [(2.6, 3.0), (5.2, 5.6), (7.5, 7.8)]:
    arrow(ax, (a, 3.4), (b, 3.4))
arrow(ax, (8.5, 4.8), (1.5, 3.9))
ax.add_patch(FancyBboxPatch((0.15, 0.7), 9.7, 1.7, boxstyle="round,pad=0.02", fc="#f9fafb", ec="#9ca3af", ls="--"))
ax.text(0.3, 2.2, "Layer 3: Partitioning & evaluation", fontsize=8, style="italic")
box(ax, 0.4, 0.9, 2.3, 1.1, "Cut controller\nmode k: first k-1 edges\nmode zahn: ratio > thr", "#fee2e2")
box(ax, 3.1, 0.9, 2.3, 1.1, "Min-size guard\nboth sides >= m ?\naccept : treat as outlier link", "#fee2e2")
box(ax, 5.8, 0.9, 1.8, 1.1, "Connected components\n= cluster labels", "#ede9fe")
box(ax, 8.0, 0.9, 1.7, 1.1, "Metrics: ARI, NMI,\nSilhouette, hull\noverlap, runtime", "#ede9fe")
for a, b in [(2.7, 3.1), (5.4, 5.8), (7.6, 8.0)]:
    arrow(ax, (a, 1.45), (b, 1.45))
arrow(ax, (8.7, 2.9), (1.5, 2.0))
plt.savefig("figures/arch_detailed.png", bbox_inches="tight", dpi=150); plt.close()

# 3. operational flow
fig, ax = plt.subplots(figsize=(7, 8.6)); ax.axis("off"); ax.set_xlim(0, 7); ax.set_ylim(0, 8.6)
box(ax, 2.3, 7.9, 2.4, 0.5, "START: load X, choose mode", "#fef3c7")
box(ax, 2.3, 7.1, 2.4, 0.5, "Standardise features", "#dbeafe")
box(ax, 2.3, 6.3, 2.4, 0.5, "Build weighted graph G", "#dcfce7")
box(ax, 2.3, 5.5, 2.4, 0.5, "T = MST(G), n-1 edges", "#dcfce7")
for y in [7.9, 7.1, 6.3]:
    arrow(ax, (3.5, y), (3.5, y - 0.3))
ax.add_patch(Polygon([[3.5, 5.5], [5.0, 4.75], [3.5, 4.0], [2.0, 4.75]], fc="#fef9c3", ec="#a16207"))
ax.text(3.5, 4.75, "mode = k ?", ha="center", va="center", fontsize=8.5)
arrow(ax, (3.5, 5.5), (3.5, 5.5))
box(ax, 0.1, 3.0, 2.6, 0.7, "Sort edges by weight\ndescending", "#fee2e2")
box(ax, 4.3, 3.0, 2.6, 0.7, "Compute ratio per edge,\ncandidates: ratio > thr", "#fee2e2")
arrow(ax, (2.0, 4.75), (1.4, 3.7), "yes")
arrow(ax, (5.0, 4.75), (5.6, 3.7), "no (Zahn)")
box(ax, 2.3, 2.0, 2.4, 0.7, "Take next candidate edge e", "#fee2e2")
arrow(ax, (1.4, 3.0), (2.8, 2.7)); arrow(ax, (5.6, 3.0), (4.2, 2.7))
ax.add_patch(Polygon([[3.5, 1.9], [5.1, 1.35], [3.5, 0.8], [1.9, 1.35]], fc="#fef9c3", ec="#a16207"))
ax.text(3.5, 1.35, "both parts >= m\nand cuts < limit?", ha="center", va="center", fontsize=7.5)
arrow(ax, (3.5, 2.0), (3.5, 1.9))
ax.text(5.6, 1.4, "yes: remove e\nno: skip e\n(loop)", fontsize=7.5)
box(ax, 2.3, 0.0, 2.4, 0.5, "Label components, evaluate; END", "#ede9fe")
arrow(ax, (3.5, 0.8), (3.5, 0.5))
plt.savefig("figures/arch_flow.png", bbox_inches="tight", dpi=150); plt.close()
print("ok")
