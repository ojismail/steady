# FrailTrack Phase 6: Dashboard & Persistence

## Context
Phase 5 is complete. The app captures data, runs the model, detects reps, extracts quality features, and displays results. Now add persistence and longitudinal tracking. Read `frailtrack_build_spec.md` for full context.

## Goal
Save session results to localStorage. Build a dashboard that shows trends across multiple sessions. Add the setup screen for height input.

## What to build

### 1. Setup screen (shown on first visit only)

If no user profile exists in localStorage:
- Show a welcome screen: "FrailTrack — Sit-to-Stand Assessment"
- Input: height (provide both cm and feet/inches options, convert to meters internally)
- Optional: age group selector (dropdown: 60-64, 65-69, 70-74, 75-79, 80-84, 85-89, 90-94) — used for normative comparison on results screen
- Optional: sex selector (male/female) — used for normative comparison
- "Get Started" button → saves profile to localStorage, goes to pre-test screen

localStorage key: `frailtrack_profile`
```json
{
    "height_m": 1.72,
    "age_group": "65-69",
    "sex": "female",
    "setup_date": "2026-02-16"
}
```

### 2. Save session results

When "Save & View Dashboard" is tapped on the results screen:
- Generate session ID: `session_` + timestamp
- Save to localStorage under key `frailtrack_sessions`
- This is an array of session objects:
```json
[
    {
        "id": "session_1708100000000",
        "date": "2026-02-16T14:30:22",
        "rep_count": 12,
        "power_wkg": 2.85,
        "mean_time_per_rep": 2.31,
        "per_rep": [
            {"rep": 1, "peak_accel": 5.2, "peak_gyro": 2.1, "duration": 2.1},
            {"rep": 2, "peak_accel": 5.0, "peak_gyro": 2.0, "duration": 2.2}
        ],
        "cv_accel": 0.18,
        "fatigue_slope": -0.08,
        "flags": {
            "weakness_accel": "intermediate",
            "weakness_power": "within_range",
            "exhaustion_cv": "stable",
            "exhaustion_fatigue": "mild_decline"
        }
    }
]
```

### 3. Dashboard screen

Accessible from the pre-test screen ("View Dashboard" button) and from results screen ("Save & View Dashboard").

**Session history list:**
- Sorted by date (newest first)
- Each row shows: date, rep count, power, number of flags triggered
- Tap a session to see its full results (re-render the results screen for that session)

**Trend charts (the core value of the dashboard):**
- A selector/tabs to choose which metric to view over time:
  - Rep count
  - Power (W/kg)
  - Mean peak acceleration
  - CV
  - Fatigue slope
- Chart: X axis = session dates, Y axis = selected metric
- Simple line chart with dots at each data point (SVG or Canvas, no library)
- If only 1 session, show just the single point with a message: "Complete more sessions to see trends"
- Threshold lines drawn on the chart where applicable (e.g., CV = 0.30 line)

**Trend alerts (if 3+ sessions exist):**
- Compare the last 3 sessions. If a metric has consistently worsened:
  - "Your fatigue slope has worsened over your last 3 sessions"
  - "Your consistency (CV) has increased — your reps are becoming more variable"
- Keep language simple and non-alarming. These are observations, not diagnoses.

**Delete session:**
- Swipe or long-press to delete a session (or a small delete button)
- Confirm before deleting

### 4. Navigation
The app now has multiple screens. Implement simple screen switching:
- Setup → Pre-test → Active test → Results → Dashboard
- Pre-test screen should have: "Start Test", "Simulate Demo", "Dashboard", and "Settings" (to change height/age)
- Back buttons where appropriate
- Use CSS to show/hide screen divs — no routing library needed

### 5. Update results screen
- Use the stored height from profile for Alcázar power calculation (instead of hardcoded 1.70m)
- Use stored age group and sex for normative rep count range on results screen (reference the table in frailtrack_build_spec.md)

## Do NOT do
- Don't add any external dependencies
- Don't create multiple HTML files — keep everything in one index.html

## Done when
- First visit shows setup screen, saves profile
- After a test, results can be saved
- Dashboard shows session history list
- Dashboard shows trend chart for any selected metric
- Data persists across page reloads (localStorage)
- Run simulate mode 3 times → dashboard shows 3 sessions with trend lines
- Navigation between all screens works smoothly
