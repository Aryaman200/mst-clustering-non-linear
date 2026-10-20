import json, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn import datasets
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score as ARI, normalized_mutual_info_score as NMI, silhouette_score
from scipy.spatial import Delaunay
from mst_clustering import MSTClusterer, build_mst

rng = 42
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 130})
PAL = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b"]


def col(y):
    return [PAL[i % 6] if i >= 0 else "#888888" for i in y]


def spirals(n=600, noise=0.05, seed=rng):
    r = np.random.RandomState(seed); m = n // 2
    t = 1.5 + r.rand(m) * 2.2 * np.pi
    a = np.c_[-np.cos(t) * t, np.sin(t) * t] / 10
    X = np.vstack([a, -a]) + r.randn(2 * m, 2) * noise
    return X, np.r_[np.zeros(m), np.ones(m)].astype(int)


def aniso(n=600, seed=rng):
    X, y = datasets.make_blobs(n, centers=3, random_state=seed)
    return X @ np.array([[0.6, -0.6], [-0.4, 0.8]]), y


DATA = {
    "Two Moons": (lambda: datasets.make_moons(600, noise=0.06, random_state=rng), 2),
    "Concentric Circles": (lambda: datasets.make_circles(600, factor=0.4, noise=0.05, random_state=rng), 2),
    "Two Spirals": (lambda: spirals(800, 0.03), 2),
    "Anisotropic Blobs": (lambda: aniso(600), 3),
    "Gaussian Blobs": (lambda: datasets.make_blobs(600, centers=3, cluster_std=0.9, random_state=7), 3),
}


