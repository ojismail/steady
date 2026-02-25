# FrailTrack: Smartphone-Based Frailty Screening App — Build Spec

## Overview

A client-side web app that turns a smartphone into a frailty screening tool. The user places their phone at their waist, performs the 30-second chair stand test, and receives a multi-dimensional movement quality assessment — not just a rep count. Results are saved locally and displayed on a longitudinal dashboard.

**Everything runs in the browser. No server. No backend. No internet needed after page load.**

---

## Why This Exists

The 30-second chair stand test is clinically validated but only gives you one number: reps completed. Research (Millor et al., 2013; Park et al., 2021) shows that sensor-derived features — peak acceleration, angular velocity, movement variability, fatigue slope — differentiate frailty levels even when rep counts are identical. A person's movement quality can decline for months while their rep count stays normal. By the time rep count drops, they're already frail. This app catches the trajectory.

---

## Architecture

```
Phone sensors (50Hz) → Raw data buffer (30s)
    → Windowing (2.56s, 50% overlap)
    → Feature extraction (48 features/window)
    → LR model (48 weights + bias + scaler)
    → Window classification (sit-to-stand vs other)
    → Event clustering (consecutive positives → reps)
    → Per-rep quality extraction (from raw signal)
    → Session summary (6 indicators)
    → Display + save to localStorage
    → Dashboard (trends across sessions)
```

Single HTML file. All JavaScript. No dependencies except the Web Sensor API.

---

## Screens

### Screen 1: Setup (first time only)
- Enter height (cm or feet/inches — convert to meters internally)
- Brief explanation of the test
- Save to localStorage

### Screen 2: Pre-Test
- Instructions: "Place your phone in your waistband at your front hip. Sit in a standard chair with arms crossed over chest. When ready, tap Start."
- "Start Test" button
- "Simulate Demo" button (for desktop/poster demo — replays real sensor data)
- Link to Dashboard

### Screen 3: Active Test
- Large countdown timer: 30 → 0
- Live rep counter (updates as reps are detected in real time)
- Visual indicator that sensors are active (pulsing dot or waveform)
- Audio beep at start and end

### Screen 4: Results
- **Tier 1: Rep Count** — large number, with normative range for context (e.g., "12 reps — typical for ages 60-64: 12-17")
- **Tier 2: Power Score** — Alcázar relative power in W/kg, with age-appropriate flag (within range / below range)
- **Tier 3: Movement Quality** — four indicators displayed as cards or gauges:
  - Peak acceleration trend (per-rep bar chart with regression line)
  - Peak gyro magnitude trend (per-rep bar chart)
  - CV (single number with status: stable / variable / highly variable)
  - Fatigue slope (single number with status: stable / declining / significantly declining)
- Each card shows the Fried frailty dimension it maps to (weakness / slowness / exhaustion)
- "Save & Return to Dashboard" button

### Screen 5: Dashboard
- Session history list (date, rep count, power, flags)
- Trend charts: select any indicator and see it plotted over all past sessions
- Key trends highlighted (e.g., "Fatigue slope has worsened over last 3 sessions")

---

## The ML Model

### What model and why
Logistic Regression trained on UCI HAPT dataset. NOT Random Forest — RF achieved 0% recall on elderly users in external validation. LR generalized at 92.6% recall on unseen elderly subjects from SisFall.

### How to train and export

