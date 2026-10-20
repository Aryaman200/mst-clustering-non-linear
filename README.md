# MST-Based Clustering for Non-Linearly Separable Patterns

Mini project: Euclidean-MST clustering vs K-Means / GMM / Ward / single linkage / DBSCAN,
with an interactive dashboard and the full report.

## Quick start (Windows)
Double-click **`start.bat`**. First run installs the dependencies (a few minutes, only if
numpy/scipy/scikit-learn are missing); the dashboard then opens at http://localhost:8765/.

Manual start (any OS): `pip install -r requirements.txt` then `python app/server.py`.

## Layout
| Path | Purpose |
|---|---|
| `start.bat` | one-click launcher for the dashboard |
| `app/` | dashboard: `server.py` (HTTP API), `engine.py` (datasets, methods, metrics), `static/index.html` (UI) |
| `research/mst_clustering.py` | the MST clustering library (`MSTClusterer`) |
| `research/experiments.py` | reproduces every figure and table in the report |
| `run_experiments.bat` | re-runs the experiments |
| `report/` | final report (PDF + DOCX) |

## Dashboard
* **Explorer** – pick a dataset (or upload a CSV), tune noise, k, minimum cluster size, Zahn ratio,
  mutual-reachability k and DBSCAN eps; compare 8 methods side by side with ARI, NMI, silhouette,
  hull overlap and run time. Toggle the MST and the cut edges. Export labels as CSV.
* **Noise sweep** and **Scalability** – the robustness and run-time experiments, run live.
* **Report results** – the tables and figures from the report.

CSV upload: numeric columns only (header optional); tick "last column is a label" to get ARI/NMI.

## Use the library
```python
from research.mst_clustering import MSTClusterer
labels = MSTClusterer(n_clusters=2, mode="k", min_size=15).fit_predict(X)          # k-cut
labels = MSTClusterer(mode="zahn", ratio_thr=3.0, min_size=15).fit_predict(X)      # automatic k
```
