const map = document.getElementById("map");
const mctx = map.getContext("2d");

const spectrum = document.getElementById("spectrum");
const sctx = spectrum.getContext("2d");

const devicesDiv = document.getElementById("devices");
const alertsDiv = document.getElementById("alerts");
const packetsDiv = document.getElementById("packets");
const capturesDiv = document.getElementById("captures");

let tick = 0;
let packets = [];
let alerts = [];
let captures = [];
let waterfallRows = [];

function resize() {
  map.width = map.clientWidth;
  map.height = map.clientHeight;
  spectrum.width = spectrum.clientWidth;
  spectrum.height = spectrum.clientHeight;
  waterfallRows = [];
}

window.addEventListener("resize", resize);
resize();

const towers = [
  { id: "TOWER-A", x: 0.22, y: 0.35, legit: true },
  { id: "TOWER-B", x: 0.74, y: 0.42, legit: true },
  { id: "ROGUE-01", x: 0.50, y: 0.68, legit: false }
];

const devices = Array.from({ length: 14 }, (_, i) => ({
  id: "UE-" + String(i + 1).padStart(3, "0"),
  imsi: "310260" + Math.floor(100000000 + Math.random() * 899999999),
  tmsi: "0x" + Math.floor(Math.random() * 0xffffffff).toString(16).toUpperCase(),
  x: Math.random() * 0.9 + 0.05,
  y: Math.random() * 0.9 + 0.05,
  dx: (Math.random() - 0.5) * 0.006,
  dy: (Math.random() - 0.5) * 0.006,
  tower: "TOWER-A",
  rssi: -70,
  captured: false
}));

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function strongestTower(device) {
  let best = towers[0];
  let bestScore = Infinity;

  for (const tower of towers) {
    let score = distance(device, tower);
    if (!tower.legit) score -= 0.12;

    if (score < bestScore) {
      best = tower;
      bestScore = score;
    }
  }

  return best;
}

function updateDevices() {
  for (const d of devices) {
    d.x += d.dx;
    d.y += d.dy;

    if (Math.random() < 0.01) {
      d.dx += (Math.random() - 0.5) * 0.002;
      d.dy += (Math.random() - 0.5) * 0.002;
    }

    d.dx = Math.max(-0.007, Math.min(0.007, d.dx));
    d.dy = Math.max(-0.007, Math.min(0.007, d.dy));

    if (d.x < 0.03 || d.x > 0.97) d.dx *= -1;
    if (d.y < 0.03 || d.y > 0.97) d.dy *= -1;

    d.x = Math.max(0.03, Math.min(0.97, d.x));
    d.y = Math.max(0.03, Math.min(0.97, d.y));

    const oldTower = d.tower;
    const best = strongestTower(d);

    d.tower = best.id;
    d.rssi = Math.round(-45 - distance(d, best) * 70 + Math.random() * 4);

    if (oldTower !== d.tower) {
      addPacket(`${d.id} HANDOFF ${oldTower} -> ${d.tower}`);

      if (!best.legit) {
        addAlert(`Suspicious attach: ${d.id} selected rogue tower ${best.id}`);
      }
    }

    if (!best.legit && !d.captured && Math.random() < 0.04) {
      captureIMSI(d);
    }

    if (best.legit && Math.random() < 0.025) {
      addPacket(`${d.id} ATTACH ACCEPT ${d.tower} TMSI=${d.tmsi}`);
    }
  }
}

function captureIMSI(device) {
  device.captured = true;

  const record = {
    time: new Date().toLocaleTimeString(),
    ue: device.id,
    imsi: device.imsi,
    tmsi: device.tmsi,
    rssi: device.rssi,
    tower: device.tower
  };

  captures.unshift(record);
  captures = captures.slice(0, 12);

  addPacket(`${device.id} RRC CONNECTION REQUEST -> ${device.tower}`);
  addPacket(`${device.tower} IDENTITY REQUEST -> ${device.id}`);
  addPacket(`CAPTURED IMSI ${device.imsi} FROM ${device.id}`);
  addAlert(`IMSI captured from ${device.id} via ${device.tower}`);

  renderCaptures();
}

