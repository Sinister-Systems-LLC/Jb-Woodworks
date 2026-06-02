// Author: RKOJ-ELENO :: 2026-06-01
// v2: Chrome-style dino runner, JBW-themed. Pure canvas, no deps.
// Player: pixel dino. Obstacles: sawhorses (jump), planks (duck).
"use client";
import { useEffect, useRef, useState } from "react";

const W = 760;
const H = 220;
const GROUND_Y = 180;
const GRAV = 0.6;
const JUMP_V = -12;

type Obstacle = { x: number; w: number; h: number; y: number; kind: "horse" | "plank" };

export function DinoGame() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [score, setScore] = useState(0);
  const [hi, setHi] = useState(0);
  const [running, setRunning] = useState(false);
  const [dead, setDead] = useState(false);

  useEffect(() => {
    try {
      const v = localStorage.getItem("jbw-dino-hi");
      if (v) setHi(parseInt(v, 10) || 0);
    } catch {}
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let last = performance.now();
    let dino = { x: 60, y: GROUND_Y - 40, w: 36, h: 40, vy: 0, ducking: false, alive: true };
    const obstacles: Obstacle[] = [];
    let spawnTimer = 80;
    let speed = 6;
    let s = 0;
    let aliveLocal = true;
    let pressedJump = false;
    let pressedDuck = false;

    function reset() {
      dino = { x: 60, y: GROUND_Y - 40, w: 36, h: 40, vy: 0, ducking: false, alive: true };
      obstacles.length = 0;
      spawnTimer = 80;
      speed = 6;
      s = 0;
      aliveLocal = true;
    }

    function spawn() {
      const isPlank = Math.random() < 0.3;
      if (isPlank) {
        obstacles.push({ x: W + 20, w: 60, h: 12, y: GROUND_Y - 60, kind: "plank" });
      } else {
        const tall = Math.random() < 0.5;
        obstacles.push({ x: W + 20, w: tall ? 22 : 30, h: tall ? 40 : 28, y: GROUND_Y - (tall ? 40 : 28), kind: "horse" });
      }
    }

    function rect(x: number, y: number, w: number, h: number, color: string) {
      ctx.fillStyle = color;
      ctx.fillRect(x, y, w, h);
    }

    function drawDino() {
      // body
      const body = dino.ducking ? { x: dino.x, y: GROUND_Y - 22, w: 46, h: 22 } : { x: dino.x, y: dino.y, w: dino.w, h: dino.h };
      rect(body.x, body.y, body.w, body.h, "#c9a84c");
      // head
      if (!dino.ducking) rect(body.x + 22, body.y - 12, 18, 18, "#e2c47a");
      // eye
      rect(body.x + (dino.ducking ? 32 : 32), body.y - (dino.ducking ? 4 : 8), 3, 3, "#080808");
      // legs running
      const phase = Math.floor(s / 6) % 2;
      rect(body.x + 4, body.y + body.h, 6, phase ? 6 : 4, "#a8842f");
      rect(body.x + 18, body.y + body.h, 6, phase ? 4 : 6, "#a8842f");
    }

    function drawObstacle(o: Obstacle) {
      if (o.kind === "horse") {
        // sawhorse: top beam + two legs
        rect(o.x, o.y, o.w, 6, "#a8842f");
        rect(o.x + 2, o.y + 6, 4, o.h - 6, "#a8842f");
        rect(o.x + o.w - 6, o.y + 6, 4, o.h - 6, "#a8842f");
      } else {
        // plank suspended
        rect(o.x, o.y, o.w, o.h, "#3a7ca5");
        rect(o.x + o.w / 2 - 1, o.y - 12, 2, 12, "#7aa9c7");
      }
    }

    function collide(a: { x: number; y: number; w: number; h: number }, b: { x: number; y: number; w: number; h: number }) {
      return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
    }

    function loop(t: number) {
      const dt = Math.min(32, t - last);
      last = t;
      ctx.clearRect(0, 0, W, H);

      // sky
      const grad = ctx.createLinearGradient(0, 0, 0, H);
      grad.addColorStop(0, "#0f0f0f");
      grad.addColorStop(1, "#1a1a1a");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, W, H);

      // ground line
      ctx.strokeStyle = "#3a7ca5";
      ctx.beginPath();
      ctx.moveTo(0, GROUND_Y + 1);
      ctx.lineTo(W, GROUND_Y + 1);
      ctx.stroke();

      if (!aliveLocal) {
        ctx.fillStyle = "#fff";
        ctx.font = "bold 22px ui-monospace, monospace";
        ctx.fillText("GAME OVER", W / 2 - 64, H / 2 - 6);
        ctx.font = "12px ui-monospace, monospace";
        ctx.fillStyle = "#c9a84c";
        ctx.fillText("Press space or tap to restart", W / 2 - 96, H / 2 + 16);
        drawDino();
        for (const o of obstacles) drawObstacle(o);
        raf = requestAnimationFrame(loop);
        return;
      }

      // dino physics
      if (pressedJump && dino.y >= GROUND_Y - dino.h) {
        dino.vy = JUMP_V;
      }
      dino.ducking = pressedDuck && dino.y >= GROUND_Y - dino.h;
      dino.vy += GRAV;
      dino.y += dino.vy;
      if (dino.y > GROUND_Y - dino.h) {
        dino.y = GROUND_Y - dino.h;
        dino.vy = 0;
      }

      // spawn
      spawnTimer -= dt * 0.06;
      if (spawnTimer <= 0) {
        spawn();
        spawnTimer = 70 + Math.random() * 50;
      }

      // move obstacles
      for (let i = obstacles.length - 1; i >= 0; i--) {
        obstacles[i].x -= speed;
        if (obstacles[i].x + obstacles[i].w < 0) obstacles.splice(i, 1);
      }

      // collision
      const dBox = dino.ducking
        ? { x: dino.x, y: GROUND_Y - 22, w: 46, h: 22 }
        : { x: dino.x + 4, y: dino.y - 8, w: dino.w + 14, h: dino.h + 8 };
      for (const o of obstacles) {
        if (collide(dBox, { x: o.x, y: o.y, w: o.w, h: o.h })) {
          aliveLocal = false;
          setDead(true);
          setScore(Math.floor(s / 6));
          try {
            const hiv = Math.max(hi, Math.floor(s / 6));
            localStorage.setItem("jbw-dino-hi", String(hiv));
            setHi(hiv);
          } catch {}
        }
      }

      // draw
      drawDino();
      for (const o of obstacles) drawObstacle(o);

      // hud
      ctx.fillStyle = "#fff";
      ctx.font = "bold 14px ui-monospace, monospace";
      ctx.fillText("SCORE " + String(Math.floor(s / 6)).padStart(5, "0"), W - 160, 24);
      ctx.fillStyle = "#c9a84c";
      ctx.fillText("HI " + String(hi).padStart(5, "0"), W - 280, 24);

      s += dt * 0.4;
      speed = 6 + Math.min(8, s / 400);

      raf = requestAnimationFrame(loop);
    }

    function onKey(e: KeyboardEvent) {
      if (e.code === "Space" || e.code === "ArrowUp") {
        e.preventDefault();
        if (!aliveLocal) { reset(); setDead(false); return; }
        pressedJump = true;
        setRunning(true);
      } else if (e.code === "ArrowDown") {
        e.preventDefault();
        pressedDuck = true;
      }
    }
    function onKeyUp(e: KeyboardEvent) {
      if (e.code === "Space" || e.code === "ArrowUp") pressedJump = false;
      if (e.code === "ArrowDown") pressedDuck = false;
    }
    function onTouch() {
      if (!aliveLocal) { reset(); setDead(false); return; }
      pressedJump = true;
      setRunning(true);
      setTimeout(() => { pressedJump = false; }, 120);
    }

    window.addEventListener("keydown", onKey);
    window.addEventListener("keyup", onKeyUp);
    canvas.addEventListener("touchstart", onTouch);
    canvas.addEventListener("mousedown", onTouch);

    raf = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("keyup", onKeyUp);
      canvas.removeEventListener("touchstart", onTouch);
      canvas.removeEventListener("mousedown", onTouch);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="max-w-[780px]">
      <canvas
        ref={canvasRef}
        width={W}
        height={H}
        className="w-full h-auto rounded-lg border border-line bg-ink-2 touch-manipulation"
        aria-label="Endless runner game. Press space to jump, down to duck."
        role="img"
      />
      <p className="mt-4 text-cream-30 text-[0.78rem]">
        {running ? null : "Press space, up-arrow, or tap to start."}
        {dead ? ` Last score: ${score}. Best: ${hi}.` : null}
      </p>
    </div>
  );
}
