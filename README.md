# Swim Forge (Reverted UI)
Reverted to the simpler UI (no photo backgrounds). Banner & logo remain, inputs & functionality are unchanged.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- Deep Learning toggle is visible only if a model file exists in `models/` (`pacing_head.pt` or `pacing_head.pkl`). This repo ships **without** model binaries.
- PNG export of charts requires `vl-convert-python`.
- SVG banner/logo are in `assets/`. Use `cairosvg` to generate PNGs if desired.
- Generated: 2025-08-16T11:11:25.397573
