"""MST-based clustering for non-linearly separable data.

Implements:
  * Euclidean MST (dense via SciPy, or Delaunay-accelerated for 2-D data)
  * Zahn-style inconsistent-edge cutting (number of clusters found automatically)
  * k-cut with minimum cluster size (cut the k-1 largest admissible edges)
"""
import numpy as np
from collections import deque
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial import Delaunay, distance_matrix


def build_mst(X, method="auto", mreach_k=0):
    """Return MST edges as array (n-1, 3): u, v, weight.

    mreach_k > 0 replaces Euclidean weights by mutual-reachability distance
    max(core_k(a), core_k(b), d(a, b)), which makes long edges in sparse
    (noisy) regions heavier and so more robust to noise/bridges.
    """
    n = len(X)
    core = None
    if mreach_k > 0:
        D = distance_matrix(X, X)
        core = np.partition(D, mreach_k, axis=1)[:, mreach_k]
    if method == "auto":
        method = "delaunay" if X.shape[1] == 2 and n > 1500 else "dense"
    if method == "delaunay":
        tri = Delaunay(X)
        s = tri.simplices
        e = np.vstack([s[:, [0, 1]], s[:, [1, 2]], s[:, [0, 2]]])
        e = np.unique(np.sort(e, axis=1), axis=0)
        w = np.linalg.norm(X[e[:, 0]] - X[e[:, 1]], axis=1)
        if core is not None:
            w = np.maximum(w, np.maximum(core[e[:, 0]], core[e[:, 1]]))
        G = coo_matrix((w, (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    else:
        D = distance_matrix(X, X) if core is None else D
        if core is not None:
            D = np.maximum(D, np.maximum(core[:, None], core[None, :]))
        G = coo_matrix(D).tocsr()
    T = minimum_spanning_tree(G).tocoo()
    return np.column_stack([T.row, T.col, T.data])


def _adjacency(n, edges):
    adj = [[] for _ in range(n)]
    for idx, (u, v, _) in enumerate(edges):
        u, v = int(u), int(v)
        adj[u].append((v, idx))
        adj[v].append((u, idx))
    return adj


def _component_size(adj, start, removed):
    seen = {start}
    q = deque([start])
    while q:
        a = q.popleft()
        for b, idx in adj[a]:
            if idx in removed or b in seen:
                continue
            seen.add(b)
            q.append(b)
    return len(seen)


def _labels_from_cuts(n, adj, removed):
    labels = -np.ones(n, dtype=int)
    c = 0
    for s in range(n):
        if labels[s] != -1:
            continue
        labels[s] = c
        q = deque([s])
        while q:
            a = q.popleft()
            for b, idx in adj[a]:
                if idx in removed or labels[b] != -1:
                    continue
                labels[b] = c
                q.append(b)
        c += 1
    return labels


def _inconsistency(edges, adj, depth=3):
    """Zahn ratio: edge weight / mean weight of neighbouring edges within `depth` hops."""
    ratios = np.zeros(len(edges))
    for idx, (u, v, w) in enumerate(edges):
        u, v = int(u), int(v)
        side_w = []
        for root, other in ((u, v), (v, u)):
            seen = {root, other}
            frontier = [root]
            ws = []
            for _ in range(depth):
                nxt = []
                for a in frontier:
                    for b, j in adj[a]:
                        if b in seen:
                            continue
                        seen.add(b)
                        ws.append(edges[j, 2])
                        nxt.append(b)
                frontier = nxt
            side_w.append(ws)
        means = [np.mean(s) for s in side_w if len(s) > 0]
        ratios[idx] = w / max(means) if means else 1.0
    return ratios


class MSTClusterer:
    """MST clustering.

    mode='k'    : remove k-1 largest MST edges whose removal leaves both sides
                  with >= min_size points (other long edges are treated as outlier links).
    mode='zahn' : remove edges whose inconsistency ratio exceeds ratio_thr,
                  largest first, subject to min_size; number of clusters is automatic.
    """

    def __init__(self, n_clusters=2, mode="k", min_size=10, ratio_thr=2.0,
                 depth=3, mst_method="auto", mreach_k=0):
        self.n_clusters, self.mode, self.min_size = n_clusters, mode, min_size
        self.ratio_thr, self.depth, self.mst_method = ratio_thr, depth, mst_method
        self.mreach_k = mreach_k

    def fit_predict(self, X):
        X = np.asarray(X, float)
        n = len(X)
        edges = build_mst(X, self.mst_method, self.mreach_k)
        adj = _adjacency(n, edges)
        self.edges_ = edges
        removed = set()
        w = edges[:, 2]
        if self.mode == "k":
            cand = np.argsort(-w)
            limit = self.n_clusters - 1
        else:
            ratios = _inconsistency(edges, adj, self.depth)
            c = np.where(ratios > self.ratio_thr)[0]
            cand = c[np.argsort(-w[c])]
            limit = n
        for idx in cand:
            if len(removed) >= limit:
                break
            u, v = int(edges[idx, 0]), int(edges[idx, 1])
            trial = removed | {int(idx)}
            if (_component_size(adj, u, trial) >= self.min_size and
                    _component_size(adj, v, trial) >= self.min_size):
                removed = trial
        self.removed_ = sorted(removed)
        self.labels_ = _labels_from_cuts(n, adj, removed)
        return self.labels_
