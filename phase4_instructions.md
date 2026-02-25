# FrailTrack Phase 4: Event Clustering & Quality Assessment

## Context
Phase 3 is complete. After a test, you have an array of window predictions (0 or 1) and access to the raw sensorBuffer. Read `frailtrack_build_spec.md` for full context.

## Goal
Turn window predictions into rep events, extract per-rep quality features, and compute session-level indicators. Still console output only — no results UI yet.

## What to build

### 1. Event clustering: windows → reps
```javascript
function clusterEvents(predictions, windowSize = 128, stride = 64) {
    // predictions: array of {index, prediction, probability} for each window
    // Each window's start sample = index * stride
    // Each window's end sample = index * stride + windowSize
    
    // Step 1: find consecutive runs of prediction=1
    // Step 2: merge runs separated by ≤ 2 windows (≤ 1.28 seconds gap)
    // Step 3: each merged cluster = one rep event
    // Step 4: for each event, record:
    //   - start_sample: first positive window's start
    //   - end_sample: last positive window's end
    //   - start_time: start_sample / 50 (seconds)
    //   - end_time: end_sample / 50 (seconds)
    
    // Return array of events: [{start_sample, end_sample, start_time, end_time}, ...]
}
```

### 2. Gravity removal
Before extracting per-rep features, remove gravity from accelerometer:
```javascript
function removeGravity(buffer) {
    // Simple first-order high-pass filter
    // filtered[0] = 0
    // filtered[i] = 0.9 * (filtered[i-1] + raw[i] - raw[i-1])
    // Apply independently to ax, ay, az
    // Return new buffer with [filtered_ax, filtered_ay, filtered_az, gx, gy, gz]
    
    const alpha = 0.9;
    const filtered = [];
    filtered.push([0, 0, 0, buffer[0][3], buffer[0][4], buffer[0][5]]);
    
    for (let i = 1; i < buffer.length; i++) {
        const fax = alpha * (filtered[i-1][0] + buffer[i][0] - buffer[i-1][0]);
        const fay = alpha * (filtered[i-1][1] + buffer[i][1] - buffer[i-1][1]);
        const faz = alpha * (filtered[i-1][2] + buffer[i][2] - buffer[i-1][2]);
        filtered.push([fax, fay, faz, buffer[i][3], buffer[i][4], buffer[i][5]]);
    }
    return filtered;
}
```

### 3. Per-rep feature extraction
For each detected rep event, go to the filtered buffer and extract:

```javascript
function extractRepFeatures(filteredBuffer, event) {
    const samples = filteredBuffer.slice(event.start_sample, event.end_sample);
    
    // 1. Peak dynamic acceleration magnitude (m/s²)
    // Convert from g's to m/s²: multiply by 9.81
    // dynamic_accel_mag = sqrt(fax² + fay² + faz²) * 9.81 for each sample
    // peak = max of these values
    
    // 2. Time per rep (seconds)
    // duration = (end_sample - start_sample) / 50
    
    // 3. Peak gyroscope magnitude (rad/s)
    // gyro_mag = sqrt(gx² + gy² + gz²) for each sample
    // peak = max of these values
    
    return {
        peak_accel: /* number in m/s² */,
        duration: /* number in seconds */,
        peak_gyro: /* number in rad/s */
    };
}
```

### 4. Session-level indicators
After extracting per-rep features for all reps:

```javascript
function computeSessionIndicators(repFeatures, heightM) {
    const n = repFeatures.length;
    
    // Rep count
    const repCount = n;
    
    // Mean time per rep
    const meanTime = repFeatures.reduce((s, r) => s + r.duration, 0) / n;
    
    // Alcázar relative power (W/kg)
    // Power = [0.9 × 9.81 × (height × 0.5 − 0.46)] / (meanTime × 0.5)
    // 0.46 = standard chair height in meters
    const power = (0.9 * 9.81 * (heightM * 0.5 - 0.46)) / (meanTime * 0.5);
    
    // CV of peak acceleration
    const accels = repFeatures.map(r => r.peak_accel);
    const meanAccel = accels.reduce((a, b) => a + b, 0) / n;
    const stdAccel = Math.sqrt(accels.reduce((s, a) => s + (a - meanAccel) ** 2, 0) / n);
    const cvAccel = meanAccel > 0 ? stdAccel / meanAccel : 0;
    
    // Fatigue slope (linear regression of peak_accel vs rep number)
    // rep numbers: 1, 2, 3, ...
    // slope = (n * Σ(x*y) - Σx * Σy) / (n * Σ(x²) - (Σx)²)
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    for (let i = 0; i < n; i++) {
        const x = i + 1;
        const y = accels[i];
        sumX += x;
        sumY += y;
        sumXY += x * y;
        sumX2 += x * x;
    }
    const fatigueSlope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    
    // Flags
    const flags = {
        weakness_accel: meanAccel < 2.7 ? 'low' : meanAccel > 8.5 ? 'high' : 'intermediate',
        weakness_power: power < 2.0 ? 'below_range' : 'within_range',
        exhaustion_cv: cvAccel < 0.15 ? 'stable' : cvAccel < 0.30 ? 'moderate' : 'high',
        exhaustion_fatigue: fatigueSlope > -0.05 ? 'stable' : fatigueSlope > -0.15 ? 'mild_decline' : 'significant_decline'
    };
    
    return { repCount, meanTime, power, cvAccel, fatigueSlope, flags };
}
```

### 5. Wire it up
After model inference (from Phase 3), add:
1. Cluster windows into events
2. Remove gravity from raw buffer
3. Extract per-rep features
4. Compute session indicators (use a default height of 1.70m for now)
5. Console.log everything:
   - Number of reps detected
   - Per-rep features table
   - Session indicators and flags
   - If simulate mode: compare detected rep count against ground truth event count

### 6. Validation (simulate mode)
- Rep count should be within ±1 of ground truth events in demo_data.json
- Peak accel should be 1–15 m/s² (not 0.001, not 500)
- Time per rep should be 1–5 seconds (not 0.01, not 30)
- Power should be 0.5–5 W/kg
- CV should be 0–1
- If values are wildly off: check unit conversions (g's vs m/s²), gravity removal, or feature extraction

## Do NOT build yet
- Results screen UI
- Dashboard
- localStorage

## Done when
- Simulate mode runs end-to-end: capture → windows → features → model → events → per-rep quality → session indicators
- Console shows plausible per-rep values and session indicators
- Rep count approximately matches ground truth
