# FrailTrack Phase 1: Train Model & Export Data

## Context
Read `frailtrack_build_spec.md` for full project context. This phase handles ONLY model training and data export. Do NOT build any UI or HTML yet.

## Goal
Produce three files in `project/app/`:
1. `train_model.py` — the training script
2. `model.json` — trained LR weights
3. `demo_data.json` — one subject's raw sensor data for simulate mode

## Steps

### 1. Create `project/app/` directory

### 2. Write `train_model.py` that does the following:

**Load data:**
- Read all `acc_expXX_userYY.txt` and `gyro_expXX_userYY.txt` files from `../data/uci_hapt/RawData/`
- Read `../data/uci_hapt/RawData/labels.txt` (space-separated, 5 columns: exp_id, user_id, activity_id, start_sample, end_sample)
- Combine acc + gyro into 6-channel arrays per experiment-user pair
- Units: accelerometer is in g's, gyroscope is in rad/s (already correct in UCI HAPT)

**Window the data:**
- Window size: 128 samples (2.56s at 50Hz)
- Stride: 64 samples (50% overlap)
- Label each window by majority vote (>50% of samples from one activity)
- Binary: activity_id 8 → 1, everything else → 0
- Track subject_id per window

**Compute features (48 per window):**
- Compute accel_mag = sqrt(ax² + ay² + az²) and gyro_mag = sqrt(gx² + gy² + gz²)
- 8 channels: ax, ay, az, gx, gy, gz, accel_mag, gyro_mag
- 6 stats per channel: mean, std, min, max, range (max-min), energy (mean of squared values)
- Feature order MUST be:
```
ax_mean, ax_std, ax_min, ax_max, ax_range, ax_energy,
ay_mean, ay_std, ay_min, ay_max, ay_range, ay_energy,
az_mean, az_std, az_min, az_max, az_range, az_energy,
gx_mean, gx_std, gx_min, gx_max, gx_range, gx_energy,
gy_mean, gy_std, gy_min, gy_max, gy_range, gy_energy,
gz_mean, gz_std, gz_min, gz_max, gz_range, gz_energy,
accel_mag_mean, accel_mag_std, accel_mag_min, accel_mag_max, accel_mag_range, accel_mag_energy,
gyro_mag_mean, gyro_mag_std, gyro_mag_min, gyro_mag_max, gyro_mag_range, gyro_mag_energy
```

**Train LR:**
```python
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
lr.fit(X_scaled, y)
```

**Export model.json:**
```json
{
    "weights": [48 numbers from lr.coef_[0]],
    "bias": lr.intercept_[0],
    "means": [48 numbers from scaler.mean_],
    "stds": [48 numbers from scaler.scale_]
}
```

**Export demo_data.json:**
- Pick subject 24 (had perfect F1 in LOSO-CV evaluation)
- Find an experiment for subject 24 that contains sit-to-stand events (activity 8)
- Extract 1500 samples (30 seconds at 50Hz) of raw 6-channel data centered around the sit-to-stand events
- If 1500 samples isn't enough to cover the events, take whatever continuous segment contains the sit-to-stand transitions and pad to 30s
- Format: array of arrays, each inner array is [ax, ay, az, gx, gy, gz]
- Also include the ground truth event times (start/end samples relative to the 30s window) so we can verify detection later
```json
{
    "samples": [[ax, ay, az, gx, gy, gz], ...],  // 1500 rows
    "sample_rate": 50,
    "ground_truth_events": [
        {"start_sample": 234, "end_sample": 362},
        ...
    ],
    "subject_id": 24
}
```

### 3. Run the script and verify outputs

**Print these checks:**
- Total windows and positive/negative counts
- Model coefficients range
- Feature names in order
- Demo data: number of samples, number of ground truth events
- Quick prediction test: run the model on the demo data's windows and print how many sit-to-stand windows are detected vs ground truth

## Done when
- `model.json` exists and contains weights (48), bias (1), means (48), stds (48)
- `demo_data.json` exists and contains 1500 samples of 6-channel data
- The quick prediction test detects a reasonable number of sit-to-stand windows from the demo data
