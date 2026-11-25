import sqlite3
from datetime import datetime
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="무한의 계단 - Python Web", page_icon="🪜", layout="centered")

DB_PATH = Path(__file__).parent / "ranking.db"
FRONTEND_DIR = Path(__file__).parent / "_game_frontend"
FRONTEND_DIR.mkdir(exist_ok=True)

CHARACTERS = {
    "mymelo_siyeoni": {
        "name": "마이멜로디 시연이",
        "desc": "연핑크 토끼 후드와 두 귀·리본이 포인트인 시연이 캐릭터",
        "body": "#ff9ff3",
        "head": "#ffeaa7",
        "band": "#ff6b81",
        "eye": "#2d3436",
        "hat": "mymelo_hood",
    },
    "trex_siu": {
        "name": "티라노사우르스 시우",
        "desc": "큼직한 공룡 주둥이와 꼬리·등지느러미가 돋보이는 시우 캐릭터",
        "body": "#2ecc71",
        "head": "#27ae60",
        "band": "#f1c40f",
        "eye": "#1e272e",
        "hat": "dino_spikes",
    },
    "princess_yua": {
        "name": "공주 유아",
        "desc": "풍성한 드레스와 보석 왕관을 쓴 유아 공주님",
        "body": "#ff7979",
        "head": "#ffeaa7",
        "band": "#f9ca24",
        "eye": "#2d3436",
        "hat": "tiara_crown",
    },
    "red_runner": {
        "name": "열혈 러너",
        "desc": "기본기 탄탄한 빨간 머리띠 주자",
        "body": "#ff6b6b",
        "head": "#ffeaa7",
        "band": "#ffdd59",
        "eye": "#2d3436",
        "hat": None,
    },
    "cyber_bot": {
        "name": "네온 봇",
        "desc": "사이버틱한 민트/네온 스타일 유닛",
        "body": "#00cec9",
        "head": "#dfe6e9",
        "band": "#55efc4",
        "eye": "#0984e3",
        "hat": "visor",
    },
    "ninja_shadow": {
        "name": "그림자 닌자",
        "desc": "어둠 속에서 빠르게 치고 올라가는 닌자",
        "body": "#2d3436",
        "head": "#353b48",
        "band": "#ff4757",
        "eye": "#ff6b81",
        "hat": "hood",
    },
}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                score INTEGER NOT NULL,
                character_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_score(nickname: str, score: int, character_name: str) -> bool:
    clean_name = (nickname or "익명").strip()[:16] or "익명"
    if score <= 0:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO rankings (nickname, score, character_name, created_at) VALUES (?, ?, ?, ?)",
            (clean_name, int(score), character_name, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
    return True


def get_top_rankings(limit: int = 10):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            SELECT nickname, score, character_name, created_at
            FROM rankings
            ORDER BY score DESC, id ASC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()


def build_frontend_html(char_data: dict) -> str:
    hat_js = f'"{char_data["hat"]}"' if char_data["hat"] else "null"
    template = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; user-select: none; }
  body {
    margin: 0;
    padding: 0;
    background: transparent;
    display: flex;
    flex-direction: column;
    align-items: center;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    color: white;
    overflow: hidden;
  }
  #game-container {
    position: relative;
    width: 400px;
    height: 600px;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 12px 32px rgba(0,0,0,0.45);
    border: 3px solid #3b3e5b;
  }
  canvas {
    display: block;
    background: linear-gradient(180deg, #1e2749 0%, #273469 100%);
  }
  #ui-layer {
    position: absolute;
    top: 14px;
    left: 0;
    width: 100%;
    padding: 0 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    pointer-events: none;
  }
  #top-meta {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
    color: #b8c4ff;
    font-weight: 700;
  }
  #score {
    font-size: 46px;
    font-weight: 900;
    text-shadow: 0 4px 8px rgba(0,0,0,0.4);
    margin: 2px 0;
  }
  #floating-badge {
    height: 22px;
    font-size: 14px;
    font-weight: 800;
    color: #ffd32a;
    text-shadow: 0 2px 6px rgba(0,0,0,0.6);
  }
  #timer-bar-bg {
    width: 88%;
    height: 13px;
    background: rgba(0,0,0,0.45);
    border-radius: 10px;
    overflow: hidden;
    margin-top: 6px;
    border: 2px solid rgba(255,255,255,0.2);
  }
  #timer-bar {
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, #ff4d4d, #ffcc00, #00e676);
    transition: width 0.05s linear;
  }
  #sound-toggle {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 10;
    background: rgba(15, 17, 26, 0.65);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 8px;
    padding: 5px 9px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
  }
  #controls {
    position: absolute;
    bottom: 18px;
    width: 100%;
    padding: 0 18px;
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }
  .btn {
    flex: 1;
    height: 68px;
    border: none;
    border-radius: 14px;
    font-size: 17px;
    font-weight: 800;
    color: white;
    cursor: pointer;
    box-shadow: 0 6px 0 rgba(0,0,0,0.3);
    transition: transform 0.05s;
  }
  .btn:active {
    transform: translateY(4px);
    box-shadow: 0 2px 0 rgba(0,0,0,0.3);
  }
  #btn-turn { background: #ff5e57; }
  #btn-climb { background: #0be881; color: #1e272e; }

  #overlay {
    position: absolute;
    inset: 0;
    background: rgba(15, 17, 26, 0.9);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 20px;
    z-index: 5;
  }
  #overlay h2 { font-size: 30px; margin-bottom: 8px; color: #ffdd59; }
  #overlay p { font-size: 15px; color: #d2dae2; margin-bottom: 18px; line-height: 1.55; }
  .hint-box {
    background: rgba(11, 232, 129, 0.12);
    border: 1px solid rgba(11, 232, 129, 0.35);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    color: #b8e994;
    margin-bottom: 18px;
    display: none;
  }
  #start-btn {
    padding: 13px 32px;
    font-size: 19px;
    font-weight: 800;
    border: none;
    border-radius: 12px;
    background: #ffdd59;
    color: #1e272e;
    cursor: pointer;
    box-shadow: 0 5px 0 #cca81d;
  }
