const API_BASE = "http://localhost:8000";

const gridEl = document.getElementById("grid");
const windTextEl = document.getElementById("wind-text");
const windIcon = document.querySelector("#wind-indicator i");
const unitContainer = document.getElementById("unit-container");

// Metrics
const metricStep = document.getElementById("metric-step");
const metricReward = document.getElementById("metric-reward");
const metricStructures = document.getElementById("metric-structures");
const metricFire = document.getElementById("metric-fire");

// Overlay
const gameOverlay = document.getElementById("game-overlay");
const overlayTitle = document.getElementById("overlay-title");
const overlayDesc = document.getElementById("overlay-desc");

const windDirectionMap = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
const windRotationMap = [0, 45, 90, 135, 180, 225, 270, 315];

let cells = [];
let epsId = null;

// Initialize 20x20 Grid DOM
function initGrid() {
    gridEl.innerHTML = "";
    cells = [];
    for (let r = 0; r < 20; r++) {
        let rowCells = [];
        for (let c = 0; c < 20; c++) {
            const cell = document.createElement("div");
            cell.className = "cell";
            gridEl.appendChild(cell);
            rowCells.push(cell);
        }
        cells.push(rowCells);
    }
}

// Update Grid Visuals
function updateGrid(payloadObs) {
    let fireCount = 0;
    let structCount = 0;
    
    // The inner observation object
    const obs = payloadObs.observation;

    for (let r = 0; r < 20; r++) {
        for (let c = 0; c < 20; c++) {
            const fire = obs.fire_grid[r][c];
            const fuel = obs.fuel_grid[r][c];
            const moisture = obs.moisture_grid[r][c];
            const struct = obs.structure_grid[r][c];
            
            const cell = cells[r][c];
            cell.innerHTML = "";
            cell.classList.remove("cell-fire");
            
            // Premium Terrain Color Mappings
            let color = "#1e293b"; // Base Slate-800 for empty dirt/firebreaks
            
            if (fire > 0.1) {
                color = `rgb(239, 68, 68)`; // Fire Red
                cell.classList.add("cell-fire");
                cell.innerHTML = `<span class="absolute inset-0 flex items-center justify-center text-[clamp(10px,1.5vw,22px)] drop-shadow-md">🔥</span>`;
                fireCount++;
            } else if (moisture > 0.2) {
                color = `rgb(59, 130, 246)`; // Water Blue
            } else if (fuel > 0.1) {
                // Natural forest green scaling
                const greenValue = Math.floor(60 + (fuel * 140)); // 60 to 200
                color = `rgb(20, ${greenValue}, 40)`;
            }
            
            cell.style.backgroundColor = color;
            
            if (struct === 1) {
                cell.innerHTML += `<span class="absolute inset-0 flex items-center justify-center text-[clamp(10px,1.5vw,20px)] drop-shadow-[0_0_5px_rgba(255,255,255,0.8)] z-10">🏘️</span>`;
                structCount++;
            }
        }
    }
    
    // Draw Agents
    if (obs.units) {
        obs.units.forEach((unit, idx) => {
            const [ur, uc] = unit.pos;
            const cell = cells[ur][uc];
            
            const isTanker = unit.type === "tanker";
            const emoji = isTanker ? "✈️" : "🧑‍🚒";
            
            cell.innerHTML += `<span class="absolute inset-0 flex items-center justify-center text-[clamp(12px,2vw,24px)] drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] z-20 transition-all">${emoji}</span>`;
        });
    }

    return { fireCount, structCount };
}