function drawMap() {
  mctx.clearRect(0, 0, map.width, map.height);
  mctx.fillStyle = "#02060a";
  mctx.fillRect(0, 0, map.width, map.height);

  mctx.strokeStyle = "#0d2434";
  mctx.lineWidth = 1;

  for (let x = 0; x < map.width; x += 40) {
    mctx.beginPath();
    mctx.moveTo(x, 0);
    mctx.lineTo(x, map.height);
    mctx.stroke();
  }

  for (let y = 0; y < map.height; y += 40) {
    mctx.beginPath();
    mctx.moveTo(0, y);
    mctx.lineTo(map.width, y);
    mctx.stroke();
  }

  for (const t of towers) {
    const x = t.x * map.width;
    const y = t.y * map.height;
    const radius = (t.legit ? 80 : 110) + Math.sin(tick / 14) * 3;

    mctx.beginPath();
    mctx.arc(x, y, radius, 0, Math.PI * 2);
    mctx.strokeStyle = t.legit
      ? "rgba(0,217,255,0.18)"
      : "rgba(255,77,109,0.28)";
    mctx.stroke();

    mctx.beginPath();
    mctx.arc(x, y, 8, 0, Math.PI * 2);
    mctx.fillStyle = t.legit ? "#00d9ff" : "#ff4d6d";
    mctx.fill();

    mctx.fillStyle = "#e8f6ff";
    mctx.font = "12px Arial";
    mctx.fillText(t.id, x + 12, y - 10);
  }

  for (const d of devices) {
    const x = d.x * map.width;
    const y = d.y * map.height;
    const rogue = d.tower.startsWith("ROGUE");
    const tower = towers.find(t => t.id === d.tower);

    if (tower) {
      mctx.beginPath();
      mctx.moveTo(x, y);
      mctx.lineTo(tower.x * map.width, tower.y * map.height);
      mctx.strokeStyle = rogue
        ? "rgba(255,77,109,0.25)"
        : "rgba(0,255,136,0.12)";
      mctx.stroke();
    }

    mctx.beginPath();
    mctx.arc(x, y, d.captured ? 7 : rogue ? 6 : 5, 0, Math.PI * 2);
    mctx.fillStyle = d.captured ? "#ff4d6d" : rogue ? "#ffb703" : "#00ff88";
    mctx.fill();

    if (d.captured) {
      mctx.beginPath();
      mctx.arc(x, y, 12 + Math.sin(tick / 6) * 3, 0, Math.PI * 2);
      mctx.strokeStyle = "rgba(255,77,109,0.65)";
      mctx.stroke();
    }

    mctx.fillStyle = "#93a9b7";
    mctx.font = "11px Arial";
    mctx.fillText(d.id, x + 7, y + 4);
  }
}

function powerToColor(power, rogueZone) {
  let r = 0;
  let g = 18;
  let b = 45;

  if (power > 22) {
    g = 30 + power * 0.7;
    b = 70 + power * 1.4;
  }

  if (power > 48) {
    r = 20 + (power - 48) * 1.2;
    g = 95 + (power - 48) * 1.4;
    b = 150 + (power - 48) * 1.2;
  }

  if (power > 82) {
    r = 150 + (power - 82) * 1.1;
    g = 210 + (power - 82) * 0.7;
    b = 245;
  }

  if (rogueZone && power > 45) {
    r += 45;
    g -= 20;
  }

  r = Math.max(0, Math.min(255, r));
  g = Math.max(0, Math.min(255, g));
  b = Math.max(0, Math.min(255, b));

  return `rgb(${r},${g},${b})`;
}

function makeSpectrumRow() {
  const w = spectrum.width;
  const row = [];

  const ch1Center = w * 0.24 + Math.sin(tick / 110) * 5;
  const ch2Center = w * 0.55 + Math.cos(tick / 130) * 5;
  const rogueCenter = w * 0.74 + Math.sin(tick / 45) * 4;

  for (let x = 0; x < w; x++) {
    let power = 10 + Math.random() * 16;

    const ch1 = Math.abs(x - ch1Center);
    const ch2 = Math.abs(x - ch2Center);
    const rogue = Math.abs(x - rogueCenter);

    if (ch1 < 30) power += (30 - ch1) * 1.45;
    if (ch2 < 34) power += (34 - ch2) * 1.35;
    if (rogue < 25) power += (25 - rogue) * 2.25;

    if (tick % 80 < 20) {
      const burstCenter = w * 0.38 + Math.sin(tick / 16) * 18;
      const burst = Math.abs(x - burstCenter);
      if (burst < 16) power += (16 - burst) * 2.1;
    }

    if (Math.random() < 0.002) power += 40;

    row.push({
      power: Math.min(115, power),
      rogue: rogue < 28
    });
  }

  return row;
}

