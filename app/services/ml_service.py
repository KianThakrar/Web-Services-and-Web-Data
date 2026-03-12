"""ML-powered win probability model using logistic regression.

Trains on all historical race results with walk-forward feature construction
(no look-ahead bias — features for each race are computed from prior races only).
The model is trained once and cached in memory for subsequent requests.

Features (all in [0, 1]):
  career_win_rate      — exponentially decayed: recent wins weighted more than old
  circuit_win_rate     — Bayesian-smoothed: shrinks toward career rate when sample is small
  recent_points_rate   — avg points in last 10 races / 25 (more granular than win/no-win)
  constructor_win_rate — constructor win rate over the most recent 3 seasons only
"""

from __future__ import annotations

import threading
from collections import defaultdict
from itertools import groupby

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult

# ── Constants ─────────────────────────────────────────────────────────────────
_SMOOTHING = 4        # Bayesian prior strength: circuit rate shrinks toward career rate
_MAX_POINTS = 25.0    # Maximum F1 points per race (for normalization)
_RECENT_N = 10        # Window size for recent form
_CTOR_SEASONS = 3     # Seasons used for constructor form
_MIN_PRIOR = 5        # Minimum prior races before including a sample in training
_DECAY = 0.92         # Exponential decay factor per season for career rate

# ── Module-level singleton ────────────────────────────────────────────────────
_lock = threading.Lock()
_pipeline: Pipeline | None = None
_meta: dict | None = None


# ── Feature construction ──────────────────────────────────────────────────────

def _decayed_win_rate(wins_by_season: dict[int, int], races_by_season: dict[int, int], current_season: int) -> float:
    """Career win rate with exponential decay — recent seasons count more."""
    total_weight = 0.0
    weighted_wins = 0.0
    for season, races in races_by_season.items():
        age = current_season - season
        w = _DECAY ** age
        weighted_wins += wins_by_season.get(season, 0) * w
        total_weight += races * w
    return weighted_wins / total_weight if total_weight > 0 else 0.0


