const API_BASE = window.location.origin;

// DOM Elements
const gridEl = document.getElementById("grid");
const windArrowEl = document.getElementById("wind-arrow");
const windTextEl = document.getElementById("wind-text");
const speedSlider = document.getElementById("speed-slider");
const speedLabel = document.getElementById("speed-label");
const gameOverlay = document.getElementById("game-overlay");
const overlayCard = document.getElementById("overlay-card");
const overlayTitle = document.getElementById("overlay-title");
const overlayDesc = document.getElementById("overlay-desc");
const overlayScore = document.getElementById("overlay-score");
const overlayStructures = document.getElementById("overlay-structures");
const overlayIconSuccess = document.getElementById("overlay-icon-success");
const overlayIconFail = document.getElementById("overlay-icon-fail");
const unitContainer = document.getElementById("unit-container");
const gridCoords = document.getElementById("grid-coords");

// Metrics
const metricStep = document.getElementById("metric-step");
const metricScore = document.getElementById("metric-score");
const metricStructures = document.getElementById("metric-structures");
const metricFire = document.getElementById("metric-fire");

// Session Info
const sessionTask = document.getElementById("session-task");
const sessionDifficulty = document.getElementById("session-difficulty");
const sessionSteps = document.getElementById("session-steps");
const sessionAvg = document.getElementById("session-avg");

// Charts
let scoreChart = null;
let fireStructChart = null;
let scoreHistory = [];
let fireHistory = [];
let structHistory = [];

// State
const windDirectionMap = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
let cells = [];
let autoPlayTimer = null;
let currentDifficulty = "medium";
let totalSteps = 0;
let scoreSum = 0;

// ── Particle System ──────────────────────────────────────────────────────────
const particleCanvas = document.getElementById("fire-particles");
const pCtx = particleCanvas.getContext("2d");
let particles = [];

function resizeParticleCanvas() {
    particleCanvas.width = window.innerWidth;
    particleCanvas.height = window.innerHeight;
}

class Particle {
    constructor() {
        this.reset();
    }

    reset() {
        this.x = Math.random() * particleCanvas.width;
        this.y = particleCanvas.height + Math.random() * 100;
        this.size = Math.random() * 3 + 1;
        this.speedY = Math.random() * 1 + 0.5;
        this.speedX = (Math.random() - 0.5) * 0.5;
        this.opacity = Math.random() * 0.5 + 0.1;
        this.color = Math.random() > 0.5 ? '239, 68, 68' : '249, 115, 22';
    }

    update() {
        this.y -= this.speedY;
        this.x += this.speedX;
        this.opacity -= 0.002;

        if (this.y < -10 || this.opacity <= 0) {
            this.reset();
        }
    }

    draw() {
        pCtx.beginPath();
        pCtx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        pCtx.fillStyle = `rgba(${this.color}, ${this.opacity})`;
        pCtx.fill();
    }
}

function initParticles() {
    resizeParticleCanvas();
    particles = [];
    for (let i = 0; i < 50; i++) {
        particles.push(new Particle());
    }
}

function animateParticles() {
    pCtx.clearRect(0, 0, particleCanvas.width, particleCanvas.height);
    particles.forEach(p => {
        p.update();
        p.draw();
    });
    requestAnimationFrame(animateParticles);
}

// ── Charts ───────────────────────────────────────────────────────────────────
function initCharts() {
    // Score Chart
    const scoreCtx = document.getElementById("scoreChart").getContext("2d");
    scoreChart = new Chart(scoreCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Score',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#64748b', font: { size: 10 } }
                },
                y: {
                    min: 0,
                    max: 1,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#64748b', font: { size: 10 } }
                }
            }
        }
    });

    // Fire vs Structures Chart
    const fireStructCtx = document.getElementById("fireStructChart").getContext("2d");
    fireStructChart = new Chart(fireStructCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Fire Cells',
                    data: [],
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderRadius: 4
                },
                {
                    label: 'Structures',
                    data: [],
                    backgroundColor: 'rgba(6, 182, 212, 0.7)',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { size: 10 } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#64748b', font: { size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#64748b', font: { size: 10 } }
                }
            }
        }
    });
}

function updateCharts(step, fireCount, structCount, score) {
    scoreHistory.push(score);
    fireHistory.push(fireCount);
    structHistory.push(structCount);

    // Keep last 20 steps
    if (scoreHistory.length > 20) {
        scoreHistory.shift();
        fireHistory.shift();
        structHistory.shift();
    }

    const labels = scoreHistory.map((_, i) => i + 1);

    scoreChart.data.labels = labels;
    scoreChart.data.datasets[0].data = scoreHistory;
    scoreChart.update('none');

    fireStructChart.data.labels = labels;
    fireStructChart.data.datasets[0].data = fireHistory;
    fireStructChart.data.datasets[1].data = structHistory;
    fireStructChart.update('none');
}

