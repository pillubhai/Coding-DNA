---
title: wildfire-containment-v0
emoji: "🔥"
colorFrom: red
colorTo: orange
sdk: docker
app_port: 7860
pinned: false
---

# WildfireContainment-v0

## Overview
WildfireContainment-v0 is a comprehensive, real-world OpenEnv environment where an AI agent controls suppression resources to minimize fire spread and protect critical structures.

Designed for the **India's First OpenEnv AI Hackathon** (Meta x Hugging Face x PyTorch), it balances complex environmental dynamics (wind, spot fires, fuel consumption) with strategic resource management.

---

## 🏗️ Environment Logic

- **Grid Size**: 20x20
- **Channels**: 
  - `fuel`: Available combustible material (0.0-1.0).
  - `fire_intensity`: Current combustion level (0.0-1.0).
  - `moisture`: Applied suppression or natural wetness (0.0-1.0).
  - `structures`: Binary grid of high-value assets requiring protection.
- **Dynamics**: 
  - **Spread**: Fire moves to adjacent 8 cells based on ignition probability, biased by **Wind Direction** and **Speed**.
  - **Spot Fires**: High-intensity fires have a chance to throw sparks downwind, starting new fires several cells away.
- **Agents**:
  - **1 Air Tanker**: High mobility, drops 3x3 water (moisture +0.5). Limited water capacity, must refill at grid edges.
  - **2 Ground Crews**: Low mobility, suppresses current 1x1 cell fire (intensity -0.2). Consumes stamina, must rest at grid edges.

---

## 🎮 Action & Observation Spaces

### 🕹️ Action Space
A `WildfireAction` object containing a list of 3 unit actions:
- `move`: 0-7 directions, 8=stay.
- `act`: Binary flag to drop water (Tanker) or suppress fire (Crew).

### 🔍 Observation Space
A `WildfireObservation` object containing:
- 20x20 fuel, fire, moisture, and structure grids.
- Unit locations and resource levels.
- Current wind vector.

---

## 📈 Reward System
- `(+)` Fire intensity reduction (Fire extinguished).
- `(+)` Structure survival bonus (per step).
- `(-)` Fire spread (New cells ignited).
- `(-)` Structure loss (Large penalty).
- `(+)` Full containment bonus (Completion).

---

## 🚀 Setup & Execution

### 1. Start the Agent Backend
The API server must be running to process environment dynamics.
```bash
pip install -r requirements.txt
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### 2. Start the Custom Visual Dashboard
Open a **second terminal** and run the following to serve the beautiful graphical UI:
```bash
cd frontend
python -m http.server 3000
```
Then, open **http://localhost:3000** in your web browser. Click **Reset** and **Auto-Play Agent** to watch the simulation!

### Docker / Online Deployment
```bash
docker build -t wildfire-env .
docker run -p 7860:7860 wildfire-env
```

### Endpoints
- `GET /tasks`: Lists Easy/Medium/Hard scenarios.
- `GET /grader`: Returns current session score (0.0-1.0).
- `POST /baseline`: Run greedy heuristic baseline.