def _build_dataset(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Build (X, y) training arrays using walk-forward feature construction."""

    # Per-driver running stats
    driver_wins_by_season: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    driver_races_by_season: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    driver_recent_pts: dict[int, list[float]] = defaultdict(list)
    driver_circuit_wins: dict[tuple, int] = defaultdict(int)
    driver_circuit_races: dict[tuple, int] = defaultdict(int)
    ctor_season_wins: dict[tuple, int] = defaultdict(int)
    ctor_season_races: dict[tuple, int] = defaultdict(int)

    X_rows: list[list[float]] = []
    y_rows: list[int] = []

    # Process chronologically, race by race
    for (season, _rnd), race_iter in groupby(rows, key=lambda r: (r["season"], r["round"])):
        race_list = list(race_iter)

        # ── Compute features BEFORE updating stats ────────────────────────
        for r in race_list:
            did = r["driver_id"]
            cid = r["constructor_id"]
            circuit = r["circuit_name"]

            prior_races = sum(driver_races_by_season[did].values())
            if prior_races < _MIN_PRIOR:
                continue  # Not enough history yet

            # 1. Decayed career win rate
            career_rate = _decayed_win_rate(
                driver_wins_by_season[did],
                driver_races_by_season[did],
                season,
            )

            # 2. Bayesian-smoothed circuit win rate
            ck = (did, circuit)
            c_wins = driver_circuit_wins[ck]
            c_races = driver_circuit_races[ck]
            circuit_rate = (c_wins + _SMOOTHING * career_rate) / (c_races + _SMOOTHING)

            # 3. Recent points rate (last N races normalised)
            recent = driver_recent_pts[did][-_RECENT_N:]
            recent_rate = sum(recent) / (len(recent) * _MAX_POINTS) if recent else career_rate

            # 4. Constructor recent form
            ctor_wins = sum(ctor_season_wins[(cid, s)] for s in range(season - _CTOR_SEASONS, season))
            ctor_races = sum(ctor_season_races[(cid, s)] for s in range(season - _CTOR_SEASONS, season))
            ctor_rate = ctor_wins / ctor_races if ctor_races > 0 else 0.0

            X_rows.append([career_rate, circuit_rate, recent_rate, ctor_rate])
            y_rows.append(1 if r["finish_position"] == 1 else 0)

        # ── Update stats WITH this race's results ─────────────────────────
        for r in race_list:
            did = r["driver_id"]
            cid = r["constructor_id"]
            circuit = r["circuit_name"]
            won = r["finish_position"] == 1

            driver_races_by_season[did][season] += 1
            if won:
                driver_wins_by_season[did][season] += 1
            driver_recent_pts[did].append(float(r["points"] or 0))

            driver_circuit_races[(did, circuit)] += 1
            if won:
                driver_circuit_wins[(did, circuit)] += 1

            ctor_season_races[(cid, season)] += 1
            if won:
                ctor_season_wins[(cid, season)] += 1

    return np.array(X_rows, dtype=float), np.array(y_rows, dtype=int)


def _load_rows(db: Session) -> list[dict]:
    """Fetch all race results with race metadata, ordered chronologically."""
    rows = (
        db.query(
            RaceResult.driver_id,
            RaceResult.constructor_id,
            RaceResult.finish_position,
            RaceResult.points,
            Race.season,
            Race.round,
            Race.circuit_name,
        )
        .join(Race, Race.id == RaceResult.race_id)
        .order_by(Race.season, Race.round, RaceResult.driver_id)
        .all()
    )
    return [r._asdict() for r in rows]


class _InsufficientDataError(Exception):
    """Raised when there is not enough data to train the model."""


def _train(db: Session) -> tuple[Pipeline, dict]:
    """Train the logistic regression pipeline and return (model, metadata)."""
    rows = _load_rows(db)
    X, y = _build_dataset(rows)
    if len(X) < 50:
        raise _InsufficientDataError("Not enough race history to train the model.")

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(class_weight="balanced", max_iter=1000, C=0.5)),
    ])
    pipe.fit(X, y)

    y_pred = pipe.predict(X)
    accuracy = float((y_pred == y).mean())
    win_precision = float(y_pred[y_pred == 1].mean()) if y_pred.sum() > 0 else 0.0

    feature_names = ["career_win_rate", "circuit_win_rate", "recent_points_rate", "constructor_win_rate"]
    coefs = pipe.named_steps["lr"].coef_[0].tolist()

    meta = {
        "training_samples": int(len(y)),
        "win_samples": int(y.sum()),
        "training_accuracy": round(accuracy, 4),
        "win_precision": round(win_precision, 4),
        "feature_coefficients": {
            name: round(c, 4) for name, c in zip(feature_names, coefs)
        },
    }
    return pipe, meta


def _get_or_train(db: Session) -> tuple[Pipeline, dict]:
    global _pipeline, _meta
    if _pipeline is not None:
        return _pipeline, _meta
    with _lock:
        if _pipeline is None:
            _pipeline, _meta = _train(db)
    return _pipeline, _meta


# ── Public API ────────────────────────────────────────────────────────────────

def predict_win_probability(db: Session, driver_id: int, circuit_name: str | None = None) -> dict | None:
    """Return ML-predicted win probability for a driver, optionally at a circuit.

    Builds current feature values from the driver's full historical record,
    then runs them through the trained logistic regression model.
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return None

    results = (
        db.query(RaceResult, Race)
        .join(Race, Race.id == RaceResult.race_id)
        .filter(RaceResult.driver_id == driver_id)
        .order_by(Race.season, Race.round)
        .all()
    )

    if not results:
        return {
            "driver_id": driver_id,
            "driver_name": driver.name,
            "win_probability": 0.0,
            "circuit_name": circuit_name,
            "model": "logistic_regression",
            "factors": {},
            "model_info": {},
        }

    total_races = len(results)
    total_wins = sum(1 for rr, _ in results if rr.finish_position == 1)

    # 1. Decayed career win rate
    wins_by_season: dict[int, int] = defaultdict(int)
    races_by_season: dict[int, int] = defaultdict(int)
    latest_season = results[-1][1].season
    for rr, r in results:
        races_by_season[r.season] += 1
        if rr.finish_position == 1:
            wins_by_season[r.season] += 1
    career_rate = _decayed_win_rate(wins_by_season, races_by_season, latest_season)

    # 2. Bayesian-smoothed circuit win rate
    if circuit_name:
        circuit_res = [(rr, r) for rr, r in results if r.circuit_name == circuit_name]
        c_wins = sum(1 for rr, _ in circuit_res if rr.finish_position == 1)
        c_races = len(circuit_res)
        circuit_rate = (c_wins + _SMOOTHING * career_rate) / (c_races + _SMOOTHING)
    else:
        c_wins = None
        c_races = None
        circuit_rate = career_rate

    # 3. Recent points rate
    recent = [float(rr.points or 0) for rr, _ in results[-_RECENT_N:]]
    recent_rate = sum(recent) / (len(recent) * _MAX_POINTS) if recent else career_rate

    # 4. Constructor recent form
    latest_ctor_id = results[-1][0].constructor_id
    ctor_res = (
        db.query(RaceResult)
        .join(Race, Race.id == RaceResult.race_id)
        .filter(
            RaceResult.constructor_id == latest_ctor_id,
            Race.season >= latest_season - _CTOR_SEASONS,
        )
        .all()
    )
    ctor_total = len(ctor_res)
    ctor_wins_n = sum(1 for r in ctor_res if r.finish_position == 1)
    ctor_rate = ctor_wins_n / ctor_total if ctor_total else 0.0

    # Predict — fall back to weighted formula if not enough training data
    model_name = "logistic_regression"
    try:
        pipe, meta = _get_or_train(db)
        X = np.array([[career_rate, circuit_rate, recent_rate, ctor_rate]], dtype=float)
        prob = float(pipe.predict_proba(X)[0][1])
    except _InsufficientDataError:
        prob = round(0.40 * circuit_rate + 0.30 * career_rate + 0.20 * recent_rate + 0.10 * ctor_rate, 4)
        meta = {}
        model_name = "weighted_fallback"

    return {
        "driver_id": driver_id,
        "driver_name": driver.name,
        "circuit_name": circuit_name,
        "win_probability": round(prob, 4),
        "model": model_name,
        "factors": {
            "circuit_win_rate": round(circuit_rate, 4),
            "circuit_appearances": c_races,
            "circuit_wins": c_wins,
            "overall_win_rate": round(career_rate, 4),
            "total_races": total_races,
            "total_wins": total_wins,
            "recent_form_rate": round(recent_rate, 4),
            "constructor_win_rate": round(ctor_rate, 4),
        },
        "model_info": meta,
    }


def predict_race_win_probabilities(
    db: Session,
    race_id: int,
    normalise: bool = False,
) -> list[dict] | None:
    """Return win probabilities for all drivers in a given race.

    Each driver's raw logistic regression probability is an independent binary
    prediction — P(this driver wins) given their historical features.

    When normalise=False (default): raw probabilities are returned. Each is an
    honest per-driver estimate; they will not sum to 1.0.

    When normalise=True: raw scores are divided by their sum so that all values
    sum to 1.0. This is a heuristic rescaling for interpretability (analogous to
    softmax), not a principled joint probability model. The scoring_method field
    in each entry indicates which mode was used.
    """
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        return None

    driver_ids = (
        db.query(RaceResult.driver_id)
        .filter(RaceResult.race_id == race_id)
        .all()
    )
    if not driver_ids:
        return None

    entries = []
    for (did,) in driver_ids:
        pred = predict_win_probability(db, did, race.circuit_name)
        if pred:
            entries.append(pred)

    if not entries:
        return None

    if normalise:
        total = sum(e["win_probability"] for e in entries)
        if total > 0:
            for e in entries:
                e["win_probability"] = round(e["win_probability"] / total, 4)
        else:
            equal = round(1.0 / len(entries), 4)
            for e in entries:
                e["win_probability"] = equal
        scoring = "normalised_relative"
    else:
        scoring = "independent_binary"

    for e in entries:
        e["scoring_method"] = scoring

    entries.sort(key=lambda x: x["win_probability"], reverse=True)
    return entries
