import sqlite3
from datetime import datetime
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="조카들 미니게임 아케이드", page_icon="🎮", layout="centered")

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

SCORE_GAMES = {"stairs", "timing_jump", "dodge_drop"}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL DEFAULT 'stairs',
                nickname TEXT NOT NULL,
                score INTEGER NOT NULL,
                clear_time REAL,
                character_name TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        cols = [row[1] for row in conn.execute("PRAGMA table_info(rankings)").fetchall()]
        if "game_type" not in cols:
            conn.execute("ALTER TABLE rankings ADD COLUMN game_type TEXT NOT NULL DEFAULT 'stairs'")
        if "clear_time" not in cols:
            conn.execute("ALTER TABLE rankings ADD COLUMN clear_time REAL")
        if "message" not in cols:
            conn.execute("ALTER TABLE rankings ADD COLUMN message TEXT NOT NULL DEFAULT ''")
        conn.commit()


def qualifies_for_top10(game_type: str, value: float) -> bool:
    if value is None:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        if game_type == "one_to_50":
            if float(value) <= 0:
                return False
            rows = conn.execute(
                """
                SELECT clear_time FROM rankings
                WHERE game_type = 'one_to_50' AND clear_time IS NOT NULL
                ORDER BY clear_time ASC, id ASC
                LIMIT 10
                """,
            ).fetchall()
            if len(rows) < 10:
                return True
            tenth_time = float(rows[-1][0])
            return float(value) < tenth_time
        else:
            if int(value) <= 0:
                return False
            rows = conn.execute(
                """
                SELECT score FROM rankings
                WHERE game_type = ?
                ORDER BY score DESC, id ASC
                LIMIT 10
                """,
                (game_type,),
            ).fetchall()
            if len(rows) < 10:
                return True
            tenth_score = int(rows[-1][0])
            return int(value) > tenth_score


def save_score_game(game_type: str, nickname: str, score: int, character_name: str, message: str = "") -> bool:
    clean_name = (nickname or "익명").strip()[:16] or "익명"
    if score <= 0:
        return False
    clean_msg = (message or "").strip()[:30] if qualifies_for_top10(game_type, score) else ""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO rankings (game_type, nickname, score, clear_time, character_name, message, created_at)
            VALUES (?, ?, ?, NULL, ?, ?, ?)
            """,
            (game_type, clean_name, int(score), character_name, clean_msg, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
    return True


def save_one_to_50_score(nickname: str, clear_time: float, character_name: str, message: str = "") -> bool:
    clean_name = (nickname or "익명").strip()[:16] or "익명"
    if clear_time is None or float(clear_time) <= 0:
        return False
    rounded_time = round(float(clear_time), 2)
    clean_msg = (message or "").strip()[:30] if qualifies_for_top10("one_to_50", rounded_time) else ""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO rankings (game_type, nickname, score, clear_time, character_name, message, created_at)
            VALUES ('one_to_50', ?, 0, ?, ?, ?, ?)
            """,
            (clean_name, rounded_time, character_name, clean_msg, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
    return True


def get_top_rankings(game_type: str, limit: int = 10):
    with sqlite3.connect(DB_PATH) as conn:
        if game_type == "one_to_50":
            cur = conn.execute(
                """
                SELECT nickname, clear_time, character_name, message, created_at
                FROM rankings
                WHERE game_type = 'one_to_50' AND clear_time IS NOT NULL
                ORDER BY clear_time ASC, id ASC
                LIMIT ?
                """,
                (limit,),
            )
        else:
            cur = conn.execute(
                """
                SELECT nickname, score, character_name, message, created_at
                FROM rankings
                WHERE game_type = ?
                ORDER BY score DESC, id ASC
                LIMIT ?
                """,
                (game_type, limit),
            )
        return cur.fetchall()


CHARACTER_DRAW_JS = """
function drawFlower(cx, cy, radius = 5.8) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.fillStyle = "#ffffff";
  ctx.strokeStyle = "#232028";
  ctx.lineWidth = 1.6;
  for (let i = 0; i < 4; i++) {
    ctx.save();
    ctx.rotate((Math.PI / 2) * i + Math.PI / 4);
    ctx.beginPath();
    ctx.ellipse(0, -radius * 0.72, radius * 0.56, radius * 0.72, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }
  ctx.fillStyle = "#ffd32a";
  ctx.beginPath();
  ctx.arc(0, 0, radius * 0.42, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

function drawMyMelodyCharacter(px, py, hopOffset) {
  const outline = "#232028";
  const pinkHood = "#ff3b9a";
  const whiteSkin = "#ffffff";
  const isJumping = hopOffset > 0.5;

  ctx.save();
  ctx.translate(px, py - hopOffset);
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  ctx.fillStyle = whiteSkin;
  ctx.strokeStyle = outline;
  ctx.lineWidth = 2.0;
  ctx.beginPath();
  ctx.arc(-13, -15, 4.3, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  const legLift = isJumping ? -3.5 : 0;
  ctx.fillStyle = whiteSkin;
  ctx.beginPath();
  ctx.ellipse(-3, -7 + legLift, 5.2, 7.5, -0.22, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.beginPath();
  ctx.ellipse(4.5, -5.5 + legLift * 0.7, 5.2, 7.2, 0.25, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = whiteSkin;
  ctx.beginPath();
  ctx.ellipse(0, -18, 12, 10.5, -0.08, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = pinkHood;
  ctx.beginPath();
  ctx.moveTo(-11, -26);
  ctx.lineTo(-15, -20);
  ctx.lineTo(-5, -22.5);
  ctx.lineTo(5, -22.5);
  ctx.lineTo(13, -21);
  ctx.lineTo(10, -26);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = pinkHood;
  ctx.lineWidth = 2.1;

  ctx.beginPath();
  ctx.moveTo(4, -46);
  ctx.bezierCurveTo(16, -61, 29, -62, 27, -52);
  ctx.bezierCurveTo(25, -45, 13, -43, 5, -41);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(6, -42);
  ctx.bezierCurveTo(18, -48, 30, -47, 28, -38);
  ctx.bezierCurveTo(25, -32, 14, -33, 6, -35);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = pinkHood;
  ctx.beginPath();
  ctx.arc(-1, -37, 15.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = whiteSkin;
  ctx.lineWidth = 2.0;
  ctx.beginPath();
  ctx.ellipse(2.5, -36, 12.2, 11.2, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = pinkHood;
  ctx.beginPath();
  ctx.arc(-2, -37, 15.5, Math.PI * 0.62, Math.PI * 1.45);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = whiteSkin;
  ctx.beginPath();
  ctx.ellipse(3.2, -36, 11.4, 10.6, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = outline;
  ctx.beginPath();
  ctx.ellipse(5.5, -37.5, 2.2, 4.4, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#ffd32a";
  ctx.strokeStyle = outline;
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.ellipse(14.2, -35.2, 2.3, 1.8, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = outline;
  ctx.beginPath();
  ctx.ellipse(11.8, -31.5, 1.5, 1.9, 0, 0, Math.PI * 2);
  ctx.fill();

  const handY = isJumping ? -26 : -24;
  ctx.fillStyle = whiteSkin;
  ctx.strokeStyle = outline;
  ctx.lineWidth = 2.0;

  ctx.beginPath();
  ctx.roundRect(4, handY - 4, 7.5, 12, 4);
  ctx.fill();
  ctx.stroke();

  ctx.beginPath();
  ctx.roundRect(7.5, handY - 2, 8.5, 12.5, 4.2);
  ctx.fill();
  ctx.stroke();

  drawFlower(6.5, -48.5, 5.6);

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

  ctx.fillStyle = spikeGold;
  ctx.beginPath();
  ctx.moveTo(-21, -22);
  ctx.lineTo(-24, -27);
  ctx.lineTo(-17, -23);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

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

  ctx.fillStyle = dinoGreen;
  ctx.beginPath();
  ctx.ellipse(-1, -22, 13, 12.5, -0.1, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = bellyLight;
  ctx.beginPath();
  ctx.ellipse(5, -21, 6.5, 9.5, 0, 0, Math.PI * 2);
  ctx.fill();

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

  ctx.fillStyle = dinoGreen;
  ctx.beginPath();
  ctx.roundRect(8, -25, 7, 5, 2.5);
  ctx.fill();
  ctx.stroke();

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

  ctx.fillStyle = hairGold;
  ctx.strokeStyle = outline;
  ctx.lineWidth = 2.0;
  ctx.beginPath();
  ctx.ellipse(-6, -36, 13, 13, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#ff477e";
  ctx.beginPath();
  ctx.ellipse(-6, -2, 4.5, 2.5, 0, 0, Math.PI * 2);
  ctx.ellipse(6, -2, 4.5, 2.5, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

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

  ctx.fillStyle = dressLight;
  ctx.beginPath();
  ctx.moveTo(-3, -27);
  ctx.lineTo(4, -27);
  ctx.lineTo(10, -4);
  ctx.lineTo(-10, -4);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = gold;
  ctx.beginPath();
  ctx.arc(0, -24, 3.2, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#ffeaa7";
  ctx.beginPath();
  ctx.arc(1, -38, 11.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

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

  ctx.strokeStyle = outline;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(1.5, -35, 2.4, 0.15 * Math.PI, 0.85 * Math.PI);
  ctx.stroke();

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
"""


def build_stairs_html(char_data: dict) -> str:
    hat_js = f'"{char_data["hat"]}"' if char_data["hat"] else "null"
    template = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; user-select: none; }
  body {
    margin: 0; padding: 0; background: transparent;
    display: flex; flex-direction: column; align-items: center;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    color: white; overflow: hidden;
  }
  #game-container {
    position: relative; width: 400px; height: 600px;
    border-radius: 16px; overflow: hidden;
    box-shadow: 0 12px 32px rgba(0,0,0,0.45); border: 3px solid #3b3e5b;
  }
  canvas { display: block; background: linear-gradient(180deg, #1e2749 0%, #273469 100%); }
  #ui-layer {
    position: absolute; top: 14px; left: 0; width: 100%; padding: 0 18px;
    display: flex; flex-direction: column; align-items: center; pointer-events: none;
  }
  #top-meta {
    width: 100%; display: flex; justify-content: space-between; align-items: center;
    font-size: 13px; color: #b8c4ff; font-weight: 700;
  }
  #score { font-size: 46px; font-weight: 900; text-shadow: 0 4px 8px rgba(0,0,0,0.4); margin: 2px 0; }
  #floating-badge { height: 22px; font-size: 14px; font-weight: 800; color: #ffd32a; }
  #timer-bar-bg {
    width: 88%; height: 13px; background: rgba(0,0,0,0.45); border-radius: 10px;
    overflow: hidden; margin-top: 6px; border: 2px solid rgba(255,255,255,0.2);
  }
  #timer-bar {
    width: 100%; height: 100%;
    background: linear-gradient(90deg, #ff4d4d, #ffcc00, #00e676);
    transition: width 0.05s linear;
  }
  #sound-toggle {
    position: absolute; top: 12px; right: 12px; z-index: 10;
    background: rgba(15, 17, 26, 0.65); color: #fff;
    border: 1px solid rgba(255,255,255,0.25); border-radius: 8px;
    padding: 5px 9px; font-size: 12px; font-weight: 700; cursor: pointer;
  }
  #controls {
    position: absolute; bottom: 18px; width: 100%; padding: 0 18px;
    display: flex; justify-content: space-between; gap: 12px;
  }
  .btn {
    flex: 1; height: 68px; border: none; border-radius: 14px;
    font-size: 17px; font-weight: 800; color: white; cursor: pointer;
    box-shadow: 0 6px 0 rgba(0,0,0,0.3);
  }
  .btn:active { transform: translateY(4px); box-shadow: 0 2px 0 rgba(0,0,0,0.3); }
  #btn-turn { background: #ff5e57; }
  #btn-climb { background: #0be881; color: #1e272e; }
  #overlay {
    position: absolute; inset: 0; background: rgba(15, 17, 26, 0.9);
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    text-align: center; padding: 20px; z-index: 5;
  }
  #overlay h2 { font-size: 30px; margin-bottom: 8px; color: #ffdd59; }
  #overlay p { font-size: 15px; color: #d2dae2; margin-bottom: 18px; line-height: 1.55; }
  .hint-box {
    background: rgba(11, 232, 129, 0.12); border: 1px solid rgba(11, 232, 129, 0.35);
    border-radius: 10px; padding: 10px 14px; font-size: 13px; color: #b8e994;
    margin-bottom: 18px; display: none;
  }
  #start-btn {
    padding: 13px 32px; font-size: 19px; font-weight: 800; border: none;
    border-radius: 12px; background: #ffdd59; color: #1e272e; cursor: pointer;
    box-shadow: 0 5px 0 #cca81d;
  }