// ── Init Grid ────────────────────────────────────────────────────────────────
function initGrid() {
    gridEl.innerHTML = "";
    cells = [];
    for (let r = 0; r < 20; r++) {
        for (let c = 0; c < 20; c++) {
            const cell = document.createElement("div");
            cell.className = "cell";
            cell.dataset.row = r;
            cell.dataset.col = c;

            // Hover tooltip
            cell.addEventListener("mouseenter", (e) => {
                gridCoords.textContent = `${r},${c}`;
            });

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

            // Reset classes
            cell.className = "cell";
            cell.innerHTML = "";

            if (fire > 0.1) {
                const intensity = Math.min(fire, 1);
                const r_val = Math.floor(180 + intensity * 75);
                const g_val = Math.floor(40 + intensity * 30);
                const b_val = Math.floor(20);
                cell.style.backgroundColor = `rgb(${r_val}, ${g_val}, ${b_val})`;
                cell.classList.add("cell-fire");
                cell.innerHTML = "🔥";
                fireCount++;
            } else if (moisture > 0.2) {
                cell.style.backgroundColor = `rgba(30, 80, 180, ${moisture})`;
                cell.classList.add("cell-water");
            } else if (fuel > 0.1) {
                const g = Math.floor(80 + fuel * 120);
                cell.style.backgroundColor = `rgb(18, ${g}, 35)`;
                cell.innerHTML = `<span style="opacity:0.4;font-size:clamp(7px,0.8vw,14px)">🌲</span>`;
            } else {
                cell.style.backgroundColor = "#0f172a";
            }

            if (struct === 1) {
                cell.innerHTML = `<span style="filter:drop-shadow(0 0 6px rgba(6,182,212,0.8))">🏠</span>`;
                cell.classList.add("cell-structure");
                structCount++;
            }
        }
    }

    // Agents
    if (obs.units) {
        obs.units.forEach((unit) => {
            const [ur, uc] = unit.pos;
            const cell = cells[ur * 20 + uc];
            const emoji = unit.type === "tanker" ? "✈️" : "🧑‍";
            cell.innerHTML = `<span style="font-size:clamp(10px,1.2vw,18px);filter:drop-shadow(0 0 4px rgba(255,255,255,0.6))">${emoji}</span>`;
            cell.classList.add("cell-unit");
        });
    }

    return { fireCount, structCount };
}

// ── Update Dashboard ─────────────────────────────────────────────────────────
function updateDashboard(payloadObs, counts) {
    const obs = payloadObs.observation;

    const step = obs.info ? obs.info.step : 0;
    const reward = payloadObs.reward || 0;
    const score = reward > 0.01 ? reward : 0.5;

    metricStep.textContent = step;
    metricScore.textContent = score.toFixed(2);
    metricStructures.textContent = counts.structCount;
    metricFire.textContent = counts.fireCount;

    totalSteps = step;
    scoreSum += score;
    sessionSteps.textContent = totalSteps;
    sessionAvg.textContent = (scoreSum / Math.max(totalSteps, 1)).toFixed(2);

    // Wind
    if (obs.wind_dir !== undefined) {
        const windDeg = obs.wind_dir * 45;
        windArrowEl.style.transform = `rotate(${windDeg}deg)`;
        windTextEl.textContent = `${windDirectionMap[obs.wind_dir]} ${(obs.wind_speed || 1.0).toFixed(1)}x`;
    }

    // Units
    unitContainer.innerHTML = "";
    if (obs.units) {
        obs.units.forEach((unit) => {
            const isTanker = unit.type === "tanker";
            const pct = Math.max(0, Math.min(100, (unit.resource / unit.max_resource) * 100));
            const emoji = isTanker ? "✈️" : "🧑‍";
            const label = isTanker ? "Air Tanker" : "Ground Crew";
            const barColor = isTanker ? "bg-blue-500" : "bg-emerald-500";
            const barGlow = isTanker ? "shadow-blue-500/50" : "shadow-emerald-500/50";

            unitContainer.innerHTML += `
                <div class="bg-dark-900 rounded-lg p-3 border border-white/5 hover:border-white/10 transition-colors">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-xs font-semibold text-slate-300 flex items-center gap-2">
                            ${emoji} ${label}
                        </span>
                        <span class="text-[10px] font-mono text-slate-500 bg-dark-800 px-2 py-0.5 rounded">[${unit.pos[0]},${unit.pos[1]}]</span>
                    </div>
                    <div class="w-full bg-dark-800 rounded-full h-2 overflow-hidden">
                        <div class="${barColor} h-2 rounded-full transition-all duration-300 shadow-lg ${barGlow}" style="width:${pct}%"></div>
                    </div>
                    <div class="flex justify-between mt-1">
                        <span class="text-[10px] text-slate-500">Resource</span>
                        <span class="text-[10px] text-slate-400 font-mono">${pct.toFixed(0)}%</span>
                    </div>
                </div>`;
        });
    }

    // Charts
    updateCharts(step, counts.fireCount, counts.structCount, score);

    // Done
    if (payloadObs.done) {
        showOverlay(counts);
        clearInterval(autoPlayTimer);
        autoPlayTimer = null;
        const btn = document.getElementById("btn-auto");
        if (btn) btn.innerHTML = '<i class="fa-solid fa-play text-emerald-400 mr-2"></i> <span>Auto-Play</span>';
    }
}