**Step 1: Load UCI HAPT raw data**
- Already downloaded at `../data/uci_hapt/RawData/`
- Raw files: `acc_expXX_userYY.txt` (3 columns: ax, ay, az in g's)
- Raw files: `gyro_expXX_userYY.txt` (3 columns: gx, gy, gz in rad/s)
- Labels: `labels.txt` (5 columns: exp_id, user_id, activity_id, start_sample, end_sample)
- 30 subjects, 50Hz sampling rate
- Activity ID 8 = sit-to-stand (the positive class)

**Step 2: Window the data**
- Window size: 128 samples (2.56 seconds at 50Hz)
- Stride: 64 samples (50% overlap)
- Label each window by majority vote (>50% of samples from one activity → that label)
- Binary: activity 8 → 1, everything else → 0
- Track subject_id per window

**Step 3: Compute features (48 per window)**
For each window, compute across 8 channels:
- Channels: ax, ay, az, gx, gy, gz, accel_mag, gyro_mag
- accel_mag = sqrt(ax² + ay² + az²)
- gyro_mag = sqrt(gx² + gy² + gz²)
- Statistics per channel: mean, std, min, max, range, energy (mean of squared values)
- Total: 8 channels × 6 stats = 48 features

Feature names (in order — this order MUST match between Python training and JavaScript inference):
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

**Step 4: Train LR**
```python
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import json

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # X is (n_windows, 48)
lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
lr.fit(X_scaled, y)  # y is binary (0 or 1)

# Export for JavaScript
model = {
    'weights': lr.coef_[0].tolist(),      # 48 numbers
    'bias': float(lr.intercept_[0]),       # 1 number
    'means': scaler.mean_.tolist(),         # 48 numbers
    'stds': scaler.scale_.tolist(),         # 48 numbers
}
with open('model.json', 'w') as f:
    json.dump(model, f)
```

**Step 5: Embed in JavaScript**
```javascript
const MODEL = {
    weights: [/* 48 numbers from model.json */],
    bias: /* 1 number */,
    means: [/* 48 numbers */],
    stds: [/* 48 numbers */]
};

function predictWindow(features) {
    // features is array of 48 numbers in the exact order above
    let sum = MODEL.bias;
    for (let i = 0; i < 48; i++) {
        const scaled = (features[i] - MODEL.means[i]) / MODEL.stds[i];
        sum += MODEL.weights[i] * scaled;
    }
    const prob = 1 / (1 + Math.exp(-sum));
    return prob > 0.5 ? 1 : 0;  // threshold at 0.5
}
```

---

## Sensor Data Capture

### Web Sensor API
```javascript
// Request permission (required on iOS)
if (typeof DeviceMotionEvent.requestPermission === 'function') {
    await DeviceMotionEvent.requestPermission();
}

// Use DeviceMotionEvent for broadest compatibility
// accelerationIncludingGravity gives raw accel (matches UCI HAPT which includes gravity)
// rotationRate gives gyroscope in degrees/sec — convert to rad/s (multiply by π/180)
window.addEventListener('devicemotion', (event) => {
    const ax = event.accelerationIncludingGravity.x / 9.81;  // convert m/s² to g's
    const ay = event.accelerationIncludingGravity.y / 9.81;
    const az = event.accelerationIncludingGravity.z / 9.81;
    const gx = event.rotationRate.alpha * Math.PI / 180;  // deg/s to rad/s
    const gy = event.rotationRate.beta * Math.PI / 180;
    const gz = event.rotationRate.gamma * Math.PI / 180;
    
    buffer.push({ ax, ay, az, gx, gy, gz, timestamp: event.timeStamp });
}, { frequency: 50 });  // Note: actual frequency may vary — resample if needed
```

### Important: Sampling Rate
The Web Sensor API doesn't guarantee exactly 50Hz. The actual rate depends on the device. After capture, resample to 50Hz by interpolating timestamps to evenly-spaced 20ms intervals. This ensures the 128-sample windows represent exactly 2.56 seconds.

---

## Post-Processing: Windows → Reps

After classifying all windows:

1. **No smoothing, no minimum duration** — use minimal post-processing (our experiments showed this works best with LR)
2. **Merge gap**: if two clusters of positive windows are separated by ≤ 2 windows (≤ 1.28s), merge them into one event
3. **Count clusters** = rep count
4. **Rep boundaries**: each cluster's first and last window define the rep's time range in the raw signal

---

## Quality Assessment: Per-Rep Features

For each detected rep, go back to the raw sensor buffer and extract:

### Gravity Removal
Before extracting peak dynamic acceleration, apply a simple high-pass filter:
- Compute a running mean of the accelerometer signal over the entire 30s capture (this approximates gravity)
- Subtract it from the raw signal to get dynamic acceleration
- OR use a simple first-order high-pass: `filtered[i] = 0.9 * (filtered[i-1] + raw[i] - raw[i-1])`
- Then compute magnitude: `dynamic_accel_mag = sqrt(filtered_ax² + filtered_ay² + filtered_az²)`

### Per-Rep Extraction
Within each rep's time boundaries in the raw buffer:

1. **Peak dynamic acceleration magnitude** (m/s²): max of dynamic_accel_mag within rep
   - Frailty dimension: Weakness
   - Reference: frail ~2.7 m/s², non-frail ~8.5 m/s² (Galán-Mercant, 2013)
   - NOTE: these thresholds are approximate — our measure is magnitude, not vertical axis

2. **Time-per-rep** (seconds): end_time - start_time
   - Frailty dimension: Slowness

3. **Peak gyroscope magnitude** (rad/s): max of sqrt(gx² + gy² + gz²) within rep
   - Frailty dimension: Slowness
   - Reference: lower peaks = frailer (Millor et al., 2013, p < 0.001)

### Session-Level Indicators

4. **Relative muscle power** (W/kg):
   ```
   Power = [0.9 × 9.81 × (height_m × 0.5 − 0.46)] / (mean_time_per_rep × 0.5)
   ```
   - 0.46m = standard chair height
   - height_m = user's height in meters (from setup)
   - Frailty dimension: Weakness
   - Reference: Alcázar et al., 2021 age/sex normative cut-off points

5. **Coefficient of Variation (CV)**:
   ```
   CV = std(peak_accel_per_rep) / mean(peak_accel_per_rep)
   ```
   - Compute for peak acceleration (could also compute for gyro, time)
   - Frailty dimension: Exhaustion
   - Thresholds: < 0.15 = stable, 0.15-0.30 = moderate, > 0.30 = high variability (exhaustion flag)
   - Reference: Park et al., 2021

6. **Fatigue slope**:
   ```
   Fit linear regression: peak_accel = slope × rep_number + intercept
   ```
   - Simple least-squares: slope = (n×Σxy - Σx×Σy) / (n×Σx² - (Σx)²)
   - Frailty dimension: Exhaustion
   - Interpretation: negative slope = declining performance
   - Thresholds: > -0.05 = stable, -0.05 to -0.15 = mild decline, < -0.15 = significant decline (these are approximate — no published threshold for this specific setup)
   - Reference: Schwenk/Lindemann found −0.0037 m/s per rep in older women

---

## Simulate Mode

For demo on desktop or when sensors aren't available:

### Embedding demo data
Export one UCI HAPT subject's raw 6-channel data (a subject with 2-3 clear sit-to-stands). Store as a JavaScript array in the HTML file. During simulate mode, feed this data into the processing pipeline at 50Hz (using setInterval at 20ms) as if it were coming from the sensors. The UI should behave identically — countdown, live rep counter, results screen.

### How to export demo data
```python
import json
# Pick a subject with clean sit-to-stands (e.g., subject 1 or subject 24)
# Load their acc + gyro data for one experiment
# Take a 30-second window (1500 samples) that contains sit-to-stand events
# Export as JSON array of [ax, ay, az, gx, gy, gz] rows
demo_data = raw_signal[start:start+1500].tolist()
with open('demo_data.json', 'w') as f:
    json.dump(demo_data, f)
```

Pick a subject that had good detection results in LOSO-CV (e.g., subject 24 had perfect F1 = 1.0).

---

## Data Storage (localStorage)

### User Profile
```json
{
    "height_m": 1.72,
    "setup_date": "2026-02-16"
}
```

### Session Record
```json
{
    "id": "session_20260216_143022",
    "date": "2026-02-16T14:30:22",
    "rep_count": 12,
    "power_wkg": 2.85,
    "mean_time_per_rep": 2.31,
    "per_rep": [
        {"rep": 1, "peak_accel": 5.2, "peak_gyro": 2.1, "duration": 2.1},
        {"rep": 2, "peak_accel": 5.0, "peak_gyro": 2.0, "duration": 2.2},
        ...
    ],
    "cv_accel": 0.18,
    "fatigue_slope": -0.08,
    "flags": {
        "weakness_accel": "intermediate",
        "weakness_power": "within_range",
        "slowness_gyro": "within_range",
        "exhaustion_cv": "stable",
        "exhaustion_fatigue": "mild_decline"
    }
}
```

---

## Normative Reference Ranges (for display)

### Rep Count (Jones et al., 1999 — 30s CST norms)
| Age | Women | Men |
|-----|-------|-----|
| 60-64 | 12-17 | 14-19 |
| 65-69 | 11-16 | 12-18 |
| 70-74 | 10-15 | 12-17 |
| 75-79 | 10-15 | 11-17 |
| 80-84 | 9-14 | 10-15 |
| 85-89 | 8-13 | 8-14 |
| 90-94 | 4-11 | 7-12 |

### Peak Dynamic Acceleration
- < 2.7 m/s²: Low (frail range per Galán-Mercant)
- 2.7 – 8.5 m/s²: Intermediate
- > 8.5 m/s²: High (non-frail range)
- NOTE: approximate — magnitude vs vertical axis

### Power (simplified from Alcázar et al., 2021)
- Display the computed value and note "compare with your clinician for age-appropriate ranges"
- Do NOT display hard frail/non-frail cutoffs — the equation is adapted, not validated on this protocol

---

## UI/UX Notes

- **Mobile-first**: designed for phone screens (portrait orientation)
- **Large text**: target users are older adults — minimum 16px body text, large buttons
- **High contrast**: dark text on light background, clear color coding for flags (green = ok, yellow = watch, red = flag)
- **Simple language**: "Your push-off force is steady" not "CV of peak dynamic acceleration magnitude is within one standard deviation"
- **Educational framing**: "This is a screening tool, not a diagnosis. Share results with your healthcare provider."
- **No login**: everything is local to the device

---

## Build Order (suggested for Claude Code)

1. **Phase 1**: Train LR model on UCI HAPT, export weights as JSON. Export one subject's raw data for simulate mode.
2. **Phase 2**: Build the sensor capture and windowing pipeline in JavaScript. Test with simulate mode.
3. **Phase 3**: Implement feature extraction and model inference. Verify predictions match Python output on the demo data.
4. **Phase 4**: Implement event clustering and per-rep quality extraction.
5. **Phase 5**: Build the results screen with all three tiers.
6. **Phase 6**: Build the dashboard with localStorage persistence and trend charts.
7. **Phase 7**: Polish UI, add setup screen, handle sensor permissions, add error states.

---

## Project Structure

The app lives in `project/app/` as a subfolder of the existing class project. The UCI HAPT dataset is already downloaded at `project/data/uci_hapt/` (contains `RawData/` with acc/gyro files and `labels.txt`).

```
project/
├── data/
│   └── uci_hapt/
│       └── RawData/
│           ├── acc_exp01_user01.txt
│           ├── gyro_exp01_user01.txt
│           ├── labels.txt
│           └── ...
├── app/
│   ├── index.html          ← single-file app (HTML + CSS + JS all inline)
│   ├── train_model.py      ← trains LR, exports model + demo data
│   ├── model.json           ← trained LR weights (embedded into index.html)
│   └── demo_data.json       ← one subject's raw data for simulate mode (embedded into index.html)
├── src/                     ← existing class project Python scripts
├── Results/                 ← existing class project results
└── ...
```

## Files to Produce

1. `project/app/index.html` — single-file app (HTML + CSS + JavaScript all inline, with model weights and demo data embedded)
2. `project/app/model.json` — trained LR weights (generated by train_model.py, then embedded into index.html)
3. `project/app/demo_data.json` — one subject's raw sensor data for simulate mode (generated by train_model.py, then embedded into index.html)
4. `project/app/train_model.py` — Python script that reads from `../data/uci_hapt/RawData/`, trains LR, exports model.json and demo_data.json

---

## Validation Checklist

- [ ] Simulate mode produces rep count within ±1 of ground truth for the demo subject
- [ ] Feature values from JavaScript match Python output (within floating point tolerance)
- [ ] Sensor capture works on Chrome Android
- [ ] Sensor capture works on Safari iOS (with permission prompt)
- [ ] Dashboard persists across page reloads
- [ ] All quality indicators produce plausible values
- [ ] Responsive layout works on phone screens
- [ ] Educational disclaimer is visible on results screen