</style>
</head>
<body>
<div id="game-container">
  <button id="sound-toggle">🔊 SFX ON</button>
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
    window.parent.postMessage({ isStreamlitMessage: true, type: type, ...data }, "*");
  },
  setComponentReady() { this.sendMessageToHost("streamlit:componentReady", { apiVersion: 1 }); },
  setFrameHeight(h) { this.sendMessageToHost("streamlit:setFrameHeight", { height: h }); },
  setComponentValue(v) { this.sendMessageToHost("streamlit:setComponentValue", { value: v, dataType: "json" }); }
};
window.addEventListener("message", (e) => {
  if (e.data && e.data.type === "streamlit:render") Streamlit.setFrameHeight(620);
});

const CHAR_CONFIG = {
  name: "__CHAR_NAME__", body: "__CHAR_BODY__", head: "__CHAR_HEAD__",
  band: "__CHAR_BAND__", eye: "__CHAR_EYE__", hat: __CHAR_HAT__
};

class SoundFX {
  constructor() { this.ctx = null; this.enabled = true; }
  ensureContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
    if (this.ctx && this.ctx.state === "suspended") this.ctx.resume();
  }
  playTone(f, ef, d, t="triangle", g=0.14, delay=0) {
    if (!this.enabled) return;
    this.ensureContext();
    if (!this.ctx) return;
    const now = this.ctx.currentTime + delay;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = t;
    osc.frequency.setValueAtTime(f, now);
    if (ef) osc.frequency.exponentialRampToValueAtTime(Math.max(40, ef), now + d);
    gain.gain.setValueAtTime(g, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + d);
    osc.connect(gain); gain.connect(this.ctx.destination);
    osc.start(now); osc.stop(now + d);
  }
  step(c) { this.playTone(340 + Math.min(350, (c % 25) * 14), 420, 0.065, "triangle", 0.12); }
  turn() { this.playTone(260, 460, 0.075, "sine", 0.12); }
  gold() { this.playTone(660, 880, 0.09, "sine", 0.16, 0); this.playTone(880, 1320, 0.14, "triangle", 0.16, 0.07); }
  gameOver() { this.playTone(300, 95, 0.35, "sawtooth", 0.15, 0); }
}

const sfx = new SoundFX();
document.getElementById("sound-toggle").addEventListener("click", (e) => {
  e.stopPropagation();
  sfx.enabled = !sfx.enabled;
  e.target.innerText = sfx.enabled ? "🔊 SFX ON" : "🔇 SFX OFF";
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

const STEP_W = 55, STEP_H = 26, STEP_ANIM_DURATION = 0.055;
let stairs = [], player = { x: 0, y: 0, dir: 1, fromX: 0, fromY: 0, toX: 0, toY: 0, animT: 1.0 };
let camera = { x: 0, y: 0 }, score = 0, timeLeft = 100, isPlaying = false, isGameOver = false, lastTime = 0, particles = [], badgeTimer = 0;
let bestScore = Number(localStorage.getItem("infinite_stairs_best") || 0);
bestEl.innerText = `BEST: ${bestScore}`;

__CHARACTER_DRAW_JS__

function showBadge(t, c="#ffd32a") { badgeEl.innerText = t; badgeEl.style.color = c; badgeTimer = 0.85; }
function createStair(x, y, idx) { return { x, y, isGold: idx > 2 && Math.random() < 0.14 }; }
function getVisualPlayerPos() {
  return {
    x: player.fromX + (player.toX - player.fromX) * Math.min(1, player.animT),
    y: player.fromY + (player.toY - player.fromY) * Math.min(1, player.animT)
  };
}
function initGame() {
  stairs = [{ x: 0, y: 0, isGold: false }];
  let curX = 0, curY = 0, dir = 1;
  for (let i = 1; i < 100; i++) {
    if (i > 1 && Math.random() < 0.35) dir *= -1;
    curX += dir; curY += 1;
    stairs.push(createStair(curX, curY, i));
  }
  player = { x: 0, y: 0, dir: 1, fromX: 0, fromY: 0, toX: 0, toY: 0, animT: 1.0 };
  camera = { x: 0, y: 0 }; score = 0; timeLeft = 100; isPlaying = true; isGameOver = false; particles = []; badgeEl.innerText = "";
  scoreEl.innerText = score; registerHint.style.display = "none"; overlay.style.display = "none"; lastTime = performance.now();
}
function addMoreStairs() {
  while (stairs.length < player.y + 50) {
    const last = stairs[stairs.length - 1], prev = stairs[stairs.length - 2];
    let dir = last.x - prev.x;
    if (Math.random() < 0.38) dir *= -1;
    stairs.push(createStair(last.x + dir, last.y + 1, stairs.length));
  }
}
function spawnParticles(x, y, color, count = 10) {
  for (let i = 0; i < count; i++) {
    particles.push({ x, y, vx: (Math.random() - 0.5) * 7, vy: (Math.random() - 0.9) * 6.5, life: 1.0, color });
  }
}
function advancePlayer(turned) {
  if (!isPlaying || isGameOver) return;
  if (turned) player.dir *= -1;
  const startVis = getVisualPlayerPos(), nextX = player.x + player.dir, nextY = player.y + 1, targetStair = stairs[nextY];
  player.fromX = startVis.x; player.fromY = startVis.y; player.toX = nextX; player.toY = nextY; player.animT = 0.0;
  if (targetStair && targetStair.x === nextX) {
    player.x = nextX; player.y = nextY;
    if (targetStair.isGold) {
      score += 3; timeLeft = Math.min(100, timeLeft + 24); sfx.gold();
      spawnParticles(canvas.width / 2, canvas.height * 0.65, "#ffd32a", 20);
      showBadge("✨ GOLD STAIR +3 & TIME UP!"); targetStair.isGold = false;
    } else {
      score += 1; timeLeft = Math.min(100, timeLeft + Math.max(8, 16 - Math.floor(score / 45)));
      if (turned) sfx.turn(); else sfx.step(score);
      spawnParticles(canvas.width / 2, canvas.height * 0.65, "#0be881", 9);
    }
    scoreEl.innerText = score; addMoreStairs();
  } else {
    player.x = nextX; player.y = nextY; triggerGameOver("발을 헛디뎠습니다!");
  }
}
function triggerGameOver(reason) {
  if (isGameOver) return;
  isGameOver = true; isPlaying = false; sfx.gameOver();
  if (score > bestScore) { bestScore = score; localStorage.setItem("infinite_stairs_best", bestScore); bestEl.innerText = `BEST: ${bestScore}`; }
  overlayTitle.innerText = "GAME OVER";
  overlayDesc.innerHTML = `${reason}<br>최종 기록: <strong style="color:#0be881; font-size:24px;">${score}점</strong>`;
  if (score > 0) {
    registerHint.style.display = "block";
    Streamlit.setComponentValue({ gameType: "stairs", runId: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`, score, characterName: CHAR_CONFIG.name });
  }
  startBtn.innerText = "다시 도전 (Space)"; overlay.style.display = "flex";
}
function update(dt) {
  if (badgeTimer > 0) { badgeTimer -= dt; if (badgeTimer <= 0) badgeEl.innerText = ""; }
  if (!isPlaying) return;
  if (player.animT < 1.0) player.animT = Math.min(1.0, player.animT + dt / STEP_ANIM_DURATION);
  timeLeft -= (18 + Math.min(45, score * 0.22)) * dt;
  if (timeLeft <= 0) { timeLeft = 0; triggerGameOver("시간이 초과되었습니다!"); }
  timerBar.style.width = `${timeLeft}%`;
  const vis = getVisualPlayerPos();
  camera.x += (vis.x * STEP_W - camera.x) * 18 * dt;
  camera.y += (vis.y * STEP_H - camera.y) * 18 * dt;
  for (let i = particles.length - 1; i >= 0; i--) {
    let p = particles[i]; p.x += p.vx; p.y += p.vy; p.vy += 0.25; p.life -= dt * 2.5;
    if (p.life <= 0) particles.splice(i, 1);
  }
}
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const centerX = canvas.width / 2, baseScreenY = canvas.height * 0.65;
  ctx.fillStyle = `rgba(10, 12, 28, ${Math.min(1, score / 300) * 0.6})`;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  for (let i = Math.max(0, player.y - 10); i < Math.min(stairs.length, player.y + 22); i++) {
    const s = stairs[i], sx = centerX + (s.x * STEP_W - camera.x), sy = baseScreenY - (s.y * STEP_H - camera.y);
    if (s.isGold) {
      ctx.fillStyle = "#b7791f"; ctx.beginPath(); ctx.roundRect(sx - 25, sy + 6, 50, 14, 5); ctx.fill();
      ctx.fillStyle = "#ffd32a"; ctx.beginPath(); ctx.roundRect(sx - 25, sy, 50, 13, 5); ctx.fill();
    } else {
      ctx.fillStyle = "#576574"; ctx.beginPath(); ctx.roundRect(sx - 24, sy + 6, 48, 14, 4); ctx.fill();
      ctx.fillStyle = (i > 0 && i % 50 === 0) ? "#ffdd59" : "#c8d6e5";
      ctx.beginPath(); ctx.roundRect(sx - 24, sy, 48, 12, 4); ctx.fill();
    }
  }
  const vis = getVisualPlayerPos();
  drawCharacter(centerX + (vis.x * STEP_W - camera.x), baseScreenY - (vis.y * STEP_H - camera.y), player.dir, player.animT < 1.0 ? Math.sin(player.animT * Math.PI) * 9 : 0);
  for (let p of particles) { ctx.globalAlpha = Math.max(0, p.life); ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(p.x, p.y, 4, 0, Math.PI * 2); ctx.fill(); }
  ctx.globalAlpha = 1.0;
}
function gameLoop(ts) {
  const dt = Math.min(0.05, (ts - lastTime) / 1000); lastTime = ts;
  update(dt); draw(); requestAnimationFrame(gameLoop);
}
window.addEventListener("keydown", (e) => {
  if (e.repeat) return;
  if (!isPlaying && (e.code === "Space" || e.code === "Enter")) { initGame(); return; }
  if (e.code === "ArrowUp" || e.code === "Space" || e.code === "KeyD") { e.preventDefault(); advancePlayer(false); }
  else if (e.code === "ArrowLeft" || e.code === "ShiftLeft" || e.code === "KeyA") { e.preventDefault(); advancePlayer(true); }
});
document.getElementById("btn-climb").addEventListener("pointerdown", (e) => { e.preventDefault(); advancePlayer(false); });
document.getElementById("btn-turn").addEventListener("pointerdown", (e) => { e.preventDefault(); advancePlayer(true); });
startBtn.addEventListener("click", initGame);
Streamlit.setComponentReady(); Streamlit.setFrameHeight(620); requestAnimationFrame(gameLoop);
</script>
</body>
</html>
"""
    return (
        template.replace("__CHARACTER_DRAW_JS__", CHARACTER_DRAW_JS)
        .replace("__CHAR_NAME__", char_data["name"])
        .replace("__CHAR_BODY__", char_data["body"])
        .replace("__CHAR_HEAD__", char_data["head"])
        .replace("__CHAR_BAND__", char_data["band"])
        .replace("__CHAR_EYE__", char_data["eye"])
        .replace("__CHAR_HAT__", hat_js)
    )


def build_one_to_50_html(char_data: dict) -> str:
    template = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; user-select: none; }
  body {
    margin: 0; padding: 0; background: transparent;
    display: flex; flex-direction: column; align-items: center;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    color: white; overflow: hidden;
  }
  #board-wrap {
    position: relative; width: 400px; height: 560px; border-radius: 16px;
    background: linear-gradient(180deg, #1b223c 0%, #252f54 100%);
    border: 3px solid #3b3e5b; box-shadow: 0 12px 32px rgba(0,0,0,0.45);
    padding: 16px; display: flex; flex-direction: column; justify-content: space-between;
  }
  .header-row { display: flex; justify-content: space-between; font-size: 13px; color: #b8c4ff; font-weight: 700; }
  .status-box {
    background: rgba(0, 0, 0, 0.28); border-radius: 12px; padding: 12px 14px;
    display: flex; justify-content: space-between; align-items: center; margin-top: 8px;
  }
  .target-label { font-size: 14px; color: #d2dae2; }
  .target-num { font-size: 32px; font-weight: 900; color: #ffdd59; }
  .timer-val { font-size: 26px; font-weight: 900; color: #0be881; font-variant-numeric: tabular-nums; }
  #grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 12px 0; flex: 1; }
  .num-btn {
    border: none; border-radius: 12px; font-size: 22px; font-weight: 900; cursor: pointer;
    color: #1e272e; background: #ffffff; box-shadow: 0 4px 0 rgba(0, 0, 0, 0.28);
  }
  .num-btn.second-wave { background: __ACCENT_LIGHT__; color: #1b1b2f; }
  .num-btn.cleared { background: rgba(255, 255, 255, 0.12); color: rgba(255, 255, 255, 0.28); box-shadow: none; cursor: default; }
  .num-btn.wrong { background: #ff5e57 !important; color: #fff !important; }
  #restart-btn {
    width: 100%; padding: 11px; border: none; border-radius: 10px;
    background: __ACCENT_COLOR__; color: #1e272e; font-size: 15px; font-weight: 800; cursor: pointer;
  }
  #result-banner {
    display: none; position: absolute; inset: 0; background: rgba(15, 17, 26, 0.92);
    border-radius: 14px; flex-direction: column; justify-content: center; align-items: center;
    text-align: center; padding: 20px; z-index: 10;
  }
  #result-banner h2 { color: #ffdd59; font-size: 28px; margin-bottom: 10px; }
  #result-banner p { color: #e2e8f0; font-size: 16px; line-height: 1.5; margin-bottom: 18px; }
  #play-again-btn {
    padding: 12px 28px; border: none; border-radius: 12px;
    background: #0be881; color: #1e272e; font-size: 17px; font-weight: 900; cursor: pointer;
  }
</style>
</head>
<body>
<div id="board-wrap">
  <div>
    <div class="header-row">
      <span id="best-time">BEST: --.-s</span>
      <span>캐릭터: __CHAR_NAME__</span>
    </div>
    <div class="status-box">
      <div><div class="target-label">다음 숫자</div><div class="target-num" id="next-target">1</div></div>
      <div style="text-align:right;"><div class="target-label">경과 시간</div><div class="timer-val" id="elapsed-time">0.00s</div></div>
    </div>
  </div>
  <div id="grid"></div>
  <button id="restart-btn">새로 섞기 / 재시작</button>
  <div id="result-banner">
    <h2>🎉 50 클리어!</h2>
    <p id="result-text"></p>
    <button id="play-again-btn">다시 도전하기</button>
  </div>
</div>
<script>
const Streamlit = {
  sendMessageToHost(t, d) { window.parent.postMessage({ isStreamlitMessage: true, type: t, ...d }, "*"); },
  setComponentReady() { this.sendMessageToHost("streamlit:componentReady", { apiVersion: 1 }); },
  setFrameHeight(h) { this.sendMessageToHost("streamlit:setFrameHeight", { height: h }); },
  setComponentValue(v) { this.sendMessageToHost("streamlit:setComponentValue", { value: v, dataType: "json" }); }
};
window.addEventListener("message", (e) => { if (e.data && e.data.type === "streamlit:render") Streamlit.setFrameHeight(580); });

const CHAR_NAME = "__CHAR_NAME__";
const gridEl = document.getElementById("grid"), nextTargetEl = document.getElementById("next-target");
const elapsedTimeEl = document.getElementById("elapsed-time"), bestTimeEl = document.getElementById("best-time");
const resultBanner = document.getElementById("result-banner"), resultText = document.getElementById("result-text");

let bestTime = Number(localStorage.getItem("one_to_50_best") || 0);
let nextNumber = 1, startTimestamp = null, isRunning = false, isFinished = false, rafId = null;

function updateBestLabel() { bestTimeEl.innerText = bestTime > 0 ? `BEST: ${bestTime.toFixed(2)}s` : "BEST: --.-s"; }
function shuffle(arr) {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [copy[i], copy[j]] = [copy[j], copy[i]]; }
  return copy;
}
function tickTimer() {
  if (isRunning && !isFinished) {
    elapsedTimeEl.innerText = `${((performance.now() - startTimestamp) / 1000).toFixed(2)}s`;
    rafId = requestAnimationFrame(tickTimer);
  }
}
function setupBoard() {
  if (rafId) cancelAnimationFrame(rafId);
  nextNumber = 1; startTimestamp = null; isRunning = false; isFinished = false;
  nextTargetEl.innerText = "1"; elapsedTimeEl.innerText = "0.00s"; resultBanner.style.display = "none"; gridEl.innerHTML = "";
  const first25 = shuffle(Array.from({ length: 25 }, (_, i) => i + 1));
  const second25 = shuffle(Array.from({ length: 25 }, (_, i) => i + 26));
  for (let i = 0; i < 25; i++) {
    const btn = document.createElement("button");
    btn.className = "num-btn"; btn.dataset.secondary = String(second25[i]); btn.dataset.stage = "1"; btn.innerText = String(first25[i]);
    btn.addEventListener("pointerdown", (e) => { e.preventDefault(); handleTileClick(btn); });
    gridEl.appendChild(btn);
  }
}
function handleTileClick(btn) {
  if (isFinished || btn.classList.contains("cleared")) return;
  if (Number(btn.innerText) === nextNumber) {
    if (nextNumber === 1 && !isRunning) { isRunning = true; startTimestamp = performance.now(); rafId = requestAnimationFrame(tickTimer); }
    if (nextNumber === 50) {
      isFinished = true; isRunning = false; if (rafId) cancelAnimationFrame(rafId);
      const finalSec = Number(((performance.now() - startTimestamp) / 1000).toFixed(2));
      elapsedTimeEl.innerText = `${finalSec.toFixed(2)}s`; btn.classList.add("cleared"); btn.innerText = "✓";
      if (bestTime === 0 || finalSec < bestTime) { bestTime = finalSec; localStorage.setItem("one_to_50_best", String(bestTime)); updateBestLabel(); }
      resultText.innerHTML = `기록: <strong style="color:#0be881; font-size:24px;">${finalSec.toFixed(2)}초</strong><br>아래 <strong>랭킹 등록</strong> 버튼을 눌러 기록을 남겨보세요!`;
      resultBanner.style.display = "flex";
      Streamlit.setComponentValue({ gameType: "one_to_50", runId: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`, clearTime: finalSec, characterName: CHAR_NAME });
      return;
    }
    nextNumber += 1; nextTargetEl.innerText = String(nextNumber);
    if (btn.dataset.stage === "1") { btn.dataset.stage = "2"; btn.innerText = btn.dataset.secondary; btn.classList.add("second-wave"); }
    else { btn.classList.add("cleared"); btn.innerText = "✓"; }
  } else {
    btn.classList.add("wrong"); setTimeout(() => btn.classList.remove("wrong"), 160);
  }
}
updateBestLabel(); setupBoard();
document.getElementById("restart-btn").addEventListener("click", setupBoard);
document.getElementById("play-again-btn").addEventListener("click", setupBoard);
Streamlit.setComponentReady(); Streamlit.setFrameHeight(580);
</script>
</body>
</html>
"""
    return template.replace("__CHAR_NAME__", char_data["name"]).replace("__ACCENT_COLOR__", char_data["body"]).replace("__ACCENT_LIGHT__", char_data["head"])


def build_timing_jump_html(char_data: dict) -> str:
    hat_js = f'"{char_data["hat"]}"' if char_data["hat"] else "null"
    template = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; user-select: none; }
  body {
    margin: 0; padding: 0; background: transparent;
    display: flex; flex-direction: column; align-items: center;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    color: white; overflow: hidden;
  }
  #game-container {
    position: relative; width: 400px; height: 580px; border-radius: 16px; overflow: hidden;
    box-shadow: 0 12px 32px rgba(0,0,0,0.45); border: 3px solid #3b3e5b;
  }
  canvas { display: block; background: linear-gradient(180deg, #1b2845 0%, #274060 65%, #2d6a4f 100%); }
  #hud {
    position: absolute; top: 14px; left: 0; width: 100%; padding: 0 18px;
    display: flex; justify-content: space-between; align-items: center; pointer-events: none;
  }
  #score-box { font-size: 36px; font-weight: 900; text-shadow: 0 3px 6px rgba(0,0,0,0.4); }
  #meta-box { text-align: right; font-size: 13px; color: #dbeafe; font-weight: 700; }
  #judgement {
    position: absolute; top: 76px; width: 100%; text-align: center;
    font-size: 18px; font-weight: 900; color: #ffd32a; pointer-events: none;
  }
  #jump-btn {
    position: absolute; bottom: 18px; left: 18px; right: 18px; height: 64px;
    border: none; border-radius: 14px; background: #ffd32a; color: #1e272e;
    font-size: 19px; font-weight: 900; cursor: pointer; box-shadow: 0 6px 0 #cca81d;
  }
  #jump-btn:active { transform: translateY(3px); box-shadow: 0 2px 0 #cca81d; }
  #overlay {
    position: absolute; inset: 0; background: rgba(15, 17, 26, 0.9);
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    text-align: center; padding: 20px; z-index: 5;
  }
  #overlay h2 { font-size: 28px; color: #ffdd59; margin-bottom: 10px; }
  #overlay p { font-size: 15px; color: #e2e8f0; line-height: 1.55; margin-bottom: 18px; }
  #start-btn {
    padding: 13px 30px; font-size: 18px; font-weight: 900; border: none;
    border-radius: 12px; background: #0be881; color: #1e272e; cursor: pointer;
  }
</style>
</head>
<body>
<div id="game-container">
  <canvas id="gameCanvas" width="400" height="580"></canvas>
  <div id="hud">
    <div id="score-box">0점</div>
    <div id="meta-box"><div id="best-lbl">BEST: 0</div><div>캐릭터: __CHAR_NAME__</div></div>
  </div>
  <div id="judgement"></div>
  <button id="jump-btn">점프! (Space / ↑)</button>
  <div id="overlay">
    <h2 id="ov-title">초집중 타이밍 점프</h2>
    <p id="ov-desc">다가오는 파동·장애물을 딱 맞춰 점프하세요!<br>정타 점프는 <strong>PERFECT +2점</strong>, 일반 통과는 <strong>+1점</strong>!</p>
    <button id="start-btn">게임 시작</button>
  </div>
</div>
<script>
const Streamlit = {
  sendMessageToHost(t, d) { window.parent.postMessage({ isStreamlitMessage: true, type: t, ...d }, "*"); },
  setComponentReady() { this.sendMessageToHost("streamlit:componentReady", { apiVersion: 1 }); },
  setFrameHeight(h) { this.sendMessageToHost("streamlit:setFrameHeight", { height: h }); },
  setComponentValue(v) { this.sendMessageToHost("streamlit:setComponentValue", { value: v, dataType: "json" }); }
};
window.addEventListener("message", (e) => { if (e.data && e.data.type === "streamlit:render") Streamlit.setFrameHeight(600); });

const CHAR_CONFIG = {
  name: "__CHAR_NAME__", body: "__CHAR_BODY__", head: "__CHAR_HEAD__",
  band: "__CHAR_BAND__", eye: "__CHAR_EYE__", hat: __CHAR_HAT__
};
const canvas = document.getElementById("gameCanvas"), ctx = canvas.getContext("2d");
const scoreBox = document.getElementById("score-box"), bestLbl = document.getElementById("best-lbl");
const judgementEl = document.getElementById("judgement"), overlay = document.getElementById("overlay");
const ovTitle = document.getElementById("ov-title"), ovDesc = document.getElementById("ov-desc");

const GROUND_Y = 450, PLAYER_X = 95;
let bestScore = Number(localStorage.getItem("timing_jump_best") || 0);
let score = 0, isPlaying = false, lastTime = 0, judgeTimer = 0;
let player = { y: GROUND_Y, vy: 0, isGrounded: true, hopPhase: 0 };
let obstacles = [], spawnCooldown = 1.1;
bestLbl.innerText = `BEST: ${bestScore}`;

__CHARACTER_DRAW_JS__

function showJudge(txt, col="#ffd32a") { judgementEl.innerText = txt; judgementEl.style.color = col; judgeTimer = 0.65; }
function startGame() {
  score = 0; isPlaying = true; obstacles = []; spawnCooldown = 0.8;
  player = { y: GROUND_Y, vy: 0, isGrounded: true, hopPhase: 0 };
  scoreBox.innerText = "0점"; overlay.style.display = "none"; lastTime = performance.now();
}
function triggerJump() {
  if (!isPlaying) return;
  if (player.isGrounded) {
    player.vy = -560; player.isGrounded = false;
  }
}
function gameOver() {
  isPlaying = false;
  if (score > bestScore) { bestScore = score; localStorage.setItem("timing_jump_best", bestScore); bestLbl.innerText = `BEST: ${bestScore}`; }
  ovTitle.innerText = "GAME OVER";
  ovDesc.innerHTML = `장애물에 걸렸습니다!<br>최종 기록: <strong style="color:#ffd32a; font-size:24px;">${score}점</strong><br><small>아래 랭킹 등록 버튼을 눌러 기록을 남기세요.</small>`;
  overlay.style.display = "flex";
  if (score > 0) {
    Streamlit.setComponentValue({ gameType: "timing_jump", runId: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`, score, characterName: CHAR_CONFIG.name });
  }
}
function update(dt) {
  if (judgeTimer > 0) { judgeTimer -= dt; if (judgeTimer <= 0) judgementEl.innerText = ""; }
  if (!isPlaying) return;
  if (!player.isGrounded) {
    player.vy += 1550 * dt; player.y += player.vy * dt;
    if (player.y >= GROUND_Y) { player.y = GROUND_Y; player.vy = 0; player.isGrounded = true; }
  } else {
    player.hopPhase += dt * 12;
  }
  const speed = 250 + Math.min(240, score * 6);
  spawnCooldown -= dt;
  if (spawnCooldown <= 0) {
    const tall = Math.random() < 0.35;
    obstacles.push({ x: canvas.width + 20, w: tall ? 24 : 30, h: tall ? 44 : 28, scored: false });
    spawnCooldown = Math.max(0.68, 1.35 - Math.min(0.55, score * 0.015));
  }
  for (let i = obstacles.length - 1; i >= 0; i--) {
    const ob = obstacles[i]; ob.x -= speed * dt;
    const pLeft = PLAYER_X - 11, pRight = PLAYER_X + 11, pBottom = player.y, pTop = player.y - 34;
    const oLeft = ob.x - ob.w / 2, oRight = ob.x + ob.w / 2, oTop = GROUND_Y - ob.h;
    if (pRight > oLeft && pLeft < oRight && pBottom > oTop && pTop < GROUND_Y) { gameOver(); return; }
    if (!ob.scored && oRight < pLeft) {
      ob.scored = true;
      const clearance = GROUND_Y - player.y;
      if (clearance > 18 && clearance < 72) { score += 2; showJudge("✨ PERFECT +2!", "#0be881"); }
      else { score += 1; showJudge("+1", "#ffd32a"); }
      scoreBox.innerText = `${score}점`;
    }
    if (ob.x < -50) obstacles.splice(i, 1);
  }
}
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#14532d"; ctx.fillRect(0, GROUND_Y, canvas.width, canvas.height - GROUND_Y);
  ctx.fillStyle = "#4ade80"; ctx.fillRect(0, GROUND_Y, canvas.width, 5);
  for (const ob of obstacles) {
    ctx.fillStyle = "#ff5e57"; ctx.beginPath(); ctx.roundRect(ob.x - ob.w / 2, GROUND_Y - ob.h, ob.w, ob.h, 6); ctx.fill();
    ctx.fillStyle = "#ffd32a"; ctx.beginPath(); ctx.arc(ob.x, GROUND_Y - ob.h + 9, 4, 0, Math.PI * 2); ctx.fill();
  }
  const idleHop = player.isGrounded ? Math.abs(Math.sin(player.hopPhase)) * 3 : 0;
  drawCharacter(PLAYER_X, player.y, 1, idleHop);
}
function gameLoop(ts) {
  const dt = Math.min(0.05, (ts - lastTime) / 1000); lastTime = ts;
  update(dt); draw(); requestAnimationFrame(gameLoop);
}
window.addEventListener("keydown", (e) => {
  if (e.repeat) return;
  if (!isPlaying && (e.code === "Space" || e.code === "Enter")) { startGame(); return; }
  if (e.code === "Space" || e.code === "ArrowUp") { e.preventDefault(); triggerJump(); }
});
document.getElementById("jump-btn").addEventListener("pointerdown", (e) => { e.preventDefault(); triggerJump(); });
document.getElementById("start-btn").addEventListener("click", startGame);
Streamlit.setComponentReady(); Streamlit.setFrameHeight(600); requestAnimationFrame(gameLoop);
</script>
</body>
</html>
"""
    return (
        template.replace("__CHARACTER_DRAW_JS__", CHARACTER_DRAW_JS)
        .replace("__CHAR_NAME__", char_data["name"])
        .replace("__CHAR_BODY__", char_data["body"])
        .replace("__CHAR_HEAD__", char_data["head"])
        .replace("__CHAR_BAND__", char_data["band"])
        .replace("__CHAR_EYE__", char_data["eye"])
        .replace("__CHAR_HAT__", hat_js)
    )


def build_dodge_drop_html(char_data: dict) -> str:
    hat_js = f'"{char_data["hat"]}"' if char_data["hat"] else "null"
    template = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; user-select: none; }
  body {
    margin: 0; padding: 0; background: transparent;
    display: flex; flex-direction: column; align-items: center;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    color: white; overflow: hidden;
  }
  #game-container {
    position: relative; width: 400px; height: 580px; border-radius: 16px; overflow: hidden;
    box-shadow: 0 12px 32px rgba(0,0,0,0.45); border: 3px solid #3b3e5b;
  }
  canvas { display: block; background: linear-gradient(180deg, #1d1e3a 0%, #2d234a 100%); }
  #hud {
    position: absolute; top: 14px; left: 0; width: 100%; padding: 0 18px;
    display: flex; justify-content: space-between; pointer-events: none;
  }
  #score-box { font-size: 36px; font-weight: 900; color: #0be881; }
  #meta-box { text-align: right; font-size: 13px; color: #e2e8f0; font-weight: 700; }
  #controls {
    position: absolute; bottom: 18px; left: 18px; right: 18px;
    display: flex; gap: 12px;
  }
  .move-btn {
    flex: 1; height: 62px; border: none; border-radius: 14px;
    font-size: 18px; font-weight: 900; color: #1e272e; cursor: pointer;
    box-shadow: 0 5px 0 rgba(0,0,0,0.3);
  }
  #btn-left { background: #ffdd59; }
  #btn-right { background: #0be881; }
  #overlay {
    position: absolute; inset: 0; background: rgba(15, 17, 26, 0.9);
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    text-align: center; padding: 20px; z-index: 5;
  }
  #overlay h2 { font-size: 28px; color: #ffdd59; margin-bottom: 10px; }
  #overlay p { font-size: 15px; color: #e2e8f0; line-height: 1.55; margin-bottom: 18px; }
  #start-btn {
    padding: 13px 30px; font-size: 18px; font-weight: 900; border: none;
    border-radius: 12px; background: #ff5e57; color: white; cursor: pointer;
  }
