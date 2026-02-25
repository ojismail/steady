# FrailTrack Phase 3: Feature Extraction & Model Inference

## Context
Phase 2 is complete. You have `index.html` with sensor capture and simulate mode working. The `sensorBuffer` array contains 1500 samples of [ax, ay, az, gx, gy, gz] after a test. Read `frailtrack_build_spec.md` for full context.

## Goal
Add windowing, feature extraction, and LR model inference to `index.html`. After the 30-second capture, the app should classify each window and print the results. No UI for results yet — just console output.

## What to build

### 1. Embed the model weights
Load `model.json` and embed it as a JavaScript const in the HTML:
```javascript
const MODEL = {
    weights: [/* 48 numbers */],
    bias: /* 1 number */,
    means: [/* 48 numbers */],
    stds: [/* 48 numbers */]
};
```

### 2. Windowing function
```javascript
function createWindows(buffer) {
    // buffer: array of [ax, ay, az, gx, gy, gz]
    // Window size: 128 samples
    // Stride: 64 samples (50% overlap)
    // Returns array of windows, each window is array of 128 samples
    const windows = [];
    for (let start = 0; start + 128 <= buffer.length; start += 64) {
        windows.push(buffer.slice(start, start + 128));
    }
    return windows;
}
```

### 3. Feature extraction function
```javascript
function extractFeatures(window) {
    // window: array of 128 samples, each [ax, ay, az, gx, gy, gz]
    
    // First, compute magnitude channels
    // accel_mag = sqrt(ax² + ay² + az²) for each sample
    // gyro_mag = sqrt(gx² + gy² + gz²) for each sample
    
    // 8 channels: ax(0), ay(1), az(2), gx(3), gy(4), gz(5), accel_mag(6), gyro_mag(7)
    // For each channel, compute 6 stats: mean, std, min, max, range, energy
    
    // CRITICAL: feature order must match training exactly:
    // ax_mean, ax_std, ax_min, ax_max, ax_range, ax_energy,
    // ay_mean, ay_std, ... (repeat for all 8 channels)
    
    // Return array of 48 numbers
}
```

**Stats formulas:**
- mean: sum / n
- std: sqrt(sum((x - mean)²) / n)  — use population std (dividing by n, not n-1), matching numpy default
- min: minimum value
- max: maximum value
- range: max - min
- energy: mean(x²) — i.e., sum(x²) / n

### 4. Model prediction function
```javascript
function predictWindow(features) {
    // features: array of 48 numbers
    let sum = MODEL.bias;
    for (let i = 0; i < 48; i++) {
        const scaled = (features[i] - MODEL.means[i]) / MODEL.stds[i];
        sum += MODEL.weights[i] * scaled;
    }
    const probability = 1 / (1 + Math.exp(-sum));
    return { prediction: probability > 0.5 ? 1 : 0, probability };
}
```

### 5. Wire it up
After the 30-second capture completes:
1. Create windows from sensorBuffer
2. Extract features for each window
3. Run model on each window
4. Console.log:
   - Total windows created
   - Number predicted as sit-to-stand (class 1)
   - Number predicted as other (class 0)
   - The probability values for all windows (to see the distribution)
   - If using simulate mode: compare detected positives against ground truth events from demo_data.json

### 6. Validation
Run simulate mode and check:
- Number of windows should be ~44 for 1500 samples: floor((1500 - 128) / 64) + 1 = 22... actually (1500-128)/64 + 1 ≈ 22 windows. Verify.
- The windows classified as sit-to-stand should roughly align with the ground truth event times
- Feature values should be in plausible ranges:
  - accel_mag_mean: around 0.9–1.1 (gravity ≈ 1g)
  - gyro values: typically -2 to +2 rad/s for quiet periods, spikes during movement
- If zero sit-to-stand windows detected: likely a feature ordering mismatch between Python and JavaScript — debug this first

## Do NOT build yet
- Event clustering (consecutive windows → reps)
- Per-rep quality extraction
- Results screen UI
- Dashboard

## Done when
- Simulate mode captures data → windows are created → features extracted → model runs → console shows which windows are classified as sit-to-stand
- The detected positive windows correspond roughly to when sit-to-stand events actually occur in the demo data
- Feature values are in plausible ranges (not NaN, not all zeros, not wildly out of range)
