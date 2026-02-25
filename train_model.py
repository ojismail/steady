"""
FrailTrack Phase 1: Train Logistic Regression on UCI HAPT dataset.
Exports model.json (weights, bias, scaler params) and demo_data.json (subject 24 raw data).
"""

import os
import re
import json
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# --- Config ---
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'uci_hapt', 'RawData')
OUTPUT_DIR = os.path.dirname(__file__)
WINDOW_SIZE = 128   # 2.56s at 50Hz
STRIDE = 64         # 50% overlap
POSITIVE_ACTIVITY = 8  # sit-to-stand
DEMO_SUBJECT = 24
DEMO_SAMPLES = 1500  # 30 seconds at 50Hz

CHANNELS = ['ax', 'ay', 'az', 'gx', 'gy', 'gz', 'accel_mag', 'gyro_mag']
STATS = ['mean', 'std', 'min', 'max', 'range', 'energy']
FEATURE_NAMES = [f'{ch}_{st}' for ch in CHANNELS for st in STATS]


def load_labels(data_dir):
    """Load labels.txt: exp_id, user_id, activity_id, start_sample, end_sample."""
    labels_path = os.path.join(data_dir, 'labels.txt')
    labels = []
    with open(labels_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 5:
                labels.append(tuple(int(x) for x in parts))
    return labels


def find_experiment_files(data_dir):
    """Find all acc/gyro file pairs and extract (exp_id, user_id)."""
    acc_pattern = re.compile(r'acc_exp(\d+)_user(\d+)\.txt')
    pairs = {}
    for fname in os.listdir(data_dir):
        m = acc_pattern.match(fname)
        if m:
            exp_id = int(m.group(1))
            user_id = int(m.group(2))
            gyro_fname = f'gyro_exp{m.group(1)}_user{m.group(2)}.txt'
            if os.path.exists(os.path.join(data_dir, gyro_fname)):
                pairs[(exp_id, user_id)] = (fname, gyro_fname)
    return pairs


def load_sensor_file(filepath):
    """Load a 3-column sensor file (space-separated)."""
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            vals = line.strip().split()
            if len(vals) == 3:
                data.append([float(v) for v in vals])
    return np.array(data)


def compute_features(window):
    """
    Compute 48 features from a (128, 8) window.
    Channels: ax, ay, az, gx, gy, gz, accel_mag, gyro_mag
    Stats: mean, std, min, max, range, energy
    """
    features = []
    for ch_idx in range(8):
        col = window[:, ch_idx]
        features.append(np.mean(col))
        features.append(np.std(col))
        features.append(np.min(col))
        features.append(np.max(col))
        features.append(np.max(col) - np.min(col))
        features.append(np.mean(col ** 2))
    return features


def create_windows(data_8ch, labels_for_exp, n_samples):
    """
    Create windows from 8-channel data with binary labels.
    Returns (windows_features, window_labels).
    """
    # Build per-sample label array
    sample_labels = np.zeros(n_samples, dtype=int)
    for _, _, act_id, start, end in labels_for_exp:
        # labels are 1-indexed
        s = max(0, start - 1)
        e = min(n_samples, end)
        sample_labels[s:e] = act_id

    windows_X = []
    windows_y = []

    for start in range(0, n_samples - WINDOW_SIZE + 1, STRIDE):
        end = start + WINDOW_SIZE
        window_data = data_8ch[start:end]
        window_labels = sample_labels[start:end]

        # Majority vote for binary label
        positive_count = np.sum(window_labels == POSITIVE_ACTIVITY)
        label = 1 if positive_count > WINDOW_SIZE / 2 else 0

        features = compute_features(window_data)
        windows_X.append(features)
        windows_y.append(label)

    return windows_X, windows_y


def main():
    print("=" * 60)
    print("FrailTrack Phase 1: Model Training")
    print("=" * 60)

    # Load labels
    labels = load_labels(DATA_DIR)
    print(f"\nLoaded {len(labels)} label segments")

    # Find experiment files
    pairs = find_experiment_files(DATA_DIR)
    print(f"Found {len(pairs)} experiment-user pairs")

    # Process all experiments
    all_X = []
    all_y = []
    all_subjects = []
    demo_data_raw = None
    demo_ground_truth = []

    for (exp_id, user_id), (acc_file, gyro_file) in sorted(pairs.items()):
        acc = load_sensor_file(os.path.join(DATA_DIR, acc_file))
        gyro = load_sensor_file(os.path.join(DATA_DIR, gyro_file))

        n_samples = min(len(acc), len(gyro))
        acc = acc[:n_samples]
        gyro = gyro[:n_samples]

        # Build 8-channel data: ax, ay, az, gx, gy, gz, accel_mag, gyro_mag
        accel_mag = np.sqrt(acc[:, 0]**2 + acc[:, 1]**2 + acc[:, 2]**2).reshape(-1, 1)
        gyro_mag = np.sqrt(gyro[:, 0]**2 + gyro[:, 1]**2 + gyro[:, 2]**2).reshape(-1, 1)
        data_8ch = np.hstack([acc, gyro, accel_mag, gyro_mag])

        # Get labels for this experiment
        exp_labels = [(e, u, a, s, en) for e, u, a, s, en in labels
                      if e == exp_id and u == user_id]

        # Create windows
        win_X, win_y = create_windows(data_8ch, exp_labels, n_samples)
        all_X.extend(win_X)
        all_y.extend(win_y)
        all_subjects.extend([user_id] * len(win_X))

        # Collect demo data for subject 24 (use first experiment with sit-to-stand)
        if user_id == DEMO_SUBJECT and demo_data_raw is None:
            sit_to_stand_labels = [(e, u, a, s, en) for e, u, a, s, en in exp_labels
                                   if a == POSITIVE_ACTIVITY]
            if sit_to_stand_labels:
                # Find center of sit-to-stand events
                all_starts = [s - 1 for _, _, _, s, _ in sit_to_stand_labels]  # 0-indexed
                all_ends = [en for _, _, _, _, en in sit_to_stand_labels]
                center = (min(all_starts) + max(all_ends)) // 2

                # Extract 1500 samples centered on events
                half = DEMO_SAMPLES // 2
                demo_start = max(0, center - half)
                demo_end = demo_start + DEMO_SAMPLES
                if demo_end > n_samples:
                    demo_end = n_samples
                    demo_start = max(0, demo_end - DEMO_SAMPLES)

                # Raw 6-channel data (ax, ay, az, gx, gy, gz)
                raw_6ch = np.hstack([acc[demo_start:demo_end], gyro[demo_start:demo_end]])
                demo_data_raw = raw_6ch.tolist()

                # Ground truth events relative to demo window
                for _, _, act, s, en in sit_to_stand_labels:
                    gt_start = (s - 1) - demo_start
                    gt_end = en - demo_start
                    if gt_start >= 0 and gt_end <= DEMO_SAMPLES:
                        demo_ground_truth.append({
                            'start_sample': gt_start,
                            'end_sample': gt_end
                        })

                print(f"\nDemo data: exp {exp_id}, user {user_id}")
                print(f"  Extracted {len(demo_data_raw)} samples from index {demo_start} to {demo_end}")
                print(f"  Ground truth events: {len(demo_ground_truth)}")
                for gt in demo_ground_truth:
                    print(f"    samples {gt['start_sample']} - {gt['end_sample']}")

    X = np.array(all_X)
    y = np.array(all_y)
    subjects = np.array(all_subjects)

    print(f"\n--- Dataset Summary ---")
    print(f"Total windows: {len(y)}")
    print(f"Positive (sit-to-stand): {np.sum(y == 1)}")
    print(f"Negative (other): {np.sum(y == 0)}")
    print(f"Positive ratio: {np.mean(y):.4f}")
    print(f"Unique subjects: {len(np.unique(subjects))}")

    # Print feature names
    print(f"\nFeature names ({len(FEATURE_NAMES)} features):")
    for i, name in enumerate(FEATURE_NAMES):
        print(f"  [{i:2d}] {name}")

    # Train LR
    print(f"\n--- Training Logistic Regression ---")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    lr.fit(X_scaled, y)

    train_acc = lr.score(X_scaled, y)
    train_preds = lr.predict(X_scaled)
    tp = np.sum((train_preds == 1) & (y == 1))
    fp = np.sum((train_preds == 1) & (y == 0))
    fn = np.sum((train_preds == 0) & (y == 1))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"Training accuracy: {train_acc:.4f}")
    print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
    print(f"Weights range: [{lr.coef_[0].min():.4f}, {lr.coef_[0].max():.4f}]")
    print(f"Bias: {lr.intercept_[0]:.4f}")

    # Export model.json
    model = {
        'weights': lr.coef_[0].tolist(),
        'bias': float(lr.intercept_[0]),
        'means': scaler.mean_.tolist(),
        'stds': scaler.scale_.tolist()
    }

    model_path = os.path.join(OUTPUT_DIR, 'model.json')
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    print(f"\nSaved model.json ({len(model['weights'])} weights)")

    # Export demo_data.json
    if demo_data_raw is not None:
        demo = {
            'samples': demo_data_raw,
            'sample_rate': 50,
            'ground_truth_events': demo_ground_truth,
            'subject_id': DEMO_SUBJECT
        }
        demo_path = os.path.join(OUTPUT_DIR, 'demo_data.json')
        with open(demo_path, 'w') as f:
            json.dump(demo, f)
        print(f"Saved demo_data.json ({len(demo_data_raw)} samples, {len(demo_ground_truth)} events)")
    else:
        print("WARNING: No demo data found for subject 24!")

    # Quick prediction test on demo data
    print(f"\n--- Quick Prediction Test on Demo Data ---")
    if demo_data_raw is not None:
        demo_arr = np.array(demo_data_raw)
        # Build 8-channel
        acc_demo = demo_arr[:, :3]
        gyro_demo = demo_arr[:, 3:]
        am = np.sqrt(acc_demo[:, 0]**2 + acc_demo[:, 1]**2 + acc_demo[:, 2]**2).reshape(-1, 1)
        gm = np.sqrt(gyro_demo[:, 0]**2 + gyro_demo[:, 1]**2 + gyro_demo[:, 2]**2).reshape(-1, 1)
        demo_8ch = np.hstack([acc_demo, gyro_demo, am, gm])

        n_demo = len(demo_arr)
        demo_wins_X = []
        demo_win_starts = []
        for start in range(0, n_demo - WINDOW_SIZE + 1, STRIDE):
            end = start + WINDOW_SIZE
            features = compute_features(demo_8ch[start:end])
            demo_wins_X.append(features)
            demo_win_starts.append(start)

        demo_X = np.array(demo_wins_X)
        demo_X_scaled = scaler.transform(demo_X)
        demo_preds = lr.predict(demo_X_scaled)
        demo_probs = lr.predict_proba(demo_X_scaled)[:, 1]

        pos_windows = np.sum(demo_preds == 1)
        print(f"Total windows in demo: {len(demo_preds)}")
        print(f"Predicted sit-to-stand windows: {pos_windows}")
        print(f"Ground truth events: {len(demo_ground_truth)}")

        # Show which windows are positive
        print(f"\nPositive window details:")
        for i, (pred, start) in enumerate(zip(demo_preds, demo_win_starts)):
            if pred == 1:
                end = start + WINDOW_SIZE
                prob = demo_probs[i]
                print(f"  Window {i}: samples {start}-{end}, prob={prob:.3f}")

        # Count clusters (consecutive positive windows, merge gap <= 2)
        clusters = []
        current_cluster = None
        for i, pred in enumerate(demo_preds):
            if pred == 1:
                if current_cluster is None:
                    current_cluster = [i, i]
                elif i - current_cluster[1] <= 3:  # merge gap <= 2 windows
                    current_cluster[1] = i
                else:
                    clusters.append(current_cluster)
                    current_cluster = [i, i]
        if current_cluster is not None:
            clusters.append(current_cluster)

        print(f"\nDetected event clusters (reps): {len(clusters)}")
        for ci, (cs, ce) in enumerate(clusters):
            s_start = demo_win_starts[cs]
            s_end = demo_win_starts[ce] + WINDOW_SIZE
            print(f"  Cluster {ci+1}: windows {cs}-{ce}, samples {s_start}-{s_end}")

    print(f"\n{'=' * 60}")
    print("Phase 1 complete!")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
