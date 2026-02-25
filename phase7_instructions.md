# FrailTrack Phase 7: Polish & Testing

## Context
Phase 6 is complete. The app is fully functional. This phase is about polish, error handling, and making it demo-ready.

## What to do

### 1. Error handling
- Sensor not available → clear message + redirect to simulate mode
- No reps detected → "No sit-to-stand movements detected. Make sure the phone is at your waist and you're standing up fully from the chair. Try again?"
- localStorage full → graceful message (unlikely but handle it)
- Very few reps (< 3) → show results but note: "Fewer than 3 reps detected. CV and fatigue indicators require more reps to be meaningful."

### 2. UI polish
- Smooth transitions between screens (CSS fade or slide, 200ms)
- Loading state while processing after capture (the computation is fast but show a brief "Analyzing..." with a spinner)
- Pulse animation on the live rep counter during the test
- The timer should be large and central during the test — the most important visual element
- Test on Chrome DevTools mobile emulation for iPhone SE, iPhone 12, Pixel 5 viewports
- Make sure nothing overflows horizontally on small screens

### 3. Educational framing
Add these text elements:
- Pre-test screen: brief explanation of the 30-second chair stand test and what the app measures
- Results screen header: "Screening tool — not a medical diagnosis"
- Dashboard: "Track changes over time. Discuss significant changes with your healthcare provider."
- Each quality card: one sentence explaining what the metric means in plain English

### 4. Simulate mode improvements
- During simulate mode, add a small "DEMO" badge in the corner so it's obvious this isn't real data
- After simulate demo results, show a note: "This used pre-recorded data for demonstration. Start a real test to capture your own movement."
- Simulate mode sessions should be tagged as demo in localStorage (so they can be filtered out or shown differently on the dashboard)

### 5. Visual identity
- App title: "FrailTrack"
- Subtitle: "Sit-to-Stand Movement Assessment"
- Clean, medical/health aesthetic — not playful
- Color palette: blues and whites, with green/yellow/red for status indicators
- Consider a simple logo/icon (even just a text mark) in the header

### 6. Test the full flow
Run through this exact sequence and verify everything works:

1. Open the app fresh (clear localStorage first)
2. Setup screen appears → enter height → save
3. Pre-test screen appears
4. Tap Simulate Demo → 30s countdown → results appear
5. Verify all three tiers display correctly
6. Save → dashboard shows 1 session
7. Go back → run simulate demo again → save
8. Go back → run simulate demo again → save
9. Dashboard now shows 3 sessions with trend charts
10. Tap a past session → its results display
11. Change metric in trend chart → chart updates
12. Refresh the page → data persists
13. Go to Settings → change height → verify new power calculation on next test

### 7. Performance check
- The entire processing pipeline (windowing + features + model + clustering + quality) should complete in under 1 second on a modern phone
- If it's slow, the bottleneck is likely feature extraction — make sure there are no unnecessary array copies or recomputations

## Done when
- The app looks professional and is demo-ready
- All error states are handled gracefully
- The full test sequence above passes
- It looks good on mobile viewports
- Educational framing is present throughout
- A non-technical person could use it (assuming they know what the chair stand test is)