// ── Game Over Overlay ────────────────────────────────────────────────────────
function showOverlay(counts) {
    const fireCount = counts.fireCount;
    const structCount = counts.structCount;
    const initialStruct = parseInt(metricStructures.dataset.initial || structCount);

    gameOverlay.classList.remove("opacity-0", "pointer-events-none");
    overlayCard.style.transform = "scale(1)";

    if (fireCount === 0) {
        overlayTitle.textContent = "🎉 Mission Complete!";
        overlayDesc.textContent = "Fire Contained Successfully";
        overlayIconSuccess.classList.remove("hidden");
        overlayIconFail.classList.add("hidden");
    } else if (structCount === 0) {
        overlayTitle.textContent = "💀 Total Loss";
        overlayDesc.textContent = "All Structures Destroyed";
        overlayIconSuccess.classList.add("hidden");
        overlayIconFail.classList.remove("hidden");
    } else {
        overlayTitle.textContent = "⚠️ Partial Success";
        overlayDesc.textContent = `${structCount} structures survived`;
        overlayIconSuccess.classList.add("hidden");
        overlayIconFail.classList.add("hidden");
    }

    const finalScore = parseFloat(metricScore.textContent);
    overlayScore.textContent = finalScore.toFixed(2);
    overlayStructures.textContent = `${structCount}`;
}

// ── API Calls ────────────────────────────────────────────────────────────────
async function resetEnv() {
    try {
        const difficulty = document.getElementById("select-difficulty").value;
        currentDifficulty = difficulty;

        const res = await fetch(`${API_BASE}/reset`, { method: "POST" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const obs = await res.json();

        // Reset state
        scoreHistory = [];
        fireHistory = [];
        structHistory = [];
        totalSteps = 0;
        scoreSum = 0;
        sessionTask.textContent = difficulty;
        sessionDifficulty.textContent = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
        sessionSteps.textContent = "0";
        sessionAvg.textContent = "0.00";

        const counts = updateGrid(obs);
        updateDashboard(obs, counts);

        // Store initial structures
        metricStructures.dataset.initial = counts.structCount;

        // Reset charts
        if (scoreChart) {
            scoreChart.data.labels = [];
            scoreChart.data.datasets[0].data = [];
            scoreChart.update();
        }
        if (fireStructChart) {
            fireStructChart.data.labels = [];
            fireStructChart.data.datasets[0].data = [];
            fireStructChart.data.datasets[1].data = [];
            fireStructChart.update();
        }
    } catch (e) {
        console.error("Reset FAILED:", e);
        metricFire.textContent = "ERR";
        metricStructures.textContent = "ERR";
    }
}

async function stepBaseline() {
    let actions = null;
    try {
        const actRes = await fetch(`${API_BASE}/act`, { method: "POST" });
        actions = (await actRes.json()).actions;
    } catch (e) {
        console.error("Act failed:", e);
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
        console.error("Step failed:", e);
        stopAutoPlay();
    }
}

function stopAutoPlay() {
    clearInterval(autoPlayTimer);
    autoPlayTimer = null;
    const btn = document.getElementById("btn-auto");
    if (btn) btn.innerHTML = '<i class="fa-solid fa-play text-emerald-400 mr-2"></i> <span>Auto-Play</span>';
}

// ── Event Listeners ──────────────────────────────────────────────────────────
document.getElementById("btn-reset").addEventListener("click", resetEnv);
document.getElementById("btn-overlay-reset").addEventListener("click", resetEnv);
document.getElementById("btn-step").addEventListener("click", stepBaseline);

// Speed Slider
speedSlider.addEventListener("input", (e) => {
    const speed = parseFloat(e.target.value);
    speedLabel.textContent = `${speed.toFixed(1)}x`;

    if (autoPlayTimer) {
        clearInterval(autoPlayTimer);
        autoPlayTimer = setInterval(stepBaseline, 1000 / speed);
    }
});

// Auto-Play
document.getElementById("btn-auto").addEventListener("click", () => {
    if (autoPlayTimer) {
        stopAutoPlay();
    } else {
        const speed = parseFloat(speedSlider.value);
        autoPlayTimer = setInterval(stepBaseline, 1000 / speed);
        const btn = document.getElementById("btn-auto");
        btn.innerHTML = '<i class="fa-solid fa-stop text-red-400 mr-2"></i> <span>Stop</span>';
    }
});

// Difficulty Change
document.getElementById("select-difficulty").addEventListener("change", () => {
    resetEnv();
});

// Window Resize
window.addEventListener("resize", () => {
    resizeParticleCanvas();
});

// ── Boot ─────────────────────────────────────────────────────────────────────
function init() {
    initGrid();
    initParticles();
    animateParticles();
    initCharts();
    resetEnv();
}

init();
