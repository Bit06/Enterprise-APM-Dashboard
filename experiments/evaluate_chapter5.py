"""
Chapter 5 Evaluation: Reproducible Controlled-Workload Anomaly Detection Experiment.
Author / System: Intelligent APM System Prototype
Evaluation Specification:
  - Random seed: 20261125
  - Total observations: 12,000 1-minute intervals (5,000 train, 7,000 test)
  - 7 Multivariate Features:
      1. request_rate (rps)
      2. api_p95_latency (ms)
      3. http_5xx_rate (%)
      4. timeout_rate (%)
      5. cpu_percent (%)
      6. memory_percent (%)
      7. dependency_p95_latency (ms)
  - 6 Non-overlapping 60-minute failure injection scenarios in test period (360 anomalous points)
  - Point-wise evaluation without point adjustment
  - Baseline: Fixed Operational Thresholds vs. Unsupervised Isolation Forest (300 estimators)
"""

import time
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

SEED = 20261125
np.random.seed(SEED)

FEATURE_COLS = [
    "request_rate",
    "api_p95_latency",
    "http_5xx_rate",
    "timeout_rate",
    "cpu_percent",
    "memory_percent",
    "dependency_p95_latency"
]

def generate_controlled_workload():
    n_points = 12000
    t = np.arange(n_points)

    # Base seasonalities: Daily cycle (1440 min) and hourly wave (60 min)
    daily_cycle = np.sin(2 * np.pi * t / 1440)
    hourly_cycle = np.cos(2 * np.pi * t / 60)

    # 1. Request rate (normal: 50-150 rps)
    rps = 100 + 35 * daily_cycle + 10 * hourly_cycle + np.random.normal(0, 5, n_points)
    rps = np.clip(rps, 20, 200)

    # 2. Dependency P95 latency (normal: 80-160 ms)
    dep_p95 = 110 + 15 * daily_cycle + np.random.normal(0, 8, n_points)
    dep_p95 = np.clip(dep_p95, 50, 200)

    # 3. API P95 latency (normal: 120-220 ms, influenced by dependency)
    api_p95 = dep_p95 + 40 + 10 * (rps / 100.0) + np.random.normal(0, 10, n_points)
    api_p95 = np.clip(api_p95, 70, 250)

    # 4. HTTP 5xx rate (normal: 0.1% - 1.5%)
    http_5xx = 0.5 + 0.3 * np.abs(np.random.normal(0, 1, n_points))
    http_5xx = np.clip(http_5xx, 0.0, 2.0)

    # 5. Timeout rate (normal: 0.0% - 0.5%)
    timeout_rate = 0.1 + 0.15 * np.abs(np.random.normal(0, 0.8, n_points))
    timeout_rate = np.clip(timeout_rate, 0.0, 1.0)

    # 6. CPU percent (normal: 25% - 65%)
    cpu = 35 + 15 * (rps / 150.0) + np.random.normal(0, 4, n_points)
    cpu = np.clip(cpu, 10, 70)

    # 7. Memory percent (normal: 45% - 70% slow diurnal swell)
    mem = 55 + 10 * np.sin(2 * np.pi * (t - 300) / 1440) + np.random.normal(0, 2, n_points)
    mem = np.clip(mem, 30, 75)

    df = pd.DataFrame({
        "minute": t,
        "request_rate": rps,
        "api_p95_latency": api_p95,
        "http_5xx_rate": http_5xx,
        "timeout_rate": timeout_rate,
        "cpu_percent": cpu,
        "memory_percent": mem,
        "dependency_p95_latency": dep_p95,
        "label": 0,
        "scenario": "normal"
    })

    # Injected Scenarios (In test set: index 5000 to 12000)
    scenarios = [
        {"name": "Latency injection", "start": 5500, "duration": 60, "primary_feature": "api_p95_latency"},
        {"name": "Elevated HTTP 5xx", "start": 6500, "duration": 60, "primary_feature": "http_5xx_rate"},
        {"name": "Timeouts", "start": 7500, "duration": 60, "primary_feature": "timeout_rate"},
        {"name": "Resource pressure", "start": 8500, "duration": 60, "primary_feature": "cpu_percent"},
        {"name": "Slow external dependency", "start": 9500, "duration": 60, "primary_feature": "dependency_p95_latency"},
        {"name": "Combined dependency failure", "start": 10500, "duration": 60, "primary_feature": "timeout_rate"}
    ]

    for sc in scenarios:
        s = sc["start"]
        e = s + sc["duration"]
        df.loc[s:e-1, "label"] = 1
        df.loc[s:e-1, "scenario"] = sc["name"]

        # Gradual ramp-up injection profiles
        ramp = np.linspace(0.4, 1.0, sc["duration"])
        if sc["name"] == "Latency injection":
            df.loc[s:e-1, "api_p95_latency"] += ramp * 280.0
        elif sc["name"] == "Elevated HTTP 5xx":
            df.loc[s:e-1, "http_5xx_rate"] += ramp * 14.0
        elif sc["name"] == "Timeouts":
            df.loc[s:e-1, "timeout_rate"] += ramp * 8.0
        elif sc["name"] == "Resource pressure":
            df.loc[s:e-1, "cpu_percent"] += ramp * 55.0
            df.loc[s:e-1, "memory_percent"] += ramp * 20.0
        elif sc["name"] == "Slow external dependency":
            df.loc[s:e-1, "dependency_p95_latency"] += ramp * 290.0
            df.loc[s:e-1, "api_p95_latency"] += ramp * 220.0
        elif sc["name"] == "Combined dependency failure":
            df.loc[s:e-1, "dependency_p95_latency"] += ramp * 310.0
            df.loc[s:e-1, "timeout_rate"] += ramp * 9.0
            df.loc[s:e-1, "api_p95_latency"] += ramp * 180.0

    return df, scenarios