</style>
</head>
<body>

<div id="game-container">
  <button id="sound-toggle" title="효과음 켜기/끄기">🔊 SFX ON</button>
  <canvas id="gameCanvas" width="400" height="600"></canvas>

  <div id="ui-layer">
    <div id="top-meta">
      <span id="best">BEST: 0</span>
      <span id="char-label">캐릭터: __CHAR_NAME__</span>
    </div>
    <div id="score">0</div>
    <div id="floating-badge"></div>
    <div id="timer-bar-bg"><div id="timer-bar"></div></div>
  </div>

  <div id="controls">
    <button class="btn" id="btn-turn">방향전환<br><small>(← / Shift / A)</small></button>
    <button class="btn" id="btn-climb">오르기<br><small>(↑ / Space / D)</small></button>
  </div>

  <div id="overlay">
    <h2 id="overlay-title">무한의 계단</h2>
    <p id="overlay-desc">
      일반 계단(<strong>+1점</strong>)과 <span style="color:#ffd32a; font-weight:700;">황금 계단(+3점 & 시간 보너스)</span>을 공략하세요!<br>
      발을 헛디디거나 시간이 다 되면 종료됩니다.
    </p>
    <div class="hint-box" id="register-hint">
      실제 게임 점수가 전달되었습니다!<br>아래 <strong>랭킹 등록</strong> 버튼을 눌러 기록을 남기세요.
    </div>
    <button id="start-btn">게임 시작 (Space)</button>
  </div>
</div>

<script>
const Streamlit = {
  sendMessageToHost(type, data) {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: type,
      ...data
    }, "*");
  },
  setComponentReady() {
    this.sendMessageToHost("streamlit:componentReady", { apiVersion: 1 });
  },
  setFrameHeight(height) {
    this.sendMessageToHost("streamlit:setFrameHeight", { height: height });
  },
  setComponentValue(value) {
    this.sendMessageToHost("streamlit:setComponentValue", {
      value: value,
      dataType: "json"
    });
  }
};

window.addEventListener("message", (event) => {
  if (event.data && event.data.type === "streamlit:render") {
    Streamlit.setFrameHeight(620);
  }
});

const CHAR_CONFIG = {
  name: "__CHAR_NAME__",
  body: "__CHAR_BODY__",
  head: "__CHAR_HEAD__",
  band: "__CHAR_BAND__",
  eye: "__CHAR_EYE__",
  hat: __CHAR_HAT__
};