function drawSpectrum() {
  const w = spectrum.width;
  const h = spectrum.height;
  if (w <= 0 || h <= 0) return;

  waterfallRows.unshift(makeSpectrumRow());

  while (waterfallRows.length > h) {
    waterfallRows.pop();
  }

  sctx.fillStyle = "#02060a";
  sctx.fillRect(0, 0, w, h);

  for (let y = 0; y < waterfallRows.length; y++) {
    const row = waterfallRows[y];

    for (let x = 0; x < row.length; x++) {
      sctx.fillStyle = powerToColor(row[x].power, row[x].rogue);
      sctx.fillRect(x, y, 1, 1);
    }
  }

  sctx.fillStyle = "rgba(0,0,0,0.68)";
  sctx.fillRect(0, 0, w, 24);

  sctx.strokeStyle = "rgba(255,255,255,0.12)";
  sctx.lineWidth = 1;

  for (let i = 0; i < 9; i++) {
    const x = (w / 8) * i;
    sctx.beginPath();
    sctx.moveTo(x, 0);
    sctx.lineTo(x, 24);
    sctx.stroke();
  }

  sctx.fillStyle = "#b6d6e2";
  sctx.font = "11px Arial";
  sctx.fillText("700 MHz", 8, 16);
  sctx.fillText("LTE CH-A", w * 0.21, 16);
  sctx.fillText("LTE CH-B", w * 0.52, 16);

  sctx.fillStyle = "#ff4d6d";
  sctx.fillText("ROGUE", w * 0.71, 16);
}

function renderDevices() {
  devicesDiv.innerHTML = devices.slice(0, 10).map(d => {
    const rogue = d.tower.startsWith("ROGUE");

    return `
      <div class="device-card">
        <strong>${d.id}</strong><br>
        IMSI: ${d.imsi}<br>
        TMSI: ${d.tmsi}<br>
        Tower: <span class="${rogue ? "bad" : "good"}">${d.tower}</span><br>
        RSSI: ${d.rssi} dBm<br>
        Status: ${d.captured ? '<span class="bad">IMSI CAPTURED</span>' : '<span class="good">normal</span>'}
      </div>
    `;
  }).join("");
}

function renderCaptures() {
  if (!capturesDiv) return;

  capturesDiv.innerHTML = captures.length
    ? captures.map(c => `
      <div class="device-card">
        <strong>${c.ue}</strong><br>
        IMSI: <span class="bad">${c.imsi}</span><br>
        TMSI: ${c.tmsi}<br>
        Tower: ${c.tower}<br>
        RSSI: ${c.rssi} dBm<br>
        Time: ${c.time}
      </div>
    `).join("")
    : `<div class="device-card">No IMSIs captured yet.</div>`;
}

function addPacket(text) {
  const stamp = new Date().toLocaleTimeString();
  packets.unshift(`[${stamp}] ${text}`);
  packets = packets.slice(0, 18);
}

function addAlert(text) {
  const stamp = new Date().toLocaleTimeString();
  alerts.unshift(`[${stamp}] ${text}`);
  alerts = alerts.slice(0, 8);
}

function renderPackets() {
  packetsDiv.innerHTML = packets.map(p => `<div class="packet">${p}</div>`).join("");
}

function renderAlerts() {
  alertsDiv.innerHTML = alerts.length
    ? alerts.map(a => `<div class="alert-card">${a}</div>`).join("")
    : `<div class="device-card">No active alerts.</div>`;
}

function loop() {
  tick++;

  updateDevices();
  drawMap();
  drawSpectrum();

  if (tick % 6 === 0) renderDevices();
  if (tick % 4 === 0) renderPackets();

  renderAlerts();
  renderCaptures();

  requestAnimationFrame(loop);
}

addAlert("Rogue tower monitor initialized");
addPacket("LTE control channel monitor started");
addPacket("Scanning MCC/MNC 310-260 simulation");

renderDevices();
renderPackets();
renderAlerts();
renderCaptures();

loop();

setInterval(() => {
  fetch("/heartbeat", {
    method: "POST",
    cache: "no-store"
  }).catch(() => {});
}, 1000);