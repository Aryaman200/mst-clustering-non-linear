"""Clustering engine used by the dashboard: datasets, methods, metrics."""
import io, os, sys, time, math
import numpy as np
from sklearn import datasets as skd
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (adjusted_rand_score, normalized_mutual_info_score,
                             silhouette_score)
from scipy.spatial import Delaunay

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "research"))
from mst_clustering import MSTClusterer  # noqa: E402

MAX_POINTS = 3000

DATASETS = {
    "moons": "Two Moons",
    "circles": "Concentric Circles",
    "spirals": "Two Spirals",
    "aniso": "Anisotropic Blobs",
    "blobs": "Gaussian Blobs",
    "moons_outliers": "Moons + 5% Outliers",
}
METHODS = ["K-Means", "GMM", "Ward", "Single-Link", "DBSCAN",
           "MST (k-cut)", "MST (Zahn)", "MST-MR (k-cut)"]
DEFAULT_NOISE = {"moons": 0.06, "circles": 0.05, "spirals": 0.03, "aniso": 0.0, "blobs": 0.07, "moons_outliers": 0.05}
DEFAULT_K = {"moons": 2, "circles": 2, "spirals": 2, "aniso": 3, "blobs": 3, "moons_outliers": 2}


def _spirals(n, noise, seed):
    r = np.random.RandomState(seed); m = n // 2
    t = 1.5 + r.rand(m) * 2.2 * np.pi
    a = np.c_[-np.cos(t) * t, np.sin(t) * t] / 10
    X = np.vstack([a, -a]) + r.randn(2 * m, 2) * noise
    return X, np.r_[np.zeros(m), np.ones(m)].astype(int)


def _centers(rs):
    """Fixed cluster centres (independent of the point-sampling seed)."""
    return skd.make_blobs(30, centers=3, random_state=rs, return_centers=True)[2]


def make_dataset(name, n, noise, seed):
    if name == "moons":
        return skd.make_moons(n, noise=noise, random_state=seed)
    if name == "circles":
        return skd.make_circles(n, factor=0.4, noise=noise, random_state=seed)
    if name == "spirals":
        return _spirals(n, noise, seed)
    if name == "aniso":
        centers = _centers(42)
        X, y = skd.make_blobs(n, centers=centers, cluster_std=1.0 + 5 * noise, random_state=seed)
        return X @ np.array([[0.6, -0.6], [-0.4, 0.8]]), y
    if name == "blobs":
        return skd.make_blobs(n, centers=_centers(7), cluster_std=0.5 + 6 * noise, random_state=seed)
    if name == "moons_outliers":
        no = max(1, int(0.05 * n))
        X, y = skd.make_moons(n - no, noise=noise, random_state=seed)
        r = np.random.RandomState(seed + 1)
        lo, hi = X.min(0) - 0.5, X.max(0) + 0.5
        return np.vstack([X, r.uniform(lo, hi, (no, 2))]), np.r_[y, -np.ones(no, int)]
    raise ValueError(f"unknown dataset {name}")


def parse_csv(text, has_label):
    rows = []
    for line in io.StringIO(text):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.replace(";", ",").replace("\t", ",").split(",")]
        rows.append(parts)
    if not rows:
        raise ValueError("empty CSV")
    try:
        [float(v) for v in rows[0][: max(1, len(rows[0]) - (1 if has_label else 0))]]
    except ValueError:
        rows = rows[1:]  # header
    y = None
    if has_label:
        labs = [r[-1] for r in rows]
        uniq = {u: i for i, u in enumerate(sorted(set(labs)))}
        y = np.array([uniq[l] for l in labs])
        rows = [r[:-1] for r in rows]
    X = np.array([[float(v) for v in r] for r in rows])
    if len(X) < 10 or X.shape[1] < 2:
        raise ValueError("need at least 10 rows and 2 numeric columns")
    return X, y


def hull_overlap(X2, y):
    inside = 0
    for l in [l for l in np.unique(y) if l >= 0]:
        P = X2[y == l]
        if len(P) < 4:
            continue
        try:
            d = Delaunay(P)
        except Exception:
            continue
        inside += int((d.find_simplex(X2[y != l]) >= 0).sum())
    return inside / len(X2)