def evaluate():
    print("=" * 70)
    print("  CHAPTER 5 CONTROLLED WORKLOAD EXPERIMENT EXECUTION")
    print("=" * 70)

    df, scenarios = generate_controlled_workload()

    # Train / Test chronological split
    train_df = df.iloc[:5000].copy()
    test_df = df.iloc[5000:].copy()

    X_train = train_df[FEATURE_COLS].values
    X_test = test_df[FEATURE_COLS].values
    y_test = test_df["label"].values

    print(f"Total Points: {len(df)} (Train: {len(train_df)}, Test: {len(test_df)})")
    print(f"Test Anomaly Points: {np.sum(y_test)} (Normal: {len(y_test) - np.sum(y_test)})")

    # --- 1. Train Isolation Forest ---
    t0_fit = time.time()
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    iforest = IsolationForest(
        n_estimators=300,
        contamination=0.05,
        random_state=SEED,
        n_jobs=-1
    )
    iforest.fit(X_train_scaled)
    fit_duration = time.time() - t0_fit

    # Score threshold: 99.5th percentile of anomaly severity (lowest 0.5% of score_samples)
    train_scores = iforest.score_samples(X_train_scaled)
    score_threshold = np.percentile(train_scores, 0.5)

    # --- Test Scoring ---
    t0_score = time.time()
    X_test_scaled = scaler.transform(X_test)
    test_scores = iforest.score_samples(X_test_scaled)
    score_duration = time.time() - t0_score

    if_pred = (test_scores <= score_threshold).astype(int)

    # --- 2. Fixed Threshold Baseline ---
    th_pred = (
        (test_df["api_p95_latency"] > 300.0) |
        (test_df["http_5xx_rate"] > 5.0) |
        (test_df["timeout_rate"] > 3.0) |
        (test_df["cpu_percent"] > 88.0) |
        (test_df["dependency_p95_latency"] > 280.0)
    ).astype(int).values

    def compute_metrics(y_true, y_pred):
        tp = int(np.sum((y_true == 1) & (y_pred == 1)))
        fp = int(np.sum((y_true == 0) & (y_pred == 1)))
        tn = int(np.sum((y_true == 0) & (y_pred == 0)))
        fn = int(np.sum((y_true == 1) & (y_pred == 0)))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        return {
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": prec, "recall": rec, "f1": f1, "fpr": fpr
        }

    m_if = compute_metrics(y_test, if_pred)
    m_th = compute_metrics(y_test, th_pred)

    # --- Per-Scenario Detection Delay & Explanatory Ranking ---
    scenario_results = []
    if_delays = []
    th_delays = []

    # Medians and IQRs from training set for feature attribution
    train_medians = np.median(X_train, axis=0)
    train_iqrs = np.percentile(X_train, 75, axis=0) - np.percentile(X_train, 25, axis=0)
    train_iqrs = np.where(train_iqrs == 0, 1.0, train_iqrs)

    top1_correct = 0
    top3_correct = 0

    for sc in scenarios:
        s_idx = sc["start"] - 5000  # Offset relative to test set start
        e_idx = s_idx + sc["duration"]

        sc_if_pred = if_pred[s_idx:e_idx]
        sc_th_pred = th_pred[s_idx:e_idx]

        # First detected index relative to scenario start
        if_hit = np.where(sc_if_pred == 1)[0]
        th_hit = np.where(sc_th_pred == 1)[0]

        d_if = int(if_hit[0]) if len(if_hit) > 0 else sc["duration"]
        d_th = int(th_hit[0]) if len(th_hit) > 0 else sc["duration"]

        if_delays.append(d_if)
        th_delays.append(d_th)

        # Feature deviation ranking during the anomaly interval
        anom_points = X_test[s_idx:e_idx]
        standardized_devs = np.mean((anom_points - train_medians) / train_iqrs, axis=0)

        # Rank features descending by positive deviation
        ranked_feature_indices = np.argsort(-standardized_devs)
        ranked_names = [FEATURE_COLS[i] for i in ranked_feature_indices]

        target_feat = sc["primary_feature"]
        rank_pos = ranked_names.index(target_feat) + 1 if target_feat in ranked_names else 99

        if rank_pos == 1:
            top1_correct += 1
        if rank_pos <= 3:
            top3_correct += 1

        scenario_results.append({
            "scenario": sc["name"],
            "if_delay_min": d_if,
            "th_delay_min": d_th,
            "expected_evidence": f"{target_feat} (Rank #{rank_pos})",
            "top_ranked": ranked_names[:3]
        })

    m_if["mttd"] = float(np.mean(if_delays))
    m_th["mttd"] = float(np.mean(th_delays))

    # --- Print Output Tables ---
    print("\n" + "=" * 70)
    print("  TABLE 5.2: CONTROLLED-WORKLOAD DETECTION RESULTS")
    print("=" * 70)
    print(f"{'Metric':<25} {'Isolation Forest':<20} {'Fixed Threshold':<20}")
    print("-" * 70)
    print(f"{'True positives':<25} {m_if['tp']:<20} {m_th['tp']:<20}")
    print(f"{'False positives':<25} {m_if['fp']:<20} {m_th['fp']:<20}")
    print(f"{'True negatives':<25} {m_if['tn']:<20} {m_th['tn']:<20}")
    print(f"{'False negatives':<25} {m_if['fn']:<20} {m_th['fn']:<20}")
    print(f"{'Precision':<25} {m_if['precision']:<20.3f} {m_th['precision']:<20.3f}")
    print(f"{'Recall':<25} {m_if['recall']:<20.3f} {m_th['recall']:<20.3f}")
    print(f"{'F1-score':<25} {m_if['f1']:<20.3f} {m_th['f1']:<20.3f}")
    print(f"{'False-positive rate':<25} {m_if['fpr']:<20.4f} {m_th['fpr']:<20.4f}")
    print(f"{'Mean time to detect':<25} {m_if['mttd']:<20.2f} min {m_th['mttd']:<20.2f} min")
    print("-" * 70)

    print("\n" + "=" * 70)
    print("  TABLE 5.3: PER-SCENARIO DETECTION DELAY AND RANKED EVIDENCE")
    print("=" * 70)
    print(f"{'Scenario':<30} {'IF Delay':<10} {'TH Delay':<10} {'Ranked Evidence'}")
    print("-" * 70)
    for sr in scenario_results:
        print(f"{sr['scenario']:<30} {sr['if_delay_min']:<2} min     {sr['th_delay_min']:<2} min     {sr['expected_evidence']}")
    print("-" * 70)
    print(f"Top-1 Feature Attribution Accuracy: {top1_correct}/{len(scenarios)} ({top1_correct/len(scenarios)*100:.1f}%)")
    print(f"Top-3 Feature Attribution Accuracy: {top3_correct}/{len(scenarios)} ({top3_correct/len(scenarios)*100:.1f}%)")
    print(f"Model Fitting Duration: {fit_duration:.2f}s | Test Scoring Duration: {score_duration*1000/len(X_test):.3f}ms/point")
    print("=" * 70)

    # Save summary artifact
    output = {
        "metadata": {
            "seed": SEED,
            "train_points": len(train_df),
            "test_points": len(test_df),
            "anomaly_points": int(np.sum(y_test)),
            "fit_time_seconds": round(fit_duration, 3)
        },
        "table_5_2_detection": {
            "isolation_forest": m_if,
            "fixed_threshold": m_th
        },
        "table_5_3_scenarios": scenario_results,
        "ranking_accuracy": {
            "top1": top1_correct / len(scenarios),
            "top3": top3_correct / len(scenarios)
        }
    }

    with open("c:/Users/ADMIN/Downloads/Projects/apm_system/apm_system/chapter5_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\n[SUCCESS] Experiment completed. Artifact saved to chapter5_results.json")

if __name__ == "__main__":
    evaluate()
