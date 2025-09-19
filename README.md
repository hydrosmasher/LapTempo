
# Swim-Forge

SwimForge: Where Science Shapes Speed 🏊‍♂️

## Features
- Login & Registration
- Pre-Race Mode: enter PB + target event → recommended pacing
- Post-Race Mode: enter splits → ML model predicts optimal splits → shows differences with red/green highlights
- Models auto-train in the background on first run, cached in `models/`
- Sidebar shows model training progress + stroke statuses
- Dropdown auto-refreshes to include new models as they finish training

## Usage
1. Place datasets (`*_dataset.csv`) inside `Swim-Forge/`
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run:
   ```bash
   streamlit run app.py
   ```