class SoundFX {
  constructor() {
    this.ctx = null;
    this.enabled = true;
  }
  ensureContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }
  playTone(freq, endFreq, duration, type = "triangle", gainVal = 0.14, delay = 0) {
    if (!this.enabled) return;
    this.ensureContext();
    if (!this.ctx) return;

    const now = this.ctx.currentTime + delay;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, now);
    if (endFreq) {
      osc.frequency.exponentialRampToValueAtTime(Math.max(40, endFreq), now + duration);
    }
    gain.gain.setValueAtTime(gainVal, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration);

    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + duration);
  }
  step(combo) {
    const base = 340 + Math.min(350, (combo % 25) * 14);
    this.playTone(base, base * 1.25, 0.065, "triangle", 0.12);
  }
  turn() {
    this.playTone(260, 460, 0.075, "sine", 0.12);
  }
  gold() {
    this.playTone(660, 880, 0.09, "sine", 0.16, 0);
    this.playTone(880, 1320, 0.14, "triangle", 0.16, 0.07);
  }
  gameOver() {
    this.playTone(300, 95, 0.35, "sawtooth", 0.15, 0);
    this.playTone(180, 65, 0.4, "square", 0.1, 0.12);
  }
}

const sfx = new SoundFX();
const soundBtn = document.getElementById("sound-toggle");
soundBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  sfx.enabled = !sfx.enabled;
  soundBtn.innerText = sfx.enabled ? "🔊 SFX ON" : "🔇 SFX OFF";
  if (sfx.enabled) sfx.step(1);
});

const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

const scoreEl = document.getElementById("score");
const bestEl = document.getElementById("best");
const badgeEl = document.getElementById("floating-badge");
const timerBar = document.getElementById("timer-bar");
const overlay = document.getElementById("overlay");
const overlayTitle = document.getElementById("overlay-title");
const overlayDesc = document.getElementById("overlay-desc");
const registerHint = document.getElementById("register-hint");
const startBtn = document.getElementById("start-btn");

const STEP_W = 55;
const STEP_H = 26;
const STEP_ANIM_DURATION = 0.055;

let stairs = [];
let player = {
  x: 0,
  y: 0,
  dir: 1,
  fromX: 0,
  fromY: 0,
  toX: 0,
  toY: 0,
  animT: 1.0
};
let camera = { x: 0, y: 0 };
let score = 0;
let bestScore = Number(localStorage.getItem("infinite_stairs_best") || 0);
let timeLeft = 100;
let isPlaying = false;
let isGameOver = false;
let lastTime = 0;
let particles = [];
let badgeTimer = 0;

bestEl.innerText = `BEST: ${bestScore}`;

function showBadge(text, color = "#ffd32a") {
  badgeEl.innerText = text;
  badgeEl.style.color = color;
  badgeTimer = 0.85;
}

function createStair(x, y, idx) {
  const isGold = idx > 2 && Math.random() < 0.14;
  return { x, y, isGold };
}

function getVisualPlayerPos() {
  const prevVisX = player.fromX + (player.toX - player.fromX) * Math.min(1, player.animT);
  const prevVisY = player.fromY + (player.toY - player.fromY) * Math.min(1, player.animT);
  return { x: prevVisX, y: prevVisY };
}

function initGame() {
  stairs = [];
  let curX = 0;
  let curY = 0;
  let dir = 1;

  stairs.push({ x: 0, y: 0, isGold: false });

  for (let i = 1; i < 100; i++) {
    if (i > 1 && Math.random() < 0.35) {
      dir *= -1;
    }
    curX += dir;
    curY += 1;
    stairs.push(createStair(curX, curY, i));
  }

  player = {
    x: 0,
    y: 0,
    dir: 1,
    fromX: 0,
    fromY: 0,
    toX: 0,
    toY: 0,
    animT: 1.0
  };
  camera = { x: 0, y: 0 };
  score = 0;
  timeLeft = 100;
  isPlaying = true;
  isGameOver = false;
  particles = [];
  badgeEl.innerText = "";

  scoreEl.innerText = score;
  registerHint.style.display = "none";
  overlay.style.display = "none";
  lastTime = performance.now();
}

function addMoreStairs() {
  while (stairs.length < player.y + 50) {
    const last = stairs[stairs.length - 1];
    const prev = stairs[stairs.length - 2];
    let dir = last.x - prev.x;
    if (Math.random() < 0.38) {
      dir *= -1;
    }
    const nextIdx = stairs.length;
    stairs.push(createStair(last.x + dir, last.y + 1, nextIdx));
  }
}

function spawnParticles(x, y, color, count = 10) {
  for (let i = 0; i < count; i++) {
    particles.push({
      x: x,
      y: y,
      vx: (Math.random() - 0.5) * 7,
      vy: (Math.random() - 0.9) * 6.5,
      life: 1.0,
      color: color
    });
  }
}

function advancePlayer(turned) {
  if (!isPlaying || isGameOver) return;
  if (turned) player.dir *= -1;

  const startVis = getVisualPlayerPos();
  const nextX = player.x + player.dir;
  const nextY = player.y + 1;
  const targetStair = stairs[nextY];

  player.fromX = startVis.x;
  player.fromY = startVis.y;
  player.toX = nextX;
  player.toY = nextY;
  player.animT = 0.0;

  if (targetStair && targetStair.x === nextX) {
    player.x = nextX;
    player.y = nextY;

    if (targetStair.isGold) {
      score += 3;
      timeLeft = Math.min(100, timeLeft + 24);
      sfx.gold();
      spawnParticles(canvas.width / 2, canvas.height * 0.65, "#ffd32a", 20);
      showBadge("✨ GOLD STAIR +3 & TIME UP!", "#ffd32a");
      targetStair.isGold = false;
    } else {
      score += 1;
      const recover = Math.max(8, 16 - Math.floor(score / 45));
      timeLeft = Math.min(100, timeLeft + recover);
      if (turned) sfx.turn();
      else sfx.step(score);
      spawnParticles(canvas.width / 2, canvas.height * 0.65, "#0be881", 9);
    }

    scoreEl.innerText = score;
    addMoreStairs();
  } else {
    player.x = nextX;
    player.y = nextY;
    triggerGameOver("발을 헛디뎠습니다!");
  }
}

function triggerGameOver(reason) {
  if (isGameOver) return;
  isGameOver = true;
  isPlaying = false;
  sfx.gameOver();

  if (score > bestScore) {
    bestScore = score;
    localStorage.setItem("infinite_stairs_best", bestScore);
    bestEl.innerText = `BEST: ${bestScore}`;
  }

  overlayTitle.innerText = "GAME OVER";
  overlayDesc.innerHTML = `${reason}<br>최종 기록: <strong style="color:#0be881; font-size:24px;">${score}점</strong>`;

  if (score > 0) {
    registerHint.style.display = "block";
    const runId = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    Streamlit.setComponentValue({
      runId: runId,
      score: score,
      characterName: CHAR_CONFIG.name
    });
  } else {
    registerHint.style.display = "none";
  }

  startBtn.innerText = "다시 도전 (Space)";
  overlay.style.display = "flex";
}

function update(dt) {
  if (badgeTimer > 0) {
    badgeTimer -= dt;
    if (badgeTimer <= 0) badgeEl.innerText = "";
  }

  if (!isPlaying) return;

  if (player.animT < 1.0) {
    player.animT = Math.min(1.0, player.animT + dt / STEP_ANIM_DURATION);
  }

  const drainRate = 18 + Math.min(45, score * 0.22);
  timeLeft -= drainRate * dt;

  if (timeLeft <= 0) {
    timeLeft = 0;
    triggerGameOver("시간이 초과되었습니다!");
  }
  timerBar.style.width = `${timeLeft}%`;

  const vis = getVisualPlayerPos();
  const targetCamX = vis.x * STEP_W;
  const targetCamY = vis.y * STEP_H;
  camera.x += (targetCamX - camera.x) * 18 * dt;
  camera.y += (targetCamY - camera.y) * 18 * dt;

  for (let i = particles.length - 1; i >= 0; i--) {
    let p = particles[i];
    p.x += p.vx;
    p.y += p.vy;
    p.vy += 0.25;
    p.life -= dt * 2.5;
    if (p.life <= 0) particles.splice(i, 1);
  }
}