// Update Side Panel
function updateDashboard(payloadObs, counts) {
    const obs = payloadObs.observation;
    
    metricStep.innerText = obs.info ? obs.info.step : 0;
    metricReward.innerText = payloadObs.reward.toFixed(2);
    metricStructures.innerText = counts.structCount;
    metricFire.innerText = counts.fireCount;
    
    // Wind
    if (obs.wind_dir !== undefined) {
        windTextEl.innerText = `${windDirectionMap[obs.wind_dir]} ${(obs.wind_speed || 1.0).toFixed(1)}x`;
        windIcon.style.transform = `rotate(${windRotationMap[obs.wind_dir]}deg)`;
    }

    // Units
    unitContainer.innerHTML = "";
    if (obs.units) {
        obs.units.forEach((unit, idx) => {
            const isTanker = unit.type === "tanker";
            const pct = (unit.resource / unit.max_resource) * 100;
            const emoji = isTanker ? "✈️" : "🧑‍🚒";
            const title = isTanker ? "Air Tanker Alpha" : `Ground Crew ${idx}`;
            
            unitContainer.innerHTML += `
                <div class="bg-slate-900/50 rounded-lg p-3 border border-slate-700/50">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-sm font-semibold text-slate-200">${emoji} ${title}</span>
                        <span class="text-xs font-mono text-slate-400">[${unit.pos[0]}, ${unit.pos[1]}]</span>
                    </div>
                    <div class="w-full bg-slate-800 rounded-full h-1.5">
                        <div class="bg-gradient-to-r ${isTanker ? 'from-blue-600 to-blue-400' : 'from-emerald-600 to-emerald-400'} h-1.5 rounded-full transition-all duration-300" style="width: ${pct}%"></div>
                    </div>
                    <div class="text-[10px] text-right mt-1 text-slate-500 uppercase">${unit.resource.toFixed(1)} / ${unit.max_resource}</div>
                </div>
            `;
        });
    }

    // Done state
    if (payloadObs.done) {
        gameOverlay.classList.remove("opacity-0", "pointer-events-none");
        if (counts.fireCount === 0) {
            overlayTitle.innerText = "Mission Complete";
            overlayDesc.innerText = "Fire Contained Successfully";
            overlayTitle.className = "font-outfit text-4xl font-bold text-emerald-400 mb-2 shadow-sm drop-shadow-[0_0_15px_rgba(52,211,153,0.5)]";
        } else {
            overlayTitle.innerText = "Total Loss";
            overlayDesc.innerText = "Structures Destroyed";
            overlayTitle.className = "font-outfit text-4xl font-bold text-rose-500 mb-2 shadow-sm drop-shadow-[0_0_15px_rgba(225,29,72,0.5)]";
        }
        clearInterval(autoPlayTimer);
        document.getElementById("btn-auto").innerHTML = `<i class="fa-solid fa-play"></i> Auto-Play Agent`;
    } else {
        gameOverlay.classList.add("opacity-0", "pointer-events-none");
    }
}

// API Calls
async function resetEnv() {
    // We parse difficulty to openenv format if supported, or via API logic
    // We are hitting the standard OpenEnv POST /reset. 
    // Wait, the FastAPI server exposes POST /reset without params in standard openenv.
    // Let's just call it.
    try {
        const res = await fetch(`${API_BASE}/reset`, { method: "POST" });
        const obs = await res.json();
        const counts = updateGrid(obs);
        updateDashboard(obs, counts);
    } catch (e) {
        console.error("Failed to reset", e);
    }
}

async function stepBaseline() {
    const diff = document.getElementById("select-difficulty").value;
    // We will cheat slightly for the frontend visualization by calling our custom /baseline endpoint,
    // actually wait, /baseline in app.py runs a full while loop of steps and returns summary. 
    // If we want a VISUAL step-by-step from the frontend, we should fetch action from baseline, and post to /step.
    // But since OpenEnv architecture puts the agent on the client side typically, we will just simulate random actions if we don't have the agent logic in JS.
    // OR we can make a new endpoint in python to give us the next baseline action, then call /step.
    // To keep it simple, we will port the baseline logic here in JS!
    
    // For now, let's just use random actions if we don't implement the full heuristic in JS.
    // Actually, let's just make the JS agent move randomly for the demo, since the real agent runs server-side or via Python EnvClient.
    
    const actionPayload = {
        "action": {
            "actions": [
                { "move": Math.floor(Math.random() * 9), "act": Math.random() > 0.5 },
                { "move": Math.floor(Math.random() * 9), "act": Math.random() > 0.5 },
                { "move": Math.floor(Math.random() * 9), "act": Math.random() > 0.5 }
            ]
        }
    };

    try {
        const res = await fetch(`${API_BASE}/step`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(actionPayload)
        });
        const obs = await res.json();
        const counts = updateGrid(obs);
        updateDashboard(obs, counts);
    } catch (e) {
        console.error("Failed to step", e);
    }
}


// Listeners
document.getElementById("btn-reset").addEventListener("click", resetEnv);
document.getElementById("btn-overlay-reset").addEventListener("click", resetEnv);
document.getElementById("btn-step").addEventListener("click", stepBaseline);

let autoPlayTimer = null;
document.getElementById("btn-auto").addEventListener("click", (e) => {
    const btn = e.currentTarget;
    if (autoPlayTimer) {
        clearInterval(autoPlayTimer);
        autoPlayTimer = null;
        btn.innerHTML = `<i class="fa-solid fa-play"></i> Auto-Play Agent`;
    } else {
        autoPlayTimer = setInterval(stepBaseline, 200); // 5 FPS
        btn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Auto-Play`;
    }
});

// Boot
initGrid();
resetEnv();