</style>
</head>
<body>
<div id="game-container">
  <canvas id="gameCanvas" width="400" height="580"></canvas>
  <div id="hud">
    <div id="score-box">0점</div>
    <div id="meta-box"><div id="best-lbl">BEST: 0</div><div>캐릭터: __CHAR_NAME__</div></div>
  </div>
  <div id="controls">
    <button class="move-btn" id="btn-left">◀ 왼쪽 (← / A)</button>
    <button class="move-btn" id="btn-right">오른쪽 (→ / D) ▶</button>
  </div>
  <div id="overlay">
    <h2 id="ov-title">하늘에서 떨어지는 폭탄 피하기</h2>
    <p id="ov-desc">위에서 떨어지는 빨간 폭탄을 피하세요!<br>폭탄을 1개 피할 때마다 <strong>+1점</strong>이 쌓입니다.</p>
    <button id="start-btn">게임 시작</button>
  </div>
</div>
<script>
const Streamlit = {
  sendMessageToHost(t, d) { window.parent.postMessage({ isStreamlitMessage: true, type: t, ...d }, "*"); },
  setComponentReady() { this.sendMessageToHost("streamlit:componentReady", { apiVersion: 1 }); },
  setFrameHeight(h) { this.sendMessageToHost("streamlit:setFrameHeight", { height: h }); },
  setComponentValue(v) { this.sendMessageToHost("streamlit:setComponentValue", { value: v, dataType: "json" }); }
};
window.addEventListener("message", (e) => { if (e.data && e.data.type === "streamlit:render") Streamlit.setFrameHeight(600); });

