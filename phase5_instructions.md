# FrailTrack Phase 5: Results Screen

## Context
Phase 4 is complete. The full pipeline runs end-to-end and produces session indicators in the console. Now build the visual results screen. Read `frailtrack_build_spec.md` for full context.

## Goal
When a test completes, display a beautiful, clear results screen instead of console output. Mobile-first, large text, accessible to older adults.

## What to build

### Results screen layout (replaces the timer/capture screen after test ends)

**Header:**
- "Your Results" title
- Date and time of test
- Educational disclaimer: small text at top — "This is a screening tool, not a diagnosis. Share results with your healthcare provider."

**Tier 1: Rep Count (prominent, top of page)**
- Large number (e.g., "12")
- Label: "Repetitions in 30 seconds"
- Subtitle showing context: "Typical range for your age group: 12–17" (use the normative table from the spec — for now, hardcode one age range or let user select age group)

**Tier 2: Power Score**
- Display: "2.85 W/kg"
- Label: "Relative Muscle Power"
- Color-coded status: green if within range, yellow/orange if below
- Small note: "Based on Alcázar et al. (2021) equation"

**Tier 3: Movement Quality — four cards in a 2×2 grid**

Card 1: **Push-off Force**
- Per-rep bar chart (small, inline) showing peak acceleration for each rep
- Overall status: "Intermediate" / "Low" / "Strong"
- Maps to: Weakness
- Color: green/yellow/red based on threshold

Card 2: **Rotational Speed**
- Per-rep bar chart showing peak gyro for each rep
- Overall status based on values
- Maps to: Slowness

Card 3: **Consistency (CV)**
- Single number displayed: "CV = 0.18"
- Status: "Stable" / "Moderate variability" / "High variability"
- Maps to: Exhaustion
- Explain in plain language: "Your reps were consistent" or "Your performance varied significantly across reps"

Card 4: **Fatigue Trend**
- Mini line chart: peak acceleration per rep with trend line
- Slope value and status: "Stable" / "Mild decline" / "Significant decline"
- Maps to: Exhaustion
- Plain language: "Your performance was steady throughout" or "Your later reps were weaker than your first"

**Bottom:**
- "Save & View Dashboard" button (just saves to a JavaScript variable for now — localStorage comes in Phase 6)
- "New Test" button (returns to pre-test screen)

### Charts
Use inline SVG or Canvas for the per-rep charts. Keep it simple — no charting library. Each chart is just 5–20 bars or dots. The fatigue trend line is a simple straight line from (1, intercept+slope) to (n, intercept+n*slope).

### Color coding
- Green: #4CAF50 (within expected range / stable)
- Yellow/Amber: #FF9800 (moderate / watch)
- Red/Orange: #F44336 (flagged / below range / declining)

### Responsive layout
- Single column on phone (cards stack vertically)
- Cards should be tappable to expand for more detail (optional — nice to have)

### Plain language mapping
Each card should show the clinical dimension in small text:
- "Weakness indicator" / "Slowness indicator" / "Exhaustion indicator"
But the primary label should be plain English, not clinical jargon.

## Do NOT build yet
- Dashboard (trend over multiple sessions)
- localStorage persistence
- Setup screen (height input)

## Done when
- After simulate mode completes, a clean results screen appears with all three tiers
- Per-rep bar charts render correctly
- Status flags show with appropriate colors
- The page looks good on a phone-sized viewport (use browser dev tools mobile preview)
- "New Test" returns to the start screen