function drawFlower(cx, cy, radius = 5.5) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.fillStyle = "#ffffff";
  ctx.strokeStyle = "#1e1e24";
  ctx.lineWidth = 1.5;

  for (let i = 0; i < 4; i++) {
    ctx.save();
    ctx.rotate((Math.PI / 2) * i + Math.PI / 4);
    ctx.beginPath();
    ctx.ellipse(0, -radius * 0.72, radius * 0.55, radius * 0.68, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  ctx.fillStyle = "#ffd32a";
  ctx.beginPath();
  ctx.arc(0, 0, radius * 0.4, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.restore();
}

function drawMyMelodyCharacter(px, py, hopOffset) {
  const outline = "#1e1e24";
  const pinkHood = "#ff3b9a";
  const whiteSkin = "#ffffff";

  ctx.save();
  ctx.translate(px, py - hopOffset);
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  // 두 다리
  ctx.fillStyle = whiteSkin;
  ctx.strokeStyle = outline;
  ctx.lineWidth = 2.1;
  ctx.beginPath();
  ctx.roundRect(-10.5, -13, 9.5, 13, 4.5);
  ctx.roundRect(1, -13, 9.5, 13, 4.5);
  ctx.fill();
  ctx.stroke();

  // 몸통
  ctx.beginPath();
  ctx.ellipse(0, -20, 13, 10.5, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 핑크 케이프
  ctx.fillStyle = pinkHood;
  ctx.beginPath();
  ctx.moveTo(-14, -28);
  ctx.lineTo(-18, -21);
  ctx.lineTo(-6, -23.5);
  ctx.lineTo(0, -26.5);
  ctx.lineTo(6, -23.5);
  ctx.lineTo(18, -21);
  ctx.lineTo(14, -28);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 귀 1 (뒤쪽 접힌 핑크 귀 - 확실히 구분되도록 바깥쪽 배치)
  ctx.fillStyle = pinkHood;
  ctx.beginPath();
  ctx.moveTo(6, -47);
  ctx.bezierCurveTo(22, -62, 26, -42, 12, -37);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 귀 2 (앞쪽 길게 뻗은 핑크 귀)
  ctx.beginPath();
  ctx.moveTo(-10, -48);
  ctx.bezierCurveTo(-19, -71, -3, -75, 2, -52);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 핑크 후드 본체
  ctx.beginPath();
  ctx.arc(0, -39, 16, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 하얀 얼굴
  ctx.fillStyle = whiteSkin;
  ctx.lineWidth = 1.9;
  ctx.beginPath();
  ctx.ellipse(1.2, -37.5, 12.8, 10.8, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 세로 눈 + 노란 코 + 미소
  ctx.fillStyle = outline;
  ctx.beginPath();
  ctx.ellipse(-4.5, -38.5, 2.0, 4.0, 0, 0, Math.PI * 2);
  ctx.ellipse(7.8, -38.5, 2.0, 4.0, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#ffd32a";
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.ellipse(1.8, -35.2, 2.6, 1.9, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(1.8, -32.3, 2.4, 0.15 * Math.PI, 0.85 * Math.PI);
  ctx.stroke();

  // 손 흔들림
  const armSwing = hopOffset > 0 ? -3 : 0;
  ctx.fillStyle = whiteSkin;
  ctx.lineWidth = 1.9;
  ctx.beginPath();
  ctx.arc(-11, -23.5 + armSwing, 4.2, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 꽃 장식 (귀 2 아래쪽 포인트)
  drawFlower(-8.5, -49, 5.5);

  ctx.restore();
}

function drawTRexCharacter(px, py, hopOffset) {
  const outline = "#1e272e";
  const dinoGreen = "#2ecc71";
  const dinoDark = "#219150";
  const spikeGold = "#ffd32a";
  const bellyLight = "#a8e6cf";

  ctx.save();
  ctx.translate(px, py - hopOffset);
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  // 1. 두툼한 티라노 꼬리 (왼쪽 뒤)
  ctx.fillStyle = dinoGreen;
  ctx.strokeStyle = outline;
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  ctx.moveTo(-10, -14);
  ctx.quadraticCurveTo(-28, -12, -31, -22);
  ctx.quadraticCurveTo(-22, -23, -10, -24);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 꼬리 위 노란 스파이크
  ctx.fillStyle = spikeGold;
  ctx.beginPath();
  ctx.moveTo(-21, -22);
  ctx.lineTo(-24, -27);
  ctx.lineTo(-17, -23);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 2. 튼튼한 두 다리
  const legStride = hopOffset > 0 ? 2.5 : 0;
  ctx.fillStyle = dinoDark;
  ctx.beginPath();
  ctx.roundRect(-11 - legStride, -13, 9.5, 13, 4);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = dinoGreen;
  ctx.beginPath();
  ctx.roundRect(1 + legStride, -13, 9.5, 13, 4);
  ctx.fill();
  ctx.stroke();

  // 3. 티라노 몸통 & 배 포인트
  ctx.fillStyle = dinoGreen;
  ctx.beginPath();
  ctx.ellipse(-1, -22, 13, 12.5, -0.1, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = bellyLight;
  ctx.beginPath();
  ctx.ellipse(5, -21, 6.5, 9.5, 0, 0, Math.PI * 2);
  ctx.fill();

  // 4. 등줄기 노란 지느러미 스파이크 3개
  ctx.fillStyle = spikeGold;
  const spikes = [
    { x: -12, y: -31, tipX: -19, tipY: -35 },
    { x: -13, y: -23, tipX: -20, tipY: -26 },
    { x: -11, y: -15, tipX: -17, tipY: -17 }
  ];
  for (const sp of spikes) {
    ctx.beginPath();
    ctx.moveTo(sp.x, sp.y - 3);
    ctx.lineTo(sp.tipX, sp.tipY);
    ctx.lineTo(sp.x, sp.y + 3);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  // 5. 큼직한 티라노 머리 & 길쭉한 주둥이(오른쪽 진행 방향)
  ctx.fillStyle = dinoGreen;
  ctx.beginPath();
  ctx.moveTo(-10, -48);
  ctx.quadraticCurveTo(6, -52, 18, -44);
  ctx.quadraticCurveTo(22, -39, 17, -35);
  ctx.lineTo(6, -35);
  ctx.lineTo(14, -32);
  ctx.quadraticCurveTo(6, -29, -10, -33);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 앙증맞은 짧은 앞발
  ctx.fillStyle = dinoGreen;
  ctx.beginPath();
  ctx.roundRect(8, -25, 7, 5, 2.5);
  ctx.fill();
  ctx.stroke();

  // 사납지만 귀여운 눈 & 눈썹
  ctx.fillStyle = outline;
  ctx.beginPath();
  ctx.arc(5, -42, 2.5, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(5.8, -42.8, 0.9, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = outline;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(2, -45.5);
  ctx.lineTo(9, -43.5);
  ctx.stroke();

  ctx.restore();
}

function drawPrincessCharacter(px, py, hopOffset) {
  const outline = "#2d2235";
  const dressPink = "#ff6b9d";
  const dressLight = "#ffa8c5";
  const gold = "#ffd32a";
  const hairGold = "#f6b93b";

  ctx.save();
  ctx.translate(px, py - hopOffset);
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  // 1. 뒤로 흐르는 금발/허니 머릿결
  ctx.fillStyle = hairGold;
  ctx.strokeStyle = outline;
  ctx.lineWidth = 2.0;
  ctx.beginPath();
  ctx.ellipse(-6, -36, 13, 13, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 2. 발끝(구두)
  ctx.fillStyle = "#ff477e";
  ctx.beginPath();
  ctx.ellipse(-6, -2, 4.5, 2.5, 0, 0, Math.PI * 2);
  ctx.ellipse(6, -2, 4.5, 2.5, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 3. 풍성한 공주 드레스 치마
  ctx.fillStyle = dressPink;
  ctx.beginPath();
  ctx.moveTo(-7, -28);
  ctx.lineTo(7, -28);
  ctx.quadraticCurveTo(17, -14, 18, -3);
  ctx.lineTo(-18, -3);
  ctx.quadraticCurveTo(-17, -14, -7, -28);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 치마 앞쪽 밝은 레이어 포인트
  ctx.fillStyle = dressLight;
  ctx.beginPath();
  ctx.moveTo(-3, -27);
  ctx.lineTo(4, -27);
  ctx.lineTo(10, -4);
  ctx.lineTo(-10, -4);
  ctx.closePath();
  ctx.fill();

  // 드레스 허리 리본
  ctx.fillStyle = gold;
  ctx.beginPath();
  ctx.arc(0, -24, 3.2, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 4. 얼굴
  ctx.fillStyle = "#ffeaa7";
  ctx.beginPath();
  ctx.arc(1, -38, 11.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 반짝이는 눈 & 볼터치
  ctx.fillStyle = outline;
  ctx.beginPath();
  ctx.ellipse(-3.5, -39, 2.0, 3.6, 0, 0, Math.PI * 2);
  ctx.ellipse(6.5, -39, 2.0, 3.6, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(-4.1, -40.2, 0.9, 0, Math.PI * 2);
  ctx.arc(5.9, -40.2, 0.9, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "rgba(255, 107, 157, 0.55)";
  ctx.beginPath();
  ctx.ellipse(-1.5, -35.5, 2.6, 1.5, 0, 0, Math.PI * 2);
  ctx.ellipse(8.2, -35.5, 2.6, 1.5, 0, 0, Math.PI * 2);
  ctx.fill();

  // 작은 미소
  ctx.strokeStyle = outline;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(1.5, -35, 2.4, 0.15 * Math.PI, 0.85 * Math.PI);
  ctx.stroke();

  // 5. 화려한 공주 왕관 + 루비 보석
  ctx.fillStyle = gold;
  ctx.strokeStyle = outline;
  ctx.lineWidth = 1.9;
  ctx.beginPath();
  ctx.moveTo(-9, -48);
  ctx.lineTo(-11, -59);
  ctx.lineTo(-4, -53);
  ctx.lineTo(1, -62);
  ctx.lineTo(6, -53);
  ctx.lineTo(13, -59);
  ctx.lineTo(11, -48);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#ff3838";
  ctx.beginPath();
  ctx.arc(1, -51.5, 2.4, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

function drawCharacter(px, py, dir, hopOffset) {
  if (CHAR_CONFIG.hat === "mymelo_hood") {
    ctx.save();
    if (dir === -1) {
      ctx.translate(px * 2, 0);
      ctx.scale(-1, 1);
    }
    drawMyMelodyCharacter(px, py, hopOffset);
    ctx.restore();
    return;
  }

  if (CHAR_CONFIG.hat === "dino_spikes") {
    ctx.save();
    if (dir === -1) {
      ctx.translate(px * 2, 0);
      ctx.scale(-1, 1);
    }
    drawTRexCharacter(px, py, hopOffset);
    ctx.restore();
    return;
  }

  if (CHAR_CONFIG.hat === "tiara_crown") {
    ctx.save();
    if (dir === -1) {
      ctx.translate(px * 2, 0);
      ctx.scale(-1, 1);
    }
    drawPrincessCharacter(px, py, hopOffset);
    ctx.restore();
    return;
  }

  ctx.save();
  ctx.translate(px, py - hopOffset);
  if (dir === -1) ctx.scale(-1, 1);

  ctx.fillStyle = CHAR_CONFIG.body;
  ctx.beginPath();
  ctx.roundRect(-12, -32, 24, 32, 8);
  ctx.fill();

  ctx.fillStyle = CHAR_CONFIG.head;
  ctx.beginPath();
  ctx.arc(0, -38, 12, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = CHAR_CONFIG.eye;
  ctx.beginPath();
  ctx.arc(5, -40, 2.5, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = CHAR_CONFIG.band;
  ctx.fillRect(-12, -45, 24, 4);

  if (CHAR_CONFIG.hat === "visor") {
    ctx.fillStyle = "#00f5d4";
    ctx.fillRect(0, -43, 12, 5);
  } else if (CHAR_CONFIG.hat === "hood") {
    ctx.strokeStyle = CHAR_CONFIG.band;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, -38, 13.5, Math.PI * 0.85, Math.PI * 2.15);
    ctx.stroke();
  }

  ctx.restore();
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const centerX = canvas.width / 2;
  const baseScreenY = canvas.height * 0.65;

  const altitudeRatio = Math.min(1, score / 300);
  ctx.fillStyle = `rgba(10, 12, 28, ${altitudeRatio * 0.6})`;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const startIdx = Math.max(0, player.y - 10);
  const endIdx = Math.min(stairs.length, player.y + 22);

  for (let i = startIdx; i < endIdx; i++) {
    const s = stairs[i];
    const screenX = centerX + (s.x * STEP_W - camera.x);
    const screenY = baseScreenY - (s.y * STEP_H - camera.y);

    if (s.isGold) {
      ctx.fillStyle = "#b7791f";
      ctx.beginPath();
      ctx.roundRect(screenX - 25, screenY + 6, 50, 14, 5);
      ctx.fill();

      ctx.fillStyle = "#ffd32a";
      ctx.beginPath();
      ctx.roundRect(screenX - 25, screenY, 50, 13, 5);
      ctx.fill();

      ctx.fillStyle = "#fff9db";
      ctx.beginPath();
      ctx.arc(screenX, screenY + 6.5, 3, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.fillStyle = "#576574";
      ctx.beginPath();
      ctx.roundRect(screenX - 24, screenY + 6, 48, 14, 4);
      ctx.fill();

      ctx.fillStyle = (i > 0 && i % 50 === 0) ? "#ffdd59" : "#c8d6e5";
      ctx.beginPath();
      ctx.roundRect(screenX - 24, screenY, 48, 12, 4);
      ctx.fill();
    }
  }

  const vis = getVisualPlayerPos();
  const px = centerX + (vis.x * STEP_W - camera.x);
  const py = baseScreenY - (vis.y * STEP_H - camera.y);
  const hopOffset = player.animT < 1.0 ? Math.sin(player.animT * Math.PI) * 9 : 0;

  drawCharacter(px, py, player.dir, hopOffset);

  for (let p of particles) {
    ctx.globalAlpha = Math.max(0, p.life);
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1.0;
}

function gameLoop(timestamp) {
  const dt = Math.min(0.05, (timestamp - lastTime) / 1000);
  lastTime = timestamp;

  update(dt);
  draw();
  requestAnimationFrame(gameLoop);
}

window.addEventListener("keydown", (e) => {
  if (e.repeat) return;
  if (!isPlaying && (e.code === "Space" || e.code === "Enter")) {
    initGame();
    return;
  }
  if (e.code === "ArrowUp" || e.code === "Space" || e.code === "KeyD") {
    e.preventDefault();
    advancePlayer(false);
  } else if (e.code === "ArrowLeft" || e.code === "ShiftLeft" || e.code === "KeyA") {
    e.preventDefault();
    advancePlayer(true);
  }
});

document.getElementById("btn-climb").addEventListener("pointerdown", (e) => {
  e.preventDefault();
  advancePlayer(false);
});
document.getElementById("btn-turn").addEventListener("pointerdown", (e) => {
  e.preventDefault();
  advancePlayer(true);
});
startBtn.addEventListener("click", initGame);

Streamlit.setComponentReady();
Streamlit.setFrameHeight(620);
requestAnimationFrame(gameLoop);
</script>
</body>
</html>
"""
    return (
        template.replace("__CHAR_NAME__", char_data["name"])
        .replace("__CHAR_BODY__", char_data["body"])
        .replace("__CHAR_HEAD__", char_data["head"])
        .replace("__CHAR_BAND__", char_data["band"])
        .replace("__CHAR_EYE__", char_data["eye"])
        .replace("__CHAR_HAT__", hat_js)
    )


init_db()

if "flash_message" in st.session_state and st.session_state["flash_message"]:
    st.success(st.session_state.pop("flash_message"))

st.title("🪜 무한의 계단 (Python Web Edition)")
st.caption("조작법: [↑ / Space / D / 오르기 버튼] 등반 | [← / Shift / A / 방향전환 버튼] 방향 전환 + 등반")

col1, col2 = st.columns([1, 1.3])
with col1:
    nickname = st.text_input(
        "랭킹 닉네임",
        value=st.session_state.get("player_nickname", "플레이어"),
        max_chars=16,
    )
    st.session_state["player_nickname"] = nickname

with col2:
    char_keys = list(CHARACTERS.keys())
    selected_char_key = st.selectbox(
        "캐릭터 선택",
        options=char_keys,
        format_func=lambda k: f"{CHARACTERS[k]['name']} — {CHARACTERS[k]['desc']}",
    )

char_data = CHARACTERS[selected_char_key]
index_html_path = FRONTEND_DIR / "index.html"
index_html_path.write_text(build_frontend_html(char_data), encoding="utf-8")

infinite_stairs_component = components.declare_component(
    "infinite_stairs_game",
    path=str(FRONTEND_DIR),
)

component_value = infinite_stairs_component(
    characterName=char_data["name"],
    key=f"game_comp_{selected_char_key}",
    default=None,
)

if isinstance(component_value, dict):
    run_id = component_value.get("runId")
    reported_score = component_value.get("score")
    reported_char = component_value.get("characterName", char_data["name"])
    if run_id and run_id != st.session_state.get("last_run_id"):
        st.session_state["last_run_id"] = run_id
        if isinstance(reported_score, (int, float)) and int(reported_score) > 0:
            st.session_state["pending_score"] = int(reported_score)
            st.session_state["pending_char"] = str(reported_char)

pending_score = st.session_state.get("pending_score")
pending_char = st.session_state.get("pending_char", char_data["name"])

with st.container(border=True):
    st.markdown("### 📝 실전 기록 랭킹 등록")
    if pending_score and pending_score > 0:
        st.info(f"방금 종료된 게임 기록: **{pending_score}점** ({pending_char})")
        if st.button(f"🏆 {pending_score}점 랭킹 등록 & 화면 새로고침", type="primary", use_container_width=True):
            if save_score(nickname, pending_score, pending_char):
                st.session_state["pending_score"] = None
                st.session_state["flash_message"] = (
                    f"🏆 '{(nickname or '익명').strip()[:16] or '익명'}' 님의 {pending_score}점 기록이 등록되었습니다!"
                )
            st.rerun()
    else:
        st.caption("게임을 플레이하고 게임 오버가 되면 실제 점수가 자동으로 전달되며, 이 자리에서 등록 버튼을 누를 수 있습니다.")

st.divider()
st.subheader("🏆 실시간 랭킹 보드 (TOP 10)")

top_rows = get_top_rankings(10)
if top_rows:
    formatted_rows = [
        {
            "순위": idx,
            "닉네임": row[0],
            "점수": row[1],
            "캐릭터": row[2],
            "기록 일시": row[3],
        }
        for idx, row in enumerate(top_rows, start=1)
    ]
    st.dataframe(formatted_rows, use_container_width=True, hide_index=True)
else:
    st.info("아직 등록된 기록이 없습니다. 첫 번째 기록을 세워보세요!")