const CHAR_CONFIG = {
  name: "__CHAR_NAME__", body: "__CHAR_BODY__", head: "__CHAR_HEAD__",
  band: "__CHAR_BAND__", eye: "__CHAR_EYE__", hat: __CHAR_HAT__
};
const canvas = document.getElementById("gameCanvas"), ctx = canvas.getContext("2d");
const scoreBox = document.getElementById("score-box"), bestLbl = document.getElementById("best-lbl");
const overlay = document.getElementById("overlay"), ovTitle = document.getElementById("ov-title"), ovDesc = document.getElementById("ov-desc");

const FLOOR_Y = 475;
let bestScore = Number(localStorage.getItem("dodge_drop_best") || 0);
let score = 0, isPlaying = false, lastTime = 0, spawnTimer = 0.5;
let px = 200, dir = 1, moveLeft = false, moveRight = false, bombs = [];
bestLbl.innerText = `BEST: ${bestScore}`;

__CHARACTER_DRAW_JS__

function startGame() {
  score = 0; isPlaying = true; bombs = []; spawnTimer = 0.4; px = 200; dir = 1;
  scoreBox.innerText = "0점"; overlay.style.display = "none"; lastTime = performance.now();
}
function gameOver() {
  isPlaying = false;
  if (score > bestScore) { bestScore = score; localStorage.setItem("dodge_drop_best", bestScore); bestLbl.innerText = `BEST: ${bestScore}`; }
  ovTitle.innerText = "꽝! GAME OVER";
  ovDesc.innerHTML = `폭탄에 맞았습니다!<br>최종 기록: <strong style="color:#0be881; font-size:24px;">${score}점</strong><br><small>아래 랭킹 등록 버튼을 눌러 기록을 남기세요.</small>`;
  overlay.style.display = "flex";
  if (score > 0) {
    Streamlit.setComponentValue({ gameType: "dodge_drop", runId: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`, score, characterName: CHAR_CONFIG.name });
  }
}
function update(dt) {
  if (!isPlaying) return;
  const moveSpeed = 270;
  if (moveLeft) { px -= moveSpeed * dt; dir = -1; }
  if (moveRight) { px += moveSpeed * dt; dir = 1; }
  px = Math.max(24, Math.min(canvas.width - 24, px));

  spawnTimer -= dt;
  if (spawnTimer <= 0) {
    const count = score > 35 && Math.random() < 0.35 ? 2 : 1;
    for (let c = 0; c < count; c++) {
      bombs.push({ x: 26 + Math.random() * (canvas.width - 52), y: -20 - c * 28, r: 13, vy: 210 + Math.min(280, score * 4.5) + Math.random() * 60 });
    }
    spawnTimer = Math.max(0.28, 0.72 - Math.min(0.38, score * 0.008));
  }

  for (let i = bombs.length - 1; i >= 0; i--) {
    const b = bombs[i]; b.y += b.vy * dt;
    const dx = b.x - px, dy = b.y - (FLOOR_Y - 22);
    if (Math.hypot(dx, dy) < b.r + 14) { gameOver(); return; }
    if (b.y > FLOOR_Y + 6) {
      score += 1; scoreBox.innerText = `${score}점`; bombs.splice(i, 1);
    }
  }
}
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#3b3561"; ctx.fillRect(0, FLOOR_Y, canvas.width, canvas.height - FLOOR_Y);
  ctx.fillStyle = "#a78bfa"; ctx.fillRect(0, FLOOR_Y, canvas.width, 4);
  for (const b of bombs) {
    ctx.fillStyle = "#ff4757"; ctx.beginPath(); ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#ffd32a"; ctx.beginPath(); ctx.arc(b.x - 4, b.y - 4, 3.5, 0, Math.PI * 2); ctx.fill();
  }
  drawCharacter(px, FLOOR_Y, dir, 0);
}
function gameLoop(ts) {
  const dt = Math.min(0.05, (ts - lastTime) / 1000); lastTime = ts;
  update(dt); draw(); requestAnimationFrame(gameLoop);
}
window.addEventListener("keydown", (e) => {
  if (!isPlaying && (e.code === "Space" || e.code === "Enter")) { startGame(); return; }
  if (e.code === "ArrowLeft" || e.code === "KeyA") moveLeft = true;
  if (e.code === "ArrowRight" || e.code === "KeyD") moveRight = true;
});
window.addEventListener("keyup", (e) => {
  if (e.code === "ArrowLeft" || e.code === "KeyA") moveLeft = false;
  if (e.code === "ArrowRight" || e.code === "KeyD") moveRight = false;
});
const bLeft = document.getElementById("btn-left"), bRight = document.getElementById("btn-right");
bLeft.addEventListener("pointerdown", (e) => { e.preventDefault(); moveLeft = true; dir = -1; });
bLeft.addEventListener("pointerup", () => { moveLeft = false; });
bLeft.addEventListener("pointerleave", () => { moveLeft = false; });
bRight.addEventListener("pointerdown", (e) => { e.preventDefault(); moveRight = true; dir = 1; });
bRight.addEventListener("pointerup", () => { moveRight = false; });
bRight.addEventListener("pointerleave", () => { moveRight = false; });
document.getElementById("start-btn").addEventListener("click", startGame);
Streamlit.setComponentReady(); Streamlit.setFrameHeight(600); requestAnimationFrame(gameLoop);
</script>
</body>
</html>
"""
    return (
        template.replace("__CHARACTER_DRAW_JS__", CHARACTER_DRAW_JS)
        .replace("__CHAR_NAME__", char_data["name"])
        .replace("__CHAR_BODY__", char_data["body"])
        .replace("__CHAR_HEAD__", char_data["head"])
        .replace("__CHAR_BAND__", char_data["band"])
        .replace("__CHAR_EYE__", char_data["eye"])
        .replace("__CHAR_HAT__", hat_js)
    )


init_db()

if "flash_message" in st.session_state and st.session_state["flash_message"]:
    st.success(st.session_state.pop("flash_message"))

st.title("🎮 조카들 미니게임 아케이드")

selected_game = st.radio(
    "게임 선택",
    options=["stairs", "one_to_50", "timing_jump", "dodge_drop"],
    format_func=lambda g: {
        "stairs": "1️⃣ 무한의 계단",
        "one_to_50": "2️⃣ 1 to 50",
        "timing_jump": "3️⃣ 초집중 점프",
        "dodge_drop": "4️⃣ 폭탄 피하기",
    }[g],
    horizontal=True,
)

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

if selected_game == "stairs":
    st.caption("조작법: [↑ / Space / D / 오르기 버튼] 등반 | [← / Shift / A / 방향전환 버튼] 방향 전환 + 등반")
    html_path = FRONTEND_DIR / "index.html"
    html_path.write_text(build_stairs_html(char_data), encoding="utf-8")
    comp = components.declare_component("infinite_stairs_game", path=str(FRONTEND_DIR))
    val = comp(characterName=char_data["name"], key=f"stairs_comp_{selected_char_key}", default=None)

    if isinstance(val, dict) and val.get("gameType") == "stairs":
        run_id = val.get("runId")
        reported_score = val.get("score")
        reported_char = val.get("characterName", char_data["name"])
        if run_id and run_id != st.session_state.get("last_stairs_run_id"):
            st.session_state["last_stairs_run_id"] = run_id
            if isinstance(reported_score, (int, float)) and int(reported_score) > 0:
                st.session_state["pending_stairs_score"] = int(reported_score)
                st.session_state["pending_stairs_char"] = str(reported_char)

    pending_score = st.session_state.get("pending_stairs_score")
    pending_char = st.session_state.get("pending_stairs_char", char_data["name"])

    with st.container(border=True):
        st.markdown("### 📝 무한의 계단 랭킹 등록")
        if pending_score and pending_score > 0:
            can_msg = qualifies_for_top10("stairs", pending_score)
            st.info(f"방금 종료된 기록: **{pending_score}점** ({pending_char})")
            if can_msg:
                rank_message = st.text_input(
                    "🌟 TOP 10 진입 축하 메시지 (선택 · 최대 30자)",
                    value=st.session_state.get("last_stairs_msg", ""),
                    max_chars=30,
                    key=f"stairs_msg_{st.session_state.get('last_stairs_run_id', 'default')}",
                )
                st.session_state["last_stairs_msg"] = rank_message
            else:
                rank_message = ""
                st.caption("10위권 점수일 때만 메시지를 남길 수 있습니다.")
            if st.button(f"🏆 {pending_score}점 랭킹 등록 & 새로고침", type="primary", use_container_width=True):
                if save_score_game("stairs", nickname, pending_score, pending_char, rank_message):
                    st.session_state["pending_stairs_score"] = None
                    st.session_state["last_stairs_msg"] = ""
                    st.session_state["flash_message"] = f"🏆 '{(nickname or '익명').strip()[:16] or '익명'}' 님의 {pending_score}점 기록이 등록되었습니다!"
                st.rerun()
        else:
            st.caption("게임 오버 후 점수가 전달되면 이곳에서 랭킹을 등록할 수 있습니다.")

    st.divider()
    st.subheader("🏆 무한의 계단 랭킹 보드 (TOP 10)")
    top_rows = get_top_rankings("stairs", 10)
    if top_rows:
        st.dataframe(
            [{"순위": i, "닉네임": r[0], "점수": r[1], "캐릭터": r[2], "한마디": r[3], "기록 일시": r[4]} for i, r in enumerate(top_rows, 1)],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("아직 등록된 기록이 없습니다.")

elif selected_game == "one_to_50":
    st.caption("조작법: [1]을 누르면 타이머 시작! [1]부터 [50]까지 순서대로 빠르게 터치/클릭하세요.")
    sub_dir = FRONTEND_DIR / "one_to_50"
    sub_dir.mkdir(exist_ok=True)
    (sub_dir / "index.html").write_text(build_one_to_50_html(char_data), encoding="utf-8")
    comp = components.declare_component("one_to_50_game", path=str(sub_dir))
    val = comp(characterName=char_data["name"], key=f"one50_comp_{selected_char_key}", default=None)

    if isinstance(val, dict) and val.get("gameType") == "one_to_50":
        run_id = val.get("runId")
        reported_time = val.get("clearTime")
        reported_char = val.get("characterName", char_data["name"])
        if run_id and run_id != st.session_state.get("last_50_run_id"):
            st.session_state["last_50_run_id"] = run_id
            if isinstance(reported_time, (int, float)) and float(reported_time) > 0:
                st.session_state["pending_50_time"] = round(float(reported_time), 2)
                st.session_state["pending_50_char"] = str(reported_char)

    pending_time = st.session_state.get("pending_50_time")
    pending_50_char = st.session_state.get("pending_50_char", char_data["name"])

    with st.container(border=True):
        st.markdown("### 📝 1 to 50 랭킹 등록")
        if pending_time and pending_time > 0:
            can_msg = qualifies_for_top10("one_to_50", pending_time)
            st.info(f"방금 클리어한 기록: **{pending_time:.2f}초** ({pending_50_char})")
            if can_msg:
                rank_message = st.text_input(
                    "🌟 TOP 10 진입 축하 메시지 (선택 · 최대 30자)",
                    value=st.session_state.get("last_50_msg", ""),
                    max_chars=30,
                    key=f"fifty_msg_{st.session_state.get('last_50_run_id', 'default')}",
                )
                st.session_state["last_50_msg"] = rank_message
            else:
                rank_message = ""
                st.caption("10위권 기록일 때만 메시지를 남길 수 있습니다.")
            if st.button(f"🏆 {pending_time:.2f}초 랭킹 등록 & 새로고침", type="primary", use_container_width=True):
                if save_one_to_50_score(nickname, pending_time, pending_50_char, rank_message):
                    st.session_state["pending_50_time"] = None
                    st.session_state["last_50_msg"] = ""
                    st.session_state["flash_message"] = f"🏆 '{(nickname or '익명').strip()[:16] or '익명'}' 님의 {pending_time:.2f}초 기록이 등록되었습니다!"
                st.rerun()
        else:
            st.caption("50까지 클리어하면 시간이 전달되며 이곳에서 등록할 수 있습니다.")

    st.divider()
    st.subheader("⏱️ 1 to 50 랭킹 보드 (TOP 10 · 빠른 순)")
    top_50 = get_top_rankings("one_to_50", 10)
    if top_50:
        st.dataframe(
            [{"순위": i, "닉네임": r[0], "기록(초)": f"{float(r[1]):.2f}s", "캐릭터": r[2], "한마디": r[3], "기록 일시": r[4]} for i, r in enumerate(top_50, 1)],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("아직 50 클리어 기록이 없습니다.")

elif selected_game == "timing_jump":
    st.caption("조작법: [Space / ↑ / 점프 버튼]으로 다가오는 장애물을 뛰어넘으세요!")
    sub_dir = FRONTEND_DIR / "timing_jump"
    sub_dir.mkdir(exist_ok=True)
    (sub_dir / "index.html").write_text(build_timing_jump_html(char_data), encoding="utf-8")
    comp = components.declare_component("timing_jump_game", path=str(sub_dir))
    val = comp(characterName=char_data["name"], key=f"jump_comp_{selected_char_key}", default=None)

    if isinstance(val, dict) and val.get("gameType") == "timing_jump":
        run_id = val.get("runId")
        reported_score = val.get("score")
        reported_char = val.get("characterName", char_data["name"])
        if run_id and run_id != st.session_state.get("last_jump_run_id"):
            st.session_state["last_jump_run_id"] = run_id
            if isinstance(reported_score, (int, float)) and int(reported_score) > 0:
                st.session_state["pending_jump_score"] = int(reported_score)
                st.session_state["pending_jump_char"] = str(reported_char)

    pending_score = st.session_state.get("pending_jump_score")
    pending_char = st.session_state.get("pending_jump_char", char_data["name"])

    with st.container(border=True):
        st.markdown("### 📝 초집중 점프 랭킹 등록")
        if pending_score and pending_score > 0:
            can_msg = qualifies_for_top10("timing_jump", pending_score)
            st.info(f"방금 종료된 기록: **{pending_score}점** ({pending_char})")
            if can_msg:
                rank_message = st.text_input(
                    "🌟 TOP 10 진입 축하 메시지 (선택 · 최대 30자)",
                    value=st.session_state.get("last_jump_msg", ""),
                    max_chars=30,
                    key=f"jump_msg_{st.session_state.get('last_jump_run_id', 'default')}",
                )
                st.session_state["last_jump_msg"] = rank_message
            else:
                rank_message = ""
                st.caption("10위권 점수일 때만 메시지를 남길 수 있습니다.")
            if st.button(f"🏆 {pending_score}점 랭킹 등록 & 새로고침", type="primary", use_container_width=True):
                if save_score_game("timing_jump", nickname, pending_score, pending_char, rank_message):
                    st.session_state["pending_jump_score"] = None
                    st.session_state["last_jump_msg"] = ""
                    st.session_state["flash_message"] = f"🏆 '{(nickname or '익명').strip()[:16] or '익명'}' 님의 {pending_score}점 기록이 등록되었습니다!"
                st.rerun()
        else:
            st.caption("게임 오버 후 점수가 전달되면 이곳에서 랭킹을 등록할 수 있습니다.")

    st.divider()
    st.subheader("🏆 초집중 점프 랭킹 보드 (TOP 10)")
    top_jump = get_top_rankings("timing_jump", 10)
    if top_jump:
        st.dataframe(
            [{"순위": i, "닉네임": r[0], "점수": r[1], "캐릭터": r[2], "한마디": r[3], "기록 일시": r[4]} for i, r in enumerate(top_jump, 1)],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("아직 등록된 기록이 없습니다.")

else:
    st.caption("조작법: [← / → / A / D / 좌우 버튼]으로 떨어지는 폭탄을 피하세요!")
    sub_dir = FRONTEND_DIR / "dodge_drop"
    sub_dir.mkdir(exist_ok=True)
    (sub_dir / "index.html").write_text(build_dodge_drop_html(char_data), encoding="utf-8")
    comp = components.declare_component("dodge_drop_game", path=str(sub_dir))
    val = comp(characterName=char_data["name"], key=f"dodge_comp_{selected_char_key}", default=None)

    if isinstance(val, dict) and val.get("gameType") == "dodge_drop":
        run_id = val.get("runId")
        reported_score = val.get("score")
        reported_char = val.get("characterName", char_data["name"])
        if run_id and run_id != st.session_state.get("last_dodge_run_id"):
            st.session_state["last_dodge_run_id"] = run_id
            if isinstance(reported_score, (int, float)) and int(reported_score) > 0:
                st.session_state["pending_dodge_score"] = int(reported_score)
                st.session_state["pending_dodge_char"] = str(reported_char)

    pending_score = st.session_state.get("pending_dodge_score")
    pending_char = st.session_state.get("pending_dodge_char", char_data["name"])

    with st.container(border=True):
        st.markdown("### 📝 폭탄 피하기 랭킹 등록")
        if pending_score and pending_score > 0:
            can_msg = qualifies_for_top10("dodge_drop", pending_score)
            st.info(f"방금 종료된 기록: **{pending_score}점** ({pending_char})")
            if can_msg:
                rank_message = st.text_input(
                    "🌟 TOP 10 진입 축하 메시지 (선택 · 최대 30자)",
                    value=st.session_state.get("last_dodge_msg", ""),
                    max_chars=30,
                    key=f"dodge_msg_{st.session_state.get('last_dodge_run_id', 'default')}",
                )
                st.session_state["last_dodge_msg"] = rank_message
            else:
                rank_message = ""
                st.caption("10위권 점수일 때만 메시지를 남길 수 있습니다.")
            if st.button(f"🏆 {pending_score}점 랭킹 등록 & 새로고침", type="primary", use_container_width=True):
                if save_score_game("dodge_drop", nickname, pending_score, pending_char, rank_message):
                    st.session_state["pending_dodge_score"] = None
                    st.session_state["last_dodge_msg"] = ""
                    st.session_state["flash_message"] = f"🏆 '{(nickname or '익명').strip()[:16] or '익명'}' 님의 {pending_score}점 기록이 등록되었습니다!"
                st.rerun()
        else:
            st.caption("게임 오버 후 점수가 전달되면 이곳에서 랭킹을 등록할 수 있습니다.")

    st.divider()
    st.subheader("🏆 폭탄 피하기 랭킹 보드 (TOP 10)")
    top_dodge = get_top_rankings("dodge_drop", 10)
    if top_dodge:
        st.dataframe(
            [{"순위": i, "닉네임": r[0], "점수": r[1], "캐릭터": r[2], "한마디": r[3], "기록 일시": r[4]} for i, r in enumerate(top_dodge, 1)],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("아직 등록된 기록이 없습니다.")
