# Flow Navy — motion graphics showreel

A 32-second, 1920×1080 showreel. Every frame is generated in code: Canvas 2D handles the type, HUD and graphic scenes, and three.js handles the 3D ocean and tunnel. No generative video model is used.

- `index.html` / `main.js`: the composition. Open it through any static server to play it live (Space pauses, ← → seek).
- `tools/storyboard.mjs`: captures key frames into `storyboard/` (a contact sheet plus shot notes).
- `node tools/storyboard.mjs`: needs Playwright (Chromium).