def run_method(name, X, k, p):
    n = len(X)
    ms = int(p.get("min_size") or max(10, n // 40))
    if name == "K-Means":
        return KMeans(k, n_init=10, random_state=0).fit_predict(X), None
    if name == "GMM":
        return GaussianMixture(k, n_init=3, random_state=0).fit_predict(X), None
    if name == "Ward":
        return AgglomerativeClustering(k, linkage="ward").fit_predict(X), None
    if name == "Single-Link":
        return AgglomerativeClustering(k, linkage="single").fit_predict(X), None
    if name == "DBSCAN":
        return DBSCAN(eps=float(p.get("eps", 0.25)), min_samples=int(p.get("minpts", 5))).fit_predict(X), None
    if name == "MST (k-cut)":
        m = MSTClusterer(k, "k", ms)
    elif name == "MST (Zahn)":
        m = MSTClusterer(mode="zahn", min_size=ms, ratio_thr=float(p.get("ratio", 3.0)), depth=int(p.get("depth", 3)))
    elif name == "MST-MR (k-cut)":
        m = MSTClusterer(k, "k", ms, mreach_k=int(p.get("mreach_k", 10)))
    else:
        raise ValueError(f"unknown method {name}")
    y = m.fit_predict(X)
    return y, m


def _num(v):
    if v is None:
        return None
    v = float(v)
    return None if math.isnan(v) or math.isinf(v) else round(v, 4)


def evaluate(X, truth, y, X2):
    labs = np.unique(y)
    out = {"K": int(len(labs[labs >= 0])), "noise_points": int((y < 0).sum())}
    out["ARI"] = _num(adjusted_rand_score(truth, y)) if truth is not None else None
    out["NMI"] = _num(normalized_mutual_info_score(truth, y)) if truth is not None else None
    mask = y >= 0
    try:
        out["Silhouette"] = _num(silhouette_score(X[mask], y[mask])) if len(np.unique(y[mask])) > 1 and mask.sum() > 2 else None
    except Exception:
        out["Silhouette"] = None
    out["Overlap"] = _num(hull_overlap(X2, y)) if X.shape[1] == 2 and len(labs) > 1 else None
    return out


def cluster(req):
    seed = int(req.get("seed", 0))
    if req.get("csv"):
        X, truth = parse_csv(req["csv"], bool(req.get("has_label")))
        k = int(req.get("k") or (len(np.unique(truth)) if truth is not None else 2))
        title = "Uploaded data"
    else:
        name = req.get("dataset", "moons")
        n = int(min(max(int(req.get("n", 600)), 50), MAX_POINTS))
        noise = float(req.get("noise", 0.06))
        X, truth = make_dataset(name, n, noise, seed)
        k = int(req.get("k") or DEFAULT_K[name])
        title = DATASETS[name]
    if len(X) > MAX_POINTS:
        idx = np.random.RandomState(0).choice(len(X), MAX_POINTS, replace=False)
        X = X[idx]; truth = truth[idx] if truth is not None else None
    X = StandardScaler().fit_transform(X)
    X2 = X if X.shape[1] == 2 else PCA(2, random_state=0).fit_transform(X)
    k = max(1, min(k, 20))
    params = req.get("params", {})
    res = {"title": title, "n": int(len(X)), "d": int(X.shape[1]), "k": k,
           "points": np.round(X2, 4).tolist(),
           "truth": truth.astype(int).tolist() if truth is not None else None,
           "methods": {}}
    for name in req.get("methods", METHODS):
        if name not in METHODS:
            continue
        try:
            t0 = time.perf_counter()
            y, m = run_method(name, X, k, params)
            dt = time.perf_counter() - t0
            entry = {"labels": [int(v) for v in y], "time_ms": round(dt * 1000, 1)}
            entry.update(evaluate(X, truth, y, X2))
            if m is not None:
                entry["edges"] = [[int(u), int(v)] for u, v, _ in m.edges_]
                entry["cut"] = [int(i) for i in m.removed_]
            res["methods"][name] = entry
        except Exception as e:  # keep dashboard alive
            res["methods"][name] = {"error": str(e)}
    return res


def noise_sweep(dataset="moons", n=400, seeds=3, levels=(0.03, 0.06, 0.10, 0.15, 0.20, 0.30)):
    names = ["K-Means", "Ward", "Single-Link", "DBSCAN", "MST (k-cut)", "MST-MR (k-cut)"]
    out = {m: [] for m in names}
    for nz in levels:
        acc = {m: [] for m in names}
        for s in range(seeds):
            X, y = make_dataset(dataset, n, nz, s)
            X = StandardScaler().fit_transform(X)
            for m in names:
                yy, _ = run_method(m, X, DEFAULT_K[dataset], {"eps": 0.2 + nz})
                acc[m].append(adjusted_rand_score(y, yy))
        for m in names:
            out[m].append(round(float(np.mean(acc[m])), 3))
    return {"levels": list(levels), "series": out, "dataset": DATASETS[dataset], "seeds": seeds}


def scalability(sizes=(500, 1000, 2000, 4000, 8000, 16000)):
    from mst_clustering import build_mst
    out = {"sizes": list(sizes), "series": {"K-Means": [], "Ward": [], "MST dense": [], "MST Delaunay": []}}
    for n in sizes:
        X, _ = skd.make_moons(n, noise=0.06, random_state=0)
        t = time.perf_counter(); KMeans(2, n_init=1, random_state=0).fit(X); out["series"]["K-Means"].append(round(time.perf_counter() - t, 4))
        if n <= 4000:
            t = time.perf_counter(); AgglomerativeClustering(2).fit(X); out["series"]["Ward"].append(round(time.perf_counter() - t, 4))
            t = time.perf_counter(); build_mst(X, "dense"); out["series"]["MST dense"].append(round(time.perf_counter() - t, 4))
        else:
            out["series"]["Ward"].append(None); out["series"]["MST dense"].append(None)
        t = time.perf_counter(); build_mst(X, "delaunay"); out["series"]["MST Delaunay"].append(round(time.perf_counter() - t, 4))
    return out
