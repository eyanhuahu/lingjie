/* 灵界 wiki —— 鼠标拖尾特效
 *
 * 六种中式修仙元素混在一个画布上，按「谁该常出现、谁该偶尔出现」分配权重：
 *   ① 灵气星辉  随时都有 —— 会呼吸的金青色光点 + 细十字光芒
 *   ② 水墨飞白  跟着移动 —— 深青墨点带一点飞白尾迹，很淡
 *   ③ 剑意拖尾  快速移动才甩 —— 青白剑芒拉长淡出
 *   ④ 丹火火星  移动时溅出 —— 火星由亮黄→橙红→暗红，带上浮热流
 *   ⑤ 符文阵纹  每隔一会儿浮一枚 —— 金八卦爻（三爻）旋转淡出
 *   ⑥ 彼岸花瓣  偶尔飘一瓣 —— 带旋转与左右飘摆，慢慢落
 *   点击：迸一圈剑气涟漪 + 一把火星 + 一枚亮些的符文
 *   静止：鼠标停住一会儿，脚下缓缓浮现一圈极淡的阵法圆环（动一下就没）
 *
 * 几条硬约束（都照那个参考站点的做法，另外因为本站是**浅色背景**做了调整）：
 *   · 画布固定在 <html> 下、pointer-events:none —— 既不挡点击，也不会被 app.js
 *     重建 body 时连带删掉（app.js 会整体替换 body.innerHTML）
 *   · 颜色全部取**中间调**（鎏金 / 青碧 / 朱砂 / 紫 / 墨）：本站底色是米白，
 *     参考站那种 #fff6c9 亮白星在浅底上根本看不见，也不能用「叠加发光」混合模式
 *   · DPR 封顶 2、粒子总数封顶、移动事件节流 —— 省电、不卡
 *   · 系统开了「减少动态效果」就整个不启动
 *
 * 想调浓淡/频率，只改下面 CFG 与 PALETTE 即可。
 */
