# AstraOps — Event Response Intelligence System

A working prototype for the **Event-Driven Congestion (Planned & Unplanned)**
problem statement: forecast event-related traffic impact and recommend
manpower, barricading, and diversion plans, using the Astram historical
incident data.

This implements the blueprint's "decision-support command center" direction:
predict impact → recommend a concrete action → let the operator see why →
record outcomes once the incident closes.

## What's real vs. what's a documented design choice

This is grounded in the actual `Astram_event_data_anonymized` CSV (8,173
rows), not just the summary numbers in the blueprint PDF. A few things
came out differently once we looked at the raw data, and the code says so
inline:

- **Clearance time** is only computed for incidents that closed within
  **24 hours** of opening. ~17% of rows with a `closed_datetime` show
  multi-day to multi-week gaps that almost certainly reflect record-keeping
  lag (a ticket closed administratively long after the road reopened), not
  real-world closure duration. Including them would have produced a
  regression target with a mean of 41 hours against a median of 1 hour —
  technically "trainable" but not honest. See the comment in
  `backend/app/data/clean.py`.
- **`vip_movement`** has only 20 rows in the whole dataset and an 80%
  historical closure rate. A gradient-boosted model can't learn a reliable
  pattern from 20 examples, and in testing it predicted ~0.2% closure
  probability for a fresh `vip_movement` event — clearly wrong. This is
  exactly why the recommendation engine (`backend/app/models/recommend.py`)
  applies rule-based overrides for `vip_movement`, `public_event`,
  `protest`, `construction`, and `tree_fall`: causes where the historical
  pattern is strong but the sample size is too thin to trust a learned
  probability alone.
- **`impact_score`** has no ground-truth label in the source data — there's
  no "how bad was this" column — so it's built as a transparent, documented
  composite (closure-rate history, priority, planned/unplanned, location
  hotspot density) rather than presented as something a model "learned."

## Stack

The blueprint suggests FastAPI + LightGBM. Neither could be installed in
the environment this was built in (no outbound network access for pip),
so the same API contract and modeling approach is implemented with
libraries that needed zero extra installs:

| Blueprint suggestion | Used instead | Why |
|---|---|---|
| FastAPI | Flask | Same REST contract, already available |
| LightGBM | scikit-learn `HistGradientBoostingClassifier/Regressor` | Same histogram-based gradient boosting family |
| PostgreSQL/SQLite | In-memory + JSONL feedback log | Enough for a hackathon prototype; swap in SQLite trivially |

If your machine has internet access and you'd rather use FastAPI/LightGBM,
the swap is mechanical — same feature columns, same training loop shape.

## Project layout

```
astraops/
├── backend/
│   ├── data_raw/astram_events.csv          # your source data
│   ├── data_processed/                     # cleaned CSV + feedback log (generated)
│   ├── saved_models/                       # trained model artifacts (generated)
│   ├── app/
│   │   ├── data/
│   │   │   ├── clean.py                    # Step 1: data cleaning
│   │   │   └── features.py                 # Step 2/3: feature engineering + labels
│   │   ├── models/
│   │   │   ├── train.py                    # Step 4: model training
│   │   │   ├── recommend.py                # Step 5: recommendation engine
│   │   │   ├── similar.py                  # similar-incidents lookup
│   │   │   └── inference.py                # scores a brand-new event at request time
│   │   └── api/
│   │       └── server.py                   # Step 6 (API): Flask endpoints
│   ├── setup.sh                            # one-shot: clean + train
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/Dashboard.jsx             # home dashboard
    │   ├── pages/MapView.jsx               # live map
    │   ├── pages/EventDetail.jsx           # event detail + similar incidents
    │   ├── pages/Simulator.jsx             # what-if planning simulator
    │   ├── pages/LearningLog.jsx           # post-event learning screen
    │   └── components/                     # RiskBadge, ActionCard, StatCard
    └── package.json
```

## Running it

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
bash setup.sh              # cleans data, trains both models, saves artifacts
python3 app/api/server.py  # starts the API on http://localhost:8000
```

Re-run `setup.sh` any time `data_raw/astram_events.csv` is replaced with a
fresher export — the trained models and lookup tables are derived from
whatever's in that file.

Quick check it's alive:
```bash
curl http://localhost:8000/api/health
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                # starts on http://localhost:5173
```

The Vite dev server proxies `/api`, `/predict`, `/simulate`,
`/similar-events`, and `/feedback` to `localhost:8000`, so just open
`http://localhost:5173` once both are running.

## API reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness check |
| GET | `/api/incidents?status=&event_cause=&corridor=&limit=` | filtered incident list (map + dashboard) |
| GET | `/api/hotspots` | corridor / zone / station / cause aggregates |
| POST | `/predict/event` | score a live or proposed event → impact, closure risk, ETA, recommendation, similar incidents |
| POST | `/simulate` | same contract as `/predict/event`, used by the planning simulator |
| GET | `/similar-events?lat=&lon=&event_cause=&corridor=&top_k=` | nearest historical incidents |
| POST | `/feedback` | record predicted-vs-actual outcome for a resolved incident |
| GET | `/api/learning-log` | list recorded feedback entries |

`POST /predict/event` body:
```json
{
  "event_cause": "tree_fall",
  "corridor": "Mysore Road",
  "police_station": "Yelahanka",
  "zone": "North Zone 1",
  "priority": "High",
  "event_type": "unplanned",
  "latitude": 13.04,
  "longitude": 77.518
}
```
Only `event_cause`, `latitude`, `longitude` are required — everything else
defaults sensibly if omitted.

`POST /feedback` body:
```json
{
  "incident_id": "FKID999999",
  "predicted_closure_probability": 0.45,
  "actual_required_closure": true,
  "predicted_eta_hours": 3.5,
  "actual_clearance_hours": 4.1
}
```

## Model performance (on this dataset, your numbers will vary slightly run to run)

- **Closure classifier**: ROC-AUC 0.78, PR-AUC 0.38, recall 52% at default
  threshold — reasonable given only 7.4% of rows in the modeling set require
  closure. Threshold and class weights are tunable in `train.py`.
- **Clearance regressor** (on the 24h-capped, sane-duration subset, ~2,460
  rows): MAE 1.25 hours, median absolute error 0.49 hours, against a median
  true clearance time of 0.79 hours.

Full metrics are written to `backend/saved_models/metrics.json` every time
you run `setup.sh`.

## What to demo

1. Open the dashboard, point at the active incident count and the
   closure-rate-by-cause chart.
2. Click into an incident, show predicted impact + recommended response +
   "why" rationale + similar past incidents.
3. Go to the Planning Simulator, configure a hypothetical `public_event` on
   a busy corridor, run it, show the recommendation flip to heavy
   barricading / full closure diversion.
4. Mention the `vip_movement` override explicitly — it's a genuinely
   interesting, defensible design decision born from looking at the real
   data, not a generic ML pitch.
5. Show the post-event learning log and the `/feedback` endpoint as the
   loop that's supposed to make the system improve over time.

## Known limitations (be upfront about these if asked)

- `zone` is missing on ~58% of rows; it's bucketed to `"Unknown"` rather
  than imputed, so zone-level aggregates undercount real volume.
- The closure classifier's precision (22%) is low at the default 0.5
  threshold — for a real deployment you'd tune the threshold against an
  actual cost-of-false-negative vs. cost-of-false-positive tradeoff, not
  ship the default.
- `impact_score` is a designed composite, not a learned or validated
  ground truth — say so if asked, don't oversell it as something the model
  discovered on its own.
