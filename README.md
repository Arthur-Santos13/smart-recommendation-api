# smart-recommendation-api

A recommendation system API built with **FastAPI** and **scikit-learn**, combining content-based filtering, collaborative filtering, and a configurable hybrid strategy. Every recommendation carries a human-readable explanation and can be filtered by category.

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Getting Started](#getting-started)
   - [Running with Docker](#running-with-docker)
6. [Environment Variables](#environment-variables)
7. [CORS Configuration](#cors-configuration)
8. [Recommendation Algorithms](#recommendation-algorithms)
   - [Content-Based Filtering — How TF-IDF Works](#content-based-filtering--how-tf-idf-works)
   - [Collaborative Filtering — KNN](#collaborative-filtering--knn)
   - [Hybrid System — Weighted Blending](#hybrid-system--weighted-blending)
   - [Category Filter](#category-filter)
   - [Explainability](#explainability)
9. [Model Persistence](#model-persistence)
10. [Background Jobs](#background-jobs)
11. [Metrics](#metrics)
12. [API Reference](#api-reference)
13. [Seed Data](#seed-data)
14. [Roadmap](#roadmap)

---

## Overview

`smart-recommendation-api` suggests items (articles, courses, products) to users based on their interaction history. The system supports three recommendation strategies:

| Strategy | Endpoint | Description |
|---|---|---|
| Content-based | `GET /recommendations/{user_id}` | Items similar to what the user has interacted with |
| Collaborative | `GET /recommendations/collaborative/{user_id}` | Items popular with users who have similar taste |
| Hybrid | `GET /recommendations/hybrid/{user_id}` | Weighted blend of both strategies |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.136 + Uvicorn |
| ORM / Database | SQLAlchemy 2.0 + PostgreSQL + Alembic |
| ML | scikit-learn 1.8, NumPy, SciPy, joblib |
| Config | pydantic-settings + python-dotenv |
| Scheduling | APScheduler 3.11 |
| Containerisation | Docker + Docker Compose |

---

## Architecture

```
Client
  │
  ▼
FastAPI  (/api/v1/...)
  │
  ├── Endpoints  (api/v1/endpoints/)
  │       └── validates input, calls service, returns schema
  │
  ├── Services  (services/)
  │       └── orchestrates repository + ML logic
  │
  ├── Repositories  (repositories/)
  │       └── all DB queries via SQLAlchemy
  │
  └── ML Layer  (ml/)
          ├── vectorizer.py       TF-IDF corpus builder
          ├── similarity.py       item-item cosine similarity matrix
          ├── interaction_matrix.py  sparse user-item matrix
          ├── collaborative_filter.py  KNN model
          ├── hybrid_merger.py    weighted score blending
          ├── trainer.py          training pipeline
          ├── model_store.py      joblib save / load
          └── model_registry.py   in-memory singleton registry
```

**Request lifecycle (content-based example):**

1. `GET /api/v1/recommendations/{user_id}` → `recommendations.py` endpoint
2. Endpoint calls `ContentBasedService(db).recommend(user_id, top_n, category)`
3. Service checks `ModelRegistry` for a cached `SimilarityMatrix`; builds one from DB if absent
4. Service loads the user's events, computes seed weights, scores candidates
5. Returns `list[RecommendationResult]` → serialised to `RecommendationResponse`

---

## Project Structure

```
app/
├── api/v1/endpoints/     REST endpoints (users, items, events, recommendations, metrics, admin)
├── core/                 config, database engine, APScheduler
├── jobs/                 retrain_job.py — periodic retraining function
├── ml/                   all ML primitives and pipelines
├── models/               SQLAlchemy ORM models
├── repositories/         DB access layer
├── schemas/              Pydantic request / response models
└── services/             business logic + ML orchestration

alembic/versions/         database migrations
scripts/
├── seed_data.py          item + user definitions
├── seed.py               deterministic event seeder (python -m scripts.seed)
└── train.py              model training entrypoint (python -m scripts.train)
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL running locally (or via Docker)

### Installation

```bash
git clone https://github.com/Arthur-Santos13/smart-recommendation-api.git
cd smart-recommendation-api

python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
APP_NAME=smart-recommendation-api
APP_ENV=development
DEBUG=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smart_recommendation
SECRET_KEY=change-me-in-production
MODEL_DIR=models
RETRAIN_INTERVAL_HOURS=6
```

### Database setup

```bash
alembic upgrade head
```

### Seed data

```bash
python -m scripts.seed
```

Inserts 12 users across 4 personas and 24 items across 6 categories, then generates deterministic interaction events.

### Train models

```bash
python -m scripts.train
```

Outputs `models/content_model.joblib` and `models/collaborative_model.joblib`.

### Run the API

```bash
uvicorn app.main:app --reload
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Running with Docker

#### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

#### Steps

**1. Copy the environment file:**

```bash
cp .env.example .env
```

> `DATABASE_URL` is overridden in `docker-compose.yml` at runtime to point at the internal `db` service hostname. The value in `.env` is only used for local (non-Docker) runs.

**2. Build and start both services:**

```bash
docker compose up --build
```

**3. On the first run, initialise the database, seed data and train models:**

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m scripts.seed
docker compose exec api python -m scripts.train
```

The API will be available at [http://localhost:8000](http://localhost:8000).  
PostgreSQL is mapped to host port **5435** (avoids conflicts with existing local PostgreSQL instances on 5432–5434 and 5436).

#### Useful commands

| Command | Description |
|---|---|
| `docker compose up -d` | Start services in the background |
| `docker compose down` | Stop and remove containers |
| `docker compose down -v` | Stop containers and **delete volumes** ⚠ destroys all data |
| `docker compose logs -f api` | Stream API logs |
| `docker compose exec api python -m scripts.train` | Retrain models inside the container |

---

## Environment Variables

All settings are loaded from `.env` via `pydantic-settings`. Copy `.env.example` and adjust the values for your environment.

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `smart-recommendation-api` | Application name shown in OpenAPI docs and logs |
| `APP_ENV` | `development` | Runtime environment — `development` or `production` |
| `DEBUG` | `true` | FastAPI debug mode — set to `false` in production |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/smart_recommendation` | PostgreSQL connection string. **Overridden automatically by Docker Compose** to use the `db` service hostname |
| `SECRET_KEY` | `change-me-in-production` | Secret for cryptographic operations — **must be changed before deploying** |
| `MODEL_DIR` | `models` | Directory for trained joblib model artifacts |
| `RETRAIN_INTERVAL_HOURS` | `6` | Hours between automatic background retraining runs. Set to `0` to disable |
| `ALLOWED_ORIGINS` | `http://localhost:4200,http://localhost:3000` | Comma-separated list of origins allowed by CORS middleware |

---

## CORS Configuration

The API ships with `CORSMiddleware` configured via the `ALLOWED_ORIGINS` environment variable. This is the integration point for the Angular frontend ([`smart-recommendation-api-frontend`](https://github.com/Arthur-Santos13/smart-recommendation-frontend)).

**Local development — Angular default port (`ng serve`):**

```env
ALLOWED_ORIGINS=http://localhost:4200
```

**Multiple origins (comma-separated, no spaces around commas):**

```env
ALLOWED_ORIGINS=http://localhost:4200,https://myfrontend.com
```

**Production:**

```env
ALLOWED_ORIGINS=https://myfrontend.com
```

The middleware is configured with `allow_credentials=True`, `allow_methods=["*"]`, and `allow_headers=["*"]`. The origin list is the only enforced boundary.

---

## Recommendation Algorithms

### Content-Based Filtering — How TF-IDF Works

Content-based filtering recommends items that are **textually similar** to the items a user has already interacted with.

#### Step 1 — Build the item corpus

Each item is converted to a single text document by concatenating its `title`, `description`, and `tags`. Tags are repeated **3 times** to boost their term-frequency score without requiring custom tokenisation:

```
corpus[i] = "{title} {description} {tags} {tags} {tags}"
```

#### Step 2 — Fit the TF-IDF matrix

[`TfidfVectorizer`](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html) is fitted on the corpus with these settings:

| Parameter | Value | Reason |
|---|---|---|
| `stop_words` | `"english"` | Removes common words (the, is, of…) that carry no signal |
| `ngram_range` | `(1, 2)` | Captures single words and two-word phrases ("machine learning") |
| `max_features` | `5 000` | Caps vocabulary size for memory efficiency |
| `sublinear_tf` | `True` | Applies `1 + log(tf)` to reduce the dominance of very frequent terms |

The result is a sparse matrix of shape `(n_items × n_features)` where each row is the TF-IDF vector of one item.

**TF-IDF formula:**

$$\text{tfidf}(t, d) = \text{tf}(t, d) \times \text{idf}(t)$$

$$\text{idf}(t) = \log\frac{1 + n}{1 + \text{df}(t)} + 1$$

Where $n$ is the total number of documents and $\text{df}(t)$ is the number of documents containing term $t$.

#### Step 3 — Compute cosine similarity

The item-item similarity matrix is computed as:

$$\text{similarity}(i, j) = \frac{\vec{v}_i \cdot \vec{v}_j}{\|\vec{v}_i\| \|\vec{v}_j\|}$$

This produces a dense `(n_items × n_items)` matrix where each cell holds a score in `[0, 1]`.

#### Step 4 — Score candidates

For a given user, the algorithm:

1. Aggregates **seed weights** per interacted item: `seed_weight(item) = Σ event.weight`
   - Event weights: `view=1`, `click=2`, `complete=3`, `skip=0`, `rate=2`
2. For every candidate item not yet seen by the user, computes:

$$\text{candidate\_score}(c) = \sum_{s \in \text{seeds}} \text{similarity}(s, c) \times \text{seed\_weight}(s)$$

3. Sorts candidates by score descending and returns the top N.

---

### Collaborative Filtering — KNN

Collaborative filtering recommends items that **users with similar interaction patterns** have engaged with.

#### Step 1 — Build the interaction matrix

A sparse `(n_users × n_items)` matrix is built where each cell holds the **maximum** event weight for that `(user, item)` pair. Max-aggregation prevents repeated event types from inflating a single pair's influence.

#### Step 2 — Find similar users

`NearestNeighbors(metric="cosine", algorithm="brute")` is fitted on the interaction matrix. For the target user, the K nearest neighbours are found (default `k=5`).

Similarity from cosine distance: $\text{similarity} = 1 - \text{cosine\_distance}$

#### Step 3 — Score unseen items

For each neighbour, the algorithm aggregates their interaction weights, scaled by the neighbour's similarity to the target user:

$$\text{item\_score}(i) = \sum_{\text{neighbour}} \text{similarity}(\text{user}, \text{neighbour}) \times \text{weight}(\text{neighbour}, i)$$

Items the target user has already interacted with are excluded.

---

### Hybrid System — Weighted Blending

The hybrid endpoint blends both strategies using configurable weights (default: **70% content-based / 30% collaborative**).

#### Step 1 — Normalise each source independently

Scores from each pipeline are min-max normalised to `[0, 1]` before merging. This prevents one pipeline's score magnitude from dominating the other:

$$\text{score\_norm}(i) = \frac{\text{score}(i) - \text{score\_min}}{\text{score\_max} - \text{score\_min}}$$

#### Step 2 — Compute the final score

$$\text{final\_score}(i) = \alpha \times \text{score\_cb}(i) + (1 - \alpha) \times \text{score\_cf}(i)$$

Items present in only one source receive a `0.0` contribution from the missing source, but can still appear if their single-source score is high enough.

#### Cold-start handling

| Situation | Behaviour |
|---|---|
| No interaction history | Falls back to pure content-based; reason tagged `(content)` |
| Too few users for KNN | Falls back to pure content-based; reason tagged `(content)` |
| No content signal | Falls back to pure collaborative; reason tagged `(collaborative)` |

---

### Category Filter

All three endpoints accept an optional `?category=` query parameter. The filter is applied **after scoring**, not before, for two reasons:

1. **Preserves score integrity** — TF-IDF and cosine similarity are computed over the full catalogue. Restricting the matrix to a subset would change the IDF values and produce different (less meaningful) scores.
2. **Maintains seed diversity** — a user's interaction history may include items from multiple categories; all of them contribute to scoring even when the result set is filtered.

Available categories: `technology`, `science`, `business`, `health`, `education`, `general`.

---

### Explainability

Every `RecommendationItem` in the response includes a `reason` string that tells the user **why** the item was recommended.

#### Content-based reason

The algorithm tracks which seed item contributed the **most** to each candidate's score:

```
best_seed = argmax(similarity(seed, candidate) × seed_weight(seed))
reason = "Similar to '{best_seed.title}' that you interacted with"
```

Example:
> *"Similar to 'Introduction to Machine Learning' that you interacted with"*

#### Collaborative reason

```
reason = "Users similar to you also interacted with this item"
```

#### Hybrid reason

The source with the higher weight provides the base reason; a source tag is appended:

| Item present in | Reason source | Tag |
|---|---|---|
| Both sources | Higher-weight source | `(hybrid)` |
| Content-based only | Content-based | `(content)` |
| Collaborative only | Collaborative | `(collaborative)` |

Example:
> *"Similar to 'FastAPI in Practice' that you interacted with (hybrid)"*

---

## Model Persistence

Trained model artifacts are serialised to disk with **joblib** (compress level 3) so the TF-IDF matrix and KNN model do not have to be rebuilt on every request.

```
models/
├── content_model.joblib        SimilarityMatrix + metadata
└── collaborative_model.joblib  InteractionMatrix + KNNCollaborativeFilter + metadata
```

At startup, FastAPI's `lifespan` hook calls `load_into_registry()` which populates the in-memory `ModelRegistry` singleton. If model files are absent (first run before training), services fall back to building the models from the database on demand.

---

## Background Jobs

APScheduler runs inside the application process on a configurable interval:

```
RETRAIN_INTERVAL_HOURS=6   # 0 = disable automatic retraining
```

On each run, `retrain_models()`:
1. Opens a fresh DB session
2. Trains both models via `ModelTrainer`
3. Persists the new artifacts to `MODEL_DIR`
4. Updates `ModelRegistry` atomically (both models or neither)
5. Closes the session

**Manual trigger** (useful after bulk imports):

```bash
curl -X POST http://localhost:8000/api/v1/admin/retrain
```

---

## Metrics

`GET /api/v1/metrics?top_n=10&k=10` returns three offline quality metrics:

### Usage rate

| Field | Description |
|---|---|
| `usage_rate` | Fraction of active users with ≥ 1 interaction |
| `avg_events_per_active_user` | Average event count among engaged users |
| `events_by_type` | Breakdown by `view`, `click`, `complete`, `skip`, `rate` |

### Precision@k (leave-one-out)

For each user with ≥ 2 distinct interacted items:
- Hold out the most recently interacted item
- Recompute content-based scores using remaining events as seeds
- Check if the held-out item appears in the top-k results

$$\text{precision}@k = \frac{\text{hits}}{\text{evaluated\_users}}$$

### Top recommended items

Items that appear most frequently across all users' content-based recommendation lists, with their `title`, `category`, and appearance count.

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/api/v1/health` | Detailed health |
| `GET` | `/api/v1/users/` | List users |
| `POST` | `/api/v1/users/` | Create user |
| `GET` | `/api/v1/users/{id}` | Get user |
| `PUT` | `/api/v1/users/{id}` | Update user |
| `DELETE` | `/api/v1/users/{id}` | Soft-delete user |
| `GET` | `/api/v1/items/` | List items |
| `POST` | `/api/v1/items/` | Create item |
| `GET` | `/api/v1/items/{id}` | Get item |
| `PUT` | `/api/v1/items/{id}` | Update item |
| `DELETE` | `/api/v1/items/{id}` | Soft-delete item |
| `POST` | `/api/v1/events/` | Record user event |
| `GET` | `/api/v1/events/user/{user_id}` | List events for a user |
| `GET` | `/api/v1/recommendations/{user_id}` | Content-based recommendations |
| `GET` | `/api/v1/recommendations/collaborative/{user_id}` | Collaborative recommendations |
| `GET` | `/api/v1/recommendations/hybrid/{user_id}` | Hybrid recommendations |
| `GET` | `/api/v1/metrics` | Offline recommendation metrics |
| `POST` | `/api/v1/admin/retrain` | Trigger immediate model retraining |

Full interactive documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Seed Data

The seed script (`python -m scripts.seed`) generates deterministic, reproducible data for development and testing.

**Users — 12 total across 4 personas:**

| Persona | Count | High-affinity categories |
|---|---|---|
| `tech_enthusiast` | 3 | technology, science |
| `business_analyst` | 3 | business, technology |
| `health_seeker` | 3 | health, education |
| `generalist` | 3 | all categories |

**Items — 24 total:**

| Category | Count |
|---|---|
| technology | 6 |
| science | 4 |
| business | 4 |
| health | 4 |
| education | 3 |
| general | 3 |

**Events** are generated probabilistically per persona × category pair (e.g. `tech_enthusiast × technology` has `p_view=0.95`, `p_click=0.80`, `p_complete=0.70`). The seed is fixed at `42` for reproducibility.

---

## Roadmap

| # | Phase | Branch | Status |
|---|-------|--------|--------|
| 1 | Initial Setup — FastAPI skeleton, project structure | `feature/initial-setup` | ✅ |
| 2 | Database Setup — SQLAlchemy models, Alembic migrations | `feature/database-setup` | ✅ |
| 3 | CRUD — users, items, user events endpoints | `feature/crud` | ✅ |
| 4 | Seed Data — deterministic seeder and sample fixtures | `feature/seed-data` | ✅ |
| 5 | Content-Based Recommender — TF-IDF + cosine similarity | `feature/content-based-recommender` | ✅ |
| 6 | Collaborative Filtering — KNN on interaction matrix | `feature/collaborative-filtering` | ✅ |
| 7 | Hybrid Recommender — weighted blend of both strategies | `feature/hybrid-recommender` | ✅ |
| 8 | Model Persistence — joblib artifacts + startup registry | `feature/model-persistence` | ✅ |
| 9 | Recommendation Metrics — usage rate, precision@k, top items | `feature/recommendation-metrics` | ✅ |
| 10 | Background Jobs — APScheduler periodic retraining | `feature/background-jobs` | ✅ |
| 11 | Architecture Documentation — algorithms and explainability | `docs/architecture-and-recommendation-system` | ✅ |
| 12 | Docker — multi-stage build, Docker Compose, CORS middleware | `feature/docker` | ✅ |
| 13 | Final Documentation — Docker usage, env vars, CORS guide, roadmap | `docs/final-documentation` | ✅ |
