# FrailTrack Phase 2: Sensor Capture & Simulate Mode

## Context
Phase 1 is complete. You have `model.json` and `demo_data.json` in `project/app/`. Read `frailtrack_build_spec.md` for full context.

## Goal
Create `project/app/index.html` — a single HTML file with inline CSS and JavaScript. This phase implements ONLY the sensor capture layer and simulate mode. No model inference, no results screen, no dashboard yet.

## What to build

### Basic page structure
- Mobile-first layout (viewport meta tag, responsive)
- Large fonts (min 16px body, buttons 18px+)
- High contrast (dark on light)
- Three visible elements for now: a "Start Test" button, a "Simulate Demo" button, and a timer display

### Simulate mode (build this FIRST — you can test it on desktop)

When "Simulate Demo" is tapped:
1. Load the demo data from `demo_data.json` (embed it directly in the HTML as a JavaScript const)
2. Start a 30-second countdown timer (displayed prominently)
3. Feed the demo data into a buffer at 50Hz using setInterval(20ms)
   - Each tick, push the next [ax, ay, az, gx, gy, gz] sample into a `sensorBuffer` array
   - If you run out of samples before 30s, loop back to the start
4. When countdown hits 0, stop the data feed
5. Display: "Test complete. [sensorBuffer.length] samples captured."
6. Console.log the first and last 5 samples to verify data looks correct

### Real sensor mode

When "Start Test" is tapped:
1. Request sensor permission (important for iOS):
```javascript
if (typeof DeviceMotionEvent !== 'undefined' && 
    typeof DeviceMotionEvent.requestPermission === 'function') {
    const permission = await DeviceMotionEvent.requestPermission();
    if (permission !== 'granted') {
        alert('Sensor permission denied. Please allow motion access.');
        return;
    }
}
```
2. Start listening to `devicemotion` events
3. Convert to matching units:
   - `ax = event.accelerationIncludingGravity.x / 9.81` (m/s² → g's)
   - `ay = event.accelerationIncludingGravity.y / 9.81`
   - `az = event.accelerationIncludingGravity.z / 9.81`
   - `gx = event.rotationRate.alpha * Math.PI / 180` (deg/s → rad/s)
   - `gy = event.rotationRate.beta * Math.PI / 180`
   - `gz = event.rotationRate.gamma * Math.PI / 180`
4. Push each reading to `sensorBuffer` with timestamp
5. 30-second countdown displayed
6. When countdown hits 0, stop listening
7. Resample to exactly 50Hz (the browser may not deliver exactly 50Hz):
   - Calculate actual sample rate from timestamps
   - If close to 50Hz (45-55Hz), use as-is
   - If significantly different, linearly interpolate to 50Hz (1500 samples for 30s)
8. Display: "Test complete. [sensorBuffer.length] samples captured. Actual rate: XX Hz"

### Handle missing sensors gracefully
- If `devicemotion` event fires but values are null → show message: "Your device doesn't support motion sensors. Use Simulate Demo instead."
- If on desktop (no sensors at all) → the Start Test button should still exist but show an appropriate message. Simulate Demo is the fallback.

### Audio feedback
- Beep at test start (use Web Audio API — simple oscillator for 200ms)
- Beep at test end
- Keep it simple — 3 lines of AudioContext code, not an audio library

## Do NOT build yet
- Feature extraction
- Model inference
- Rep detection
- Results screen
- Dashboard
- localStorage

## Done when
- Simulate mode works on desktop: tapping "Simulate Demo" shows a 30-second countdown, feeds demo data, and reports sample count at the end
- Console shows the raw buffer data looks reasonable (accelerometer values around ±1-2 g's, gyroscope values around ±1-5 rad/s)
- Real sensor mode has permission handling and capture logic (can only be fully tested on a phone, but the code should be in place)
- Audio beeps play at start and end