(function () {
  "use strict";

  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var CFG = {
    maxParticles: 420,     // 粒子总数上限
    moveInterval: 24,      // 鼠标移动节流（毫秒）
    touchInterval: 40,     // 触摸移动节流
    streakSpeed: 0.55,     // 移动速度（像素/毫秒）超过这个才甩剑光
    fastSpeed: 1.1,        // 更快时多溅火星
    runeInterval: 900,     // 每隔多久浮一枚符文
    petalInterval: 520,    // 每隔多久飘一瓣花
    inkSpeed: 0.12,        // 超过这个速度才落墨点
    idleRingDelay: 650     // 鼠标静止多久后浮现阵法圆环
  };

  // 浅色背景下能看清的中间调：鎏金 / 青碧 / 丹火 / 朱砂 / 紫 / 墨
  var COLOR = {
    mote: ["#B79A54", "#8A7330", "#3E8E9E", "#5F9AA6", "#C2A24E"],
    spark: ["#D99A2B", "#C2551F", "#A03A18"],
    petal: ["#B03A32", "#C75C74", "#8A5BB8", "#A97BD6"],
    rune: "#A88636",
    ink: "#33555E",
    streakCore: "#6FBFC4",
    streakEdge: "#C2A24E",
    ring: "#B79A54"
  };

  var TAU = Math.PI * 2;
  var rand = Math.random;

  function pick(list) { return list[Math.floor(rand() * list.length)]; }

  function rgba(hex, alpha) {
    var h = hex.replace("#", "");
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + alpha + ")";
  }

  // ---- 画布 ----
  var canvas = document.createElement("canvas");
  canvas.id = "cursorFxCanvas";
  canvas.setAttribute("aria-hidden", "true");
  canvas.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:9999;";
  document.documentElement.appendChild(canvas);
  var ctx = canvas.getContext("2d");
  var W = 0, H = 0;

  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener("resize", resize);

  // ---- 光点贴图（预先画好，避免每帧建渐变）----
  var glowCache = {};
  function glowSprite(color) {
    if (glowCache[color]) return glowCache[color];
    var size = 48;
    var c = document.createElement("canvas");
    c.width = c.height = size;
    var g = c.getContext("2d");
    var grd = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    grd.addColorStop(0, rgba(color, 0.85));
    grd.addColorStop(0.4, rgba(color, 0.35));
    grd.addColorStop(1, rgba(color, 0));
    g.fillStyle = grd;
    g.fillRect(0, 0, size, size);
    glowCache[color] = c;
    return c;
  }

  var list = [];
  var rings = [];

  function push(p) {
    list.push(p);
    if (list.length > CFG.maxParticles) list.splice(0, list.length - CFG.maxParticles);
  }

  // ---- ① 灵气星辉 ----
  function spawnMote(x, y) {
    push({
      kind: "mote", x: x, y: y,
      vx: (rand() - 0.5) * 0.7, vy: -0.25 - rand() * 0.5,
      life: 1, decay: 0.012 + rand() * 0.016,
      size: 2.4 + rand() * 3.4, color: pick(COLOR.mote), phase: rand() * TAU,
      twinkle: 0.08 + rand() * 0.1
    });
  }

  // ---- ② 水墨飞白 ----
  function spawnInk(x, y, dx, dy) {
    var len = 8 + rand() * 14;
    var a = Math.atan2(dy, dx) + (rand() - 0.5) * 0.5;
    push({
      kind: "ink", x: x, y: y,
      vx: (rand() - 0.5) * 0.2, vy: (rand() - 0.5) * 0.2,
      life: 1, decay: 0.05 + rand() * 0.04,
      size: 1.4 + rand() * 2.2, color: COLOR.ink,
      tx: Math.cos(a) * len, ty: Math.sin(a) * len
    });
  }

  // ---- ③ 剑意拖尾 ----
  function spawnStreak(x, y, dx, dy, speed) {
    var a = Math.atan2(dy, dx);
    push({
      kind: "streak", x: x, y: y,
      vx: Math.cos(a) * speed * 0.06, vy: Math.sin(a) * speed * 0.06,
      life: 1, decay: 0.055 + rand() * 0.03,
      size: 1.6 + Math.min(speed, 2.4) * 1.1, angle: a,
      len: 26 + Math.min(speed, 2.6) * 22
    });
  }

  // ---- ④ 丹火火星 ----
  function spawnSpark(x, y, burst) {
    var a = burst ? rand() * TAU : (rand() - 0.5) * 1.6 + Math.PI / 2;
    var sp = burst ? 0.9 + rand() * 2.1 : 0.15 + rand() * 0.6;
    push({
      kind: "spark", x: x, y: y,
      vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - (burst ? 0 : 0.3),
      life: 1, decay: 0.02 + rand() * 0.028,
      size: 1.4 + rand() * 2.1, color: pick(COLOR.spark),
      hot: 0
    });
  }

  // ---- ⑤ 符文（金八卦爻：三爻，随机断连）----
  function spawnRune(x, y, scale) {
    var solid = [];
    for (var i = 0; i < 3; i++) solid.push(rand() > 0.42);
    push({
      kind: "rune", x: x, y: y,
      vx: (rand() - 0.5) * 0.16, vy: -0.12 - rand() * 0.2,
      life: 1, decay: 0.011 + rand() * 0.008,
      size: (13 + rand() * 5) * (scale || 1), color: COLOR.rune,
      rot: (rand() - 0.5) * 0.5, spin: (rand() - 0.5) * 0.006, solid: solid
    });
  }

  // ---- ⑥ 彼岸花瓣 ----
  function spawnPetal(x, y) {
    push({
      kind: "petal", x: x, y: y,
      vx: (rand() - 0.5) * 0.35, vy: 0.16 + rand() * 0.32,
      life: 1, decay: 0.0045 + rand() * 0.005,
      size: 4.5 + rand() * 3.5, color: pick(COLOR.petal),
      rot: rand() * TAU, spin: (rand() - 0.5) * 0.05, phase: rand() * TAU
    });
  }

  // ---- 点击：剑气涟漪 ----
  function spawnRing(x, y) {
    rings.push({ x: x, y: y, r: 6, life: 1 });
  }

  // ---- 画 ----
  function drawMote(p) {
    var tw = 0.62 + 0.38 * Math.sin(p.phase);
    var r = p.size * tw;
    ctx.globalAlpha = Math.max(0, Math.min(1, p.life)) * 0.9;
    var sp = glowSprite(p.color);
    ctx.drawImage(sp, p.x - r * 3, p.y - r * 3, r * 6, r * 6);
    ctx.strokeStyle = p.color;
    ctx.lineWidth = Math.max(0.6, r * 0.28);
    ctx.beginPath();
    ctx.moveTo(p.x - r * 2.1, p.y); ctx.lineTo(p.x + r * 2.1, p.y);
    ctx.moveTo(p.x, p.y - r * 2.1); ctx.lineTo(p.x, p.y + r * 2.1);
    ctx.stroke();
  }

  function drawInk(p) {
    var a = Math.max(0, Math.min(1, p.life));
    ctx.globalAlpha = a * 0.5;
    ctx.strokeStyle = p.color;
    ctx.lineCap = "round";
    ctx.lineWidth = p.size * (1.6 - a * 0.9);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    ctx.lineTo(p.x + p.tx, p.y + p.ty);
    ctx.stroke();
    ctx.globalAlpha = a * 0.3;
    ctx.lineWidth = Math.max(0.6, p.size * 0.5);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    ctx.lineTo(p.x + p.tx * 1.35, p.y + p.ty * 1.35);
    ctx.stroke();
  }

  function drawStreak(p) {
    var a = Math.max(0, Math.min(1, p.life));
    var len = p.len * (0.4 + 0.6 * a);
    var dx = Math.cos(p.angle), dy = Math.sin(p.angle);
    var x2 = p.x - dx * len, y2 = p.y - dy * len;
    ctx.lineCap = "round";
    // 外圈金边 → 内芯青白，两层描边（浅底上比单向渐变清楚，也便宜）
    ctx.globalAlpha = a * 0.3;
    ctx.strokeStyle = COLOR.streakEdge;
    ctx.lineWidth = p.size * 1.9 * (0.5 + 0.5 * a);
    ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(x2, y2); ctx.stroke();
    ctx.globalAlpha = a * 0.85;
    ctx.strokeStyle = COLOR.streakCore;
    ctx.lineWidth = p.size * (0.5 + 0.5 * a);
    ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(x2, y2); ctx.stroke();
  }

  function drawSpark(p) {
    var a = Math.max(0, Math.min(1, p.life));
    // 亮黄 → 橙红 → 暗红
    var c = p.life > 0.62 ? COLOR.spark[0] : (p.life > 0.3 ? COLOR.spark[1] : COLOR.spark[2]);
    var r = p.size * (1.5 - a * 0.5);
    ctx.globalAlpha = a * 0.95;
    var sp = glowSprite(c);
    ctx.drawImage(sp, p.x - r * 2.4, p.y - r * 2.4, r * 4.8, r * 4.8);
  }

  function drawRune(p) {
    var a = Math.max(0, Math.min(1, p.life));
    var w = p.size, gap = p.size * 0.6;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.globalAlpha = a * 0.8;
    ctx.strokeStyle = p.color;
    ctx.lineWidth = 1.7;
    ctx.lineCap = "round";
    for (var i = 0; i < 3; i++) {
      var y = (i - 1) * gap;
      ctx.beginPath();
      if (p.solid[i]) {
        ctx.moveTo(-w / 2, y); ctx.lineTo(w / 2, y);
      } else {
        ctx.moveTo(-w / 2, y); ctx.lineTo(-w * 0.14, y);
        ctx.moveTo(w * 0.14, y); ctx.lineTo(w / 2, y);
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawPetal(p) {
    var a = Math.min(1, p.life * 1.6);
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.globalAlpha = a * 0.82;
    ctx.fillStyle = p.color;
    var s = p.size;
    ctx.beginPath();
    ctx.moveTo(0, -s);
    ctx.bezierCurveTo(s * 0.9, -s * 0.45, s * 0.62, s * 0.7, 0, s);
    ctx.bezierCurveTo(-s * 0.62, s * 0.7, -s * 0.9, -s * 0.45, 0, -s);
    ctx.fill();
    ctx.restore();
  }

  // 静止时的阵法圆环：双圈 + 八卦刻度，慢慢转
  function drawIdleRing(t) {
    if (state.idle < CFG.idleRingDelay || !state.inside) return;
    var a = Math.min(1, (state.idle - CFG.idleRingDelay) / 600) * 0.3;
    var r = 26;
    ctx.save();
    ctx.translate(state.x, state.y);
    ctx.globalAlpha = a;
    ctx.strokeStyle = COLOR.ring;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.stroke();
    ctx.globalAlpha = a * 0.8;
    ctx.beginPath(); ctx.arc(0, 0, r - 6, 0, TAU); ctx.stroke();
    var rot = t / 4200;
    ctx.globalAlpha = a * 0.9;
    ctx.lineWidth = 1.6;
    for (var i = 0; i < 8; i++) {
      var ang = rot + (i * TAU) / 8;
      var cx = Math.cos(ang), cy = Math.sin(ang);
      ctx.beginPath();
      ctx.moveTo(cx * (r - 6), cy * (r - 6));
      ctx.lineTo(cx * r, cy * r);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawRings() {
    for (var i = rings.length - 1; i >= 0; i--) {
      var g = rings[i];
      g.r += 2.6;
      g.life -= 0.035;
      if (g.life <= 0) { rings.splice(i, 1); continue; }
      ctx.globalAlpha = g.life * 0.5;
      ctx.strokeStyle = COLOR.streakEdge;
      ctx.lineWidth = 2.4 * g.life + 0.6;
      ctx.beginPath(); ctx.arc(g.x, g.y, g.r, 0, TAU); ctx.stroke();
      ctx.globalAlpha = g.life * 0.4;
      ctx.strokeStyle = COLOR.streakCore;
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(g.x, g.y, g.r * 0.72, 0, TAU); ctx.stroke();
    }
  }

  var state = { x: 0, y: 0, px: 0, py: 0, lastMove: 0, idle: 1e9, inside: false, lastFrame: 0 };
  var lastSpawn = 0, lastRune = 0, lastPetal = 0, last = 0, dirty = false;

  function move(x, y, now) {
    var dx = x - state.px, dy = y - state.py;
    var dist = Math.sqrt(dx * dx + dy * dy);
    var gap = Math.max(now - state.lastMove, 8);
    var speed = dist / gap;                     // 像素 / 毫秒
    state.px = x; state.py = y; state.x = x; state.y = y;
    state.lastMove = now; state.idle = 0; state.inside = true;

    if (now - lastSpawn < CFG.moveInterval) return;
    lastSpawn = now;

    // ① 灵气：常驻，走一下就撒 1~2 点
    spawnMote(x, y);
    if (rand() > 0.55) spawnMote(x + (rand() - 0.5) * 10, y + (rand() - 0.5) * 10);

    // ② 水墨：只要在动就偶尔落一笔
    if (speed > CFG.inkSpeed && rand() > 0.6) spawnInk(x, y, dx, dy);

    // ③ 剑意 + ④ 丹火：快甩才出来
    if (speed > CFG.streakSpeed && dist > 2) {
      spawnStreak(x, y, dx, dy, speed);
      spawnSpark(x, y, false);
      if (speed > CFG.fastSpeed) spawnSpark(x, y, false);
    }

    // ⑤ 符文：隔一会儿浮一枚
    if (now - lastRune > CFG.runeInterval) {
      lastRune = now;
      spawnRune(x + (rand() - 0.5) * 24, y + (rand() - 0.5) * 24, 1);
    }

    // ⑥ 花瓣：偶尔飘一瓣
    if (now - lastPetal > CFG.petalInterval) {
      lastPetal = now;
      spawnPetal(x + (rand() - 0.5) * 30, y + (rand() - 0.5) * 20);
    }
  }

  function frame(t) {
    var dt = last ? Math.min((t - last) / 16.7, 3) : 1;
    last = t;
    state.idle += t - (state.lastFrame || t);
    state.lastFrame = t;

    // 屏幕上没东西可画时就不清屏、也不遍历，省电（rAF 本身很便宜）
    var ringVisible = state.idle > CFG.idleRingDelay && state.inside;
    if (dirty || list.length || rings.length || ringVisible) {
      ctx.clearRect(0, 0, W, H);
      drawIdleRing(t);
      for (var i = list.length - 1; i >= 0; i--) {
        var p = list[i];
        p.life -= p.decay * dt;
        if (p.life <= 0) { list.splice(i, 1); continue; }
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        if (p.kind === "mote") { p.phase += p.twinkle * dt; p.vy -= 0.004 * dt; }
        else if (p.kind === "spark") { p.vy -= 0.012 * dt; p.vx *= 0.985; }
        else if (p.kind === "petal") {
          p.phase += 0.03 * dt;
          p.x += Math.sin(p.phase) * 0.55 * dt;
          p.vy = Math.min(p.vy + 0.004 * dt, 0.75);
          p.rot += p.spin * dt;
        }
        else if (p.kind === "rune") { p.rot += p.spin * dt; }

        if (p.kind === "mote") drawMote(p);
        else if (p.kind === "ink") drawInk(p);
        else if (p.kind === "streak") drawStreak(p);
        else if (p.kind === "spark") drawSpark(p);
        else if (p.kind === "rune") drawRune(p);
        else if (p.kind === "petal") drawPetal(p);
      }

      drawRings();
      ctx.globalAlpha = 1;
      dirty = Boolean(list.length || rings.length || ringVisible);
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  document.addEventListener("mousemove", function (e) {
    move(e.clientX, e.clientY, performance.now());
  }, { passive: true });

  document.addEventListener("touchmove", function (e) {
    var touch = e.touches && e.touches[0];
    if (!touch) return;
    var now = performance.now();
    if (now - lastSpawn < CFG.touchInterval) return;
    move(touch.clientX, touch.clientY, now);
  }, { passive: true });

  document.addEventListener("mouseleave", function () { state.inside = false; });
  document.addEventListener("pointerdown", function (e) {
    var now = performance.now();
    state.x = e.clientX; state.y = e.clientY;
    state.px = e.clientX; state.py = e.clientY;
    state.idle = 0;
    spawnRing(e.clientX, e.clientY);
    for (var i = 0; i < 14; i++) spawnSpark(e.clientX, e.clientY, true);
    spawnRune(e.clientX, e.clientY, 1.35);
    spawnMote(e.clientX, e.clientY);
    lastSpawn = now;
  }, { passive: true });
})();
