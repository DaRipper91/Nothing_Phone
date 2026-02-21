# Palette's Journal

## 2026-02-19 - CLI Interaction Patterns
**Learning:** For recovery tools where users are stressed, highlighting key actions (like button presses) with color reduces cognitive load and prevents missteps.
**Action:** Always use color hierarchy (Cyan for keys, Green for actions, Red for errors) in interactive CLI scripts, but check for TTY to avoid garbage output.
## 2024-05-22 - [CLI Recovery Tool Visual Hierarchy]
**Learning:** In high-stress recovery scenarios (holding buttons, waiting for narrow timing windows), plain text output is easy to miss. Color-coding success (Green) and critical keys (Cyan) reduces cognitive load.
**Action:** Always implement a `Colors` class for CLI tools that require real-time user interaction with hardware.