def methods(k, n):
    ms = max(10, n // 40)
    return {
        "K-Means": lambda X: KMeans(k, n_init=10, random_state=rng).fit_predict(X),
        "GMM": lambda X: GaussianMixture(k, n_init=5, random_state=rng).fit_predict(X),
        "Ward": lambda X: AgglomerativeClustering(k, linkage="ward").fit_predict(X),
        "Single-Link": lambda X: AgglomerativeClustering(k, linkage="single").fit_predict(X),
        "MST (k-cut)": lambda X: MSTClusterer(k, "k", ms).fit_predict(X),
        "MST (Zahn)": lambda X: MSTClusterer(mode="zahn", min_size=ms, ratio_thr=3.0).fit_predict(X),
    }


def hull_overlap(X, y):
    """Fraction of all points lying inside the convex hull of a different cluster."""
    inside = 0
    for l in [l for l in np.unique(y) if l >= 0]:
        P = X[y == l]
        if len(P) < 4:
            continue
        try:
            d = Delaunay(P)
        except Exception:
            continue
        inside += (d.find_simplex(X[y != l]) >= 0).sum()
    return inside / len(X)


def sil(X, y):
    return silhouette_score(X, y) if len(np.unique(y)) > 1 else float("nan")


res = {}
fig, axes = plt.subplots(len(DATA), 7, figsize=(17, 2.6 * len(DATA)))
for r, (name, (gen, k)) in enumerate(DATA.items()):
    X, yt = gen()
    X = StandardScaler().fit_transform(X)
    axes[r, 0].scatter(*X.T, c=col(yt), s=5)
    axes[r, 0].set_title(f"{name}\n(ground truth)")
    res[name] = {}
    for c, (mn, f) in enumerate(methods(k, len(X)).items(), 1):
        t0 = time.perf_counter(); y = f(X); dt = time.perf_counter() - t0
        res[name][mn] = dict(ARI=ARI(yt, y), NMI=NMI(yt, y), Sil=sil(X, y),
                             Overlap=hull_overlap(X, y), K=int(len(np.unique(y))), time=dt)
        axes[r, c].scatter(*X.T, c=col(y), s=5)
        axes[r, c].set_title(f"{mn}\nARI={res[name][mn]['ARI']:.2f}")
    for a in axes[r]:
        a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig("figures/comparison_grid.png"); plt.close()

for name in ["Two Moons", "Two Spirals", "Concentric Circles"]:
    gen, k = DATA[name]; X, yt = gen(); X = StandardScaler().fit_transform(X)
    m = MSTClusterer(k, "k", 15); y = m.fit_predict(X)
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    E = m.edges_; cut = set(m.removed_)
    for i, (u, v, w) in enumerate(E):
        ax[0].plot(*X[[int(u), int(v)]].T, c="gray", lw=0.5)
        ax[1].plot(*X[[int(u), int(v)]].T, c="red" if i in cut else "lightgray", lw=2.5 if i in cut else 0.5)
    ax[0].scatter(*X.T, s=4, c="k"); ax[0].set_title("Euclidean MST")
    ax[1].scatter(*X.T, s=4, c="k"); ax[1].set_title("Cut edges in red")
    ax[2].scatter(*X.T, c=col(y), s=6); ax[2].set_title(f"Resulting clusters (ARI={ARI(yt, y):.2f})")
    for a in ax:
        a.set_xticks([]); a.set_yticks([])
    plt.tight_layout(); plt.savefig(f"figures/mst_steps_{name.replace(' ', '_').lower()}.png"); plt.close()

X, yt = DATA["Two Moons"][0](); X = StandardScaler().fit_transform(X)
E = build_mst(X); w = np.sort(E[:, 2])[::-1]
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
ax[0].hist(E[:, 2], bins=40, color="#1f77b4"); ax[0].set_title("MST edge-weight histogram (Two Moons)"); ax[0].set_xlabel("weight")
ax[1].plot(w[:30], "o-", ms=3); ax[1].set_title("30 largest MST edge weights"); ax[1].set_xlabel("rank"); ax[1].set_ylabel("weight")
plt.tight_layout(); plt.savefig("figures/edge_weights.png"); plt.close()

levels = [0.03, 0.06, 0.10, 0.15, 0.20, 0.30]
nr = {m: [] for m in ["K-Means", "GMM", "Ward", "Single-Link", "MST (k-cut)", "MST (Zahn)", "MST-MR (k=10)", "DBSCAN"]}
for nz in levels:
    accs = {m: [] for m in nr}
    for s in range(5):
        X, yt = datasets.make_moons(600, noise=nz, random_state=s); X = StandardScaler().fit_transform(X)
        for mn, f in methods(2, 600).items():
            accs[mn].append(ARI(yt, f(X)))
        accs["MST-MR (k=10)"].append(ARI(yt, MSTClusterer(2, "k", 15, mreach_k=10).fit_predict(X)))
        accs["DBSCAN"].append(ARI(yt, DBSCAN(eps=0.2 + nz, min_samples=5).fit_predict(X)))
    for m in nr:
        nr[m].append((float(np.mean(accs[m])), float(np.std(accs[m]))))
fig, ax = plt.subplots(figsize=(6.2, 3.8))
for m, v in nr.items():
    ax.errorbar(levels, [a for a, _ in v], yerr=[b for _, b in v], marker="o", ms=3, capsize=2, label=m)
ax.set_xlabel("Gaussian noise (std)"); ax.set_ylabel("ARI (mean of 5 seeds)"); ax.set_title("Noise robustness on Two Moons")
ax.legend(fontsize=7); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig("figures/noise_robustness.png"); plt.close()

sizes = [500, 1000, 2000, 4000, 8000, 16000]
sc = {"K-Means": [], "Ward": [], "MST dense": [], "MST Delaunay": []}
for n in sizes:
    X, _ = datasets.make_moons(n, noise=0.06, random_state=0)
    t = time.perf_counter(); KMeans(2, n_init=3, random_state=0).fit(X); sc["K-Means"].append(time.perf_counter() - t)
    if n <= 8000:
        t = time.perf_counter(); AgglomerativeClustering(2).fit(X); sc["Ward"].append(time.perf_counter() - t)
    else:
        sc["Ward"].append(None)
    if n <= 4000:
        t = time.perf_counter(); build_mst(X, "dense"); sc["MST dense"].append(time.perf_counter() - t)
    else:
        sc["MST dense"].append(None)
    t = time.perf_counter(); build_mst(X, "delaunay"); sc["MST Delaunay"].append(time.perf_counter() - t)
fig, ax = plt.subplots(figsize=(6, 3.6))
for m, v in sc.items():
    xs = [s for s, t in zip(sizes, v) if t is not None]; ys = [t for t in v if t is not None]
    ax.loglog(xs, ys, "o-", ms=3, label=m)
ax.set_xlabel("n points"); ax.set_ylabel("seconds"); ax.set_title("MST construction vs baselines (runtime)")
ax.legend(fontsize=7); ax.grid(alpha=.3, which="both")
plt.tight_layout(); plt.savefig("figures/scalability.png"); plt.close()

rt = [1.2, 1.5, 2.0, 2.5, 3.0, 4.0]
sens = {}
for name in ["Two Moons", "Two Spirals", "Concentric Circles"]:
    X, yt = DATA[name][0](); X = StandardScaler().fit_transform(X)
    sens[name] = []
    for t in rt:
        y = MSTClusterer(mode="zahn", min_size=15, ratio_thr=t).fit_predict(X)
        sens[name].append((float(ARI(yt, y)), int(len(np.unique(y)))))
fig, ax = plt.subplots(figsize=(6, 3.4))
for name, v in sens.items():
    ax.plot(rt, [a for a, _ in v], "o-", label=name)
ax.set_xlabel("ratio threshold"); ax.set_ylabel("ARI"); ax.set_title("Zahn ratio-threshold sensitivity (min size = 15)")
ax.legend(fontsize=7); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig("figures/sensitivity.png"); plt.close()

real = {}
for nm, k in {"Iris": 3, "Wine": 3, "Digits (PCA-10)": 10}.items():
    if nm == "Iris":
        X, y = datasets.load_iris(return_X_y=True)
    elif nm == "Wine":
        X, y = datasets.load_wine(return_X_y=True)
    else:
        d = datasets.load_digits(); X = PCA(10, random_state=0).fit_transform(StandardScaler().fit_transform(d.data)); y = d.target
    X = StandardScaler().fit_transform(X)
    real[nm] = {}
    for mn, f in methods(k, len(X)).items():
        yy = f(X); real[nm][mn] = dict(ARI=ARI(y, yy), NMI=NMI(y, yy), K=int(len(np.unique(yy))))

X, yt = datasets.make_moons(500, noise=0.05, random_state=1)
out = np.random.RandomState(3).uniform(-1.5, 2.5, (25, 2))
Xo = StandardScaler().fit_transform(np.vstack([X, out]))
fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
mk = MSTClusterer(2, "k", 20).fit_predict(Xo)
mz = MSTClusterer(mode="zahn", min_size=1, ratio_thr=3.0).fit_predict(Xo)
mz2 = MSTClusterer(mode="zahn", min_size=20, ratio_thr=3.0).fit_predict(Xo)
for a, y, t in zip(ax, [mk, mz, mz2], ["k-cut, min_size=20", "Zahn, min_size=1", "Zahn, min_size=20"]):
    a.scatter(*Xo.T, c=col(y), s=6); a.set_title(f"{t}\nclusters={len(np.unique(y))}"); a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig("figures/outliers.png"); plt.close()
outl = {"kcut_K": int(len(np.unique(mk))), "zahn_min1_K": int(len(np.unique(mz))), "zahn_min20_K": int(len(np.unique(mz2))),
        "ARI_inliers_kcut": float(ARI(yt, mk[:500])), "ARI_inliers_zahn20": float(ARI(yt, mz2[:500])),
        "ARI_inliers_zahn1": float(ARI(yt, mz[:500]))}

json.dump(dict(main=res, noise=dict(levels=levels, res=nr), scal=dict(sizes=sizes, res=sc), sens=dict(rt=rt, res=sens), real=real, outl=outl),
          open("results.json", "w"), indent=1, default=float)
print("done")
