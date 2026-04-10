const API_BASE = window.location.origin;

const gridEl = document.getElementById("grid");
const windTextEl = document.getElementById("wind-text");

const metricStep = document.getElementById("metric-step");
const metricReward = document.getElementById("metric-reward");
const metricStructures = document.getElementById("metric-structures");
const metricFire = document.getElementById("metric-fire");

const gameOverlay = document.getElementById("game-overlay");
const overlayTitle = document.getElementById("overlay-title");
const overlayDesc = document.getElementById("overlay-desc");
const unitContainer = document.getElementById("unit-container");

const windDirectionMap = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];

let cells = [];

// ── Init Grid ────────────────────────────────────────────────────────────────
function initGrid() {
    gridEl.innerHTML = "";
    cells = [];
    for (let r = 0; r < 20; r++) {
        for (let c = 0; c < 20; c++) {
            const cell = document.createElement("div");
            cell.className = "cell";
            gridEl.appendChild(cell);
            cells.push(cell);
        }
    }
}

// ── Update Grid ──────────────────────────────────────────────────────────────
function updateGrid(payloadObs) {
    let fireCount = 0;
    let structCount = 0;
    const obs = payloadObs.observation;

    for (let r = 0; r < 20; r++) {
        for (let c = 0; c < 20; c++) {
            const idx = r * 20 + c;
            const cell = cells[idx];
            const fire = obs.fire_grid[r][c];
            const fuel = obs.fuel_grid[r][c];
            const moisture = obs.moisture_grid[r][c];
            const struct = obs.structure_grid[r][c];

            cell.className = "cell";
            cell.innerHTML = "";

            if (fire > 0.1) {
                cell.style.backgroundColor = "rgb(220, 60, 40)";
                cell.classList.add("cell-fire");
                cell.innerHTML = "🔥";
                fireCount++;
            } else if (moisture > 0.2) {
                cell.style.backgroundColor = "rgb(30, 80, 180)";
            } else if (fuel > 0.1) {
                const g = Math.floor(80 + fuel * 120);
                cell.style.backgroundColor = `rgb(18, ${g}, 35)`;
                cell.innerHTML = `<span style="opacity:0.35;font-size:clamp(7px,0.8vw,14px)">🌲</span>`;
            } else {
                cell.style.backgroundColor = "#151a2e";
            }

            if (struct === 1) {
                cell.innerHTML = `<span style="filter:drop-shadow(0 0 4px rgba(255,255,255,0.5))">🏠</span>`;
                structCount++;
            }
        }
    }

    // Agents
    if (obs.units) {
        obs.units.forEach((unit) => {
            const [ur, uc] = unit.pos;
            const cell = cells[ur * 20 + uc];
            const emoji = unit.type === "tanker" ? "✈️" : "🧑‍🚒";
            cell.innerHTML = `<span style="font-size:clamp(10px,1.2vw,18px)">${emoji}</span>`;
        });
    }

    return { fireCount, structCount };
}

// ── Update Metrics ───────────────────────────────────────────────────────────
function updateDashboard(payloadObs, counts) {
    const obs = payloadObs.observation;

    metricStep.textContent = obs.info ? obs.info.step : 0;
    metricReward.textContent = payloadObs.reward.toFixed(2);
    metricStructures.textContent = counts.structCount;
    metricFire.textContent = counts.fireCount;

    if (obs.wind_dir !== undefined) {
        windTextEl.textContent = `${windDirectionMap[obs.wind_dir]} ${(obs.wind_speed || 1.0).toFixed(1)}x`;
    }

    // Units
    unitContainer.innerHTML = "";
    if (obs.units) {
        obs.units.forEach((unit) => {
            const isTanker = unit.type === "tanker";
            const pct = (unit.resource / unit.max_resource) * 100;
            const emoji = isTanker ? "✈️" : "🧑‍";
            const label = isTanker ? "Air Tanker" : "Ground Crew";
            const barColor = isTanker ? "bg-blue-500" : "bg-emerald-500";

            unitContainer.innerHTML += `
                <div class="bg-white/[0.03] rounded-lg p-2.5">
                    <div class="flex justify-between items-center mb-1.5">
                        <span class="text-xs font-medium text-slate-300">${emoji} ${label}</span>
                        <span class="text-[10px] font-mono text-slate-500">[${unit.pos[0]},${unit.pos[1]}]</span>
                    </div>
                    <div class="w-full bg-white/5 rounded-full h-1">
                        <div class="${barColor} h-1 rounded-full transition-all" style="width:${pct}%"></div>
                    </div>
                </div>`;
        });
    }

    // Done
    if (payloadObs.done) {
        gameOverlay.classList.remove("opacity-0", "pointer-events-none");
        if (counts.fireCount === 0) {
            overlayTitle.textContent = "Mission Complete";
            overlayDesc.textContent = "Fire Contained Successfully";
        } else {
            overlayTitle.textContent = "Total Loss";
            overlayDesc.textContent = "All Structures Destroyed";
        }
        clearInterval(autoPlayTimer);
        document.getElementById("btn-auto").innerHTML = '<i class="fa-solid fa-play mr-1"></i> Auto-Play';
    } else {
        gameOverlay.classList.add("opacity-0", "pointer-events-none");
    }
}

// ── API Calls ────────────────────────────────────────────────────────────────
async function resetEnv() {
    try {
        console.log("Calling /reset at:", `${API_BASE}/reset`);
        const res = await fetch(`${API_BASE}/reset`, { method: "POST" });
        console.log("Response status:", res.status);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const obs = await res.json();
        console.log("Reset OK, structures:", obs.observation.structure_grid.flat().reduce((a, b) => a + b, 0));
        const counts = updateGrid(obs);
        updateDashboard(obs, counts);
    } catch (e) {
        console.error("Reset FAILED:", e);
        document.getElementById("metric-fire").textContent = "ERR";
        document.getElementById("metric-structures").textContent = "ERR";
    }
}

async function stepBaseline() {
    let actions = null;
    try {
        const actRes = await fetch(`${API_BASE}/act`, { method: "POST" });
        actions = (await actRes.json()).actions;
    } catch (e) {
        console.error("Act failed, stopping auto-play:", e);
        stopAutoPlay();
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/step`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: { actions } })
        });
        const obs = await res.json();
        const counts = updateGrid(obs);
        updateDashboard(obs, counts);

        if (obs.done) stopAutoPlay();
    } catch (e) {
        console.error("Step failed, stopping auto-play:", e);
        stopAutoPlay();
    }
}

function stopAutoPlay() {
    clearInterval(autoPlayTimer);
    autoPlayTimer = null;
    const btn = document.getElementById("btn-auto");
    if (btn) btn.innerHTML = '<i class="fa-solid fa-play mr-1"></i> Auto-Play';
}

// ── Listeners ────────────────────────────────────────────────────────────────
document.getElementById("btn-reset").addEventListener("click", resetEnv);
document.getElementById("btn-overlay-reset").addEventListener("click", resetEnv);
document.getElementById("btn-step").addEventListener("click", stepBaseline);

let autoPlayTimer = null;
document.getElementById("btn-auto").addEventListener("click", () => {
    if (autoPlayTimer) {
        stopAutoPlay();
    } else {
        autoPlayTimer = setInterval(stepBaseline, 1000);
        document.getElementById("btn-auto").innerHTML = '<i class="fa-solid fa-stop mr-1"></i> Stop';
    }
});

// ── Boot ─────────────────────────────────────────────────────────────────────
initGrid();
resetEnv();
