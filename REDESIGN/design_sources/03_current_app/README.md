# Current App Captures
This folder contains the current visual baseline for NeuroMood Suite, NeuroMood Hub, installers, and uninstallers.
## Canonical folder
`extracted/current_app_captures/`
This is the single canonical capture set. It contains 60 PNG screenshots organized by product, theme, and module.
## Files
- `linked_captures.html`: lightweight HTML viewer that references the PNG files by relative path.
- `unified captures.html`: self-contained HTML viewer with embedded images.
- `manifest.json`: original capture metadata.
- `manifest_all.json`: complete capture metadata for the 60 screenshots.
## Important
Do not rename the internal screenshot files or module folders unless the HTML and JSON references are updated as well.
The PNG screenshots were deduplicated. Older duplicated folders and archive ZIPs were removed to keep the repository clean.
