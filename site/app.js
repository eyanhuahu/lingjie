const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

const LOG_SECTION_ID = "log";
const Sheets = window.SheetsContent || {};
const PRIMARY_IMAGE_BASE_PATH = Sheets.PRIMARY_IMAGE_BASE_PATH || "images/";
const DEFAULT_PLACEHOLDER_IMAGE = Sheets.DEFAULT_PLACEHOLDER_IMAGE || "images/placeholder.jpg";

function scrollTrigger() {
  const value = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop);
  return Number.isFinite(value) ? value : 156;
}

// 顶栏是 fixed 的，正文靠 --mast-h 让位。顶栏里文字换行、字体加载完、窗口变窄
// 都会让它的真实高度和 CSS 里写死的 132px 对不上，于是侧栏第一行会被顶栏盖住。
// 这里量一次真实高度写回去（min-height 用的是另一个变量，不会自反馈）。
function syncMastHeight() {
  const mast = $(".masthead");
  if (!mast) return;
  const h = Math.round(mast.getBoundingClientRect().height);
  if (!h) return;
  document.documentElement.style.setProperty("--mast-h", `${h}px`);
  document.documentElement.style.scrollPaddingTop = `${h + 24}px`;
}

const state = {
  data: null,
  query: "",
  activeSec: "",
  pendingItem: "",
  itemById: new Map(),
  itemByName: new Map(),
  autoXrefByTerm: new Map(),
  autoXrefPattern: null,
  carousel: new Map(),
  reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  lastFocus: null,
  modalMode: "",
  locked: false,
  lockTimer: 0,
  ticking: false
};
let spyCards = null;

// ---------------------------------------------------------------------------
// 侧边栏底部的「加入 mod 讨论群」按钮（要换群 / 换链接改这里就行）
// QQ_GROUP_INVITE_URL 是 QQ 群设置里「分享群链接」复制出来的地址，
// 任何浏览器都能打开加群页面（含二维码）；authKey 那种参数是 QQ 生成的，
// 万一哪天失效，按钮会退回用 scheme 唤起 QQ，群号也一直显示在旁边可以手搜。
// ---------------------------------------------------------------------------
const QQ_GROUP_NUMBER = "767318372";
const QQ_GROUP_NAME = "【灵界】渡劫办事处";
const QQ_GROUP_INVITE_URL = "https://qun.qq.com/universal-share/share?ac=1"
  + "&authKey=QyAiF93GwBtDmUvMv0yL9TPnf42OggZXHjzmT%2BY4OWrRsvy%2FV8bxee0zHAULratp"
  + "&busi_data=eyJncm91cENvZGUiOiI3NjczMTgzNzIiLCJ0b2tlbiI6IlMxaEFHQU5XRlVNT08yTzlFVHdoNW0yVUp4ZXA0clVMTTZKbUNtaU92dUx6OVJ4LzE3Z0pOZzd4Y0RzM1F5MnIiLCJ1aW4iOiI3ODYyNTYzOCJ9"
  + "&data=wHS830Gr8gsVN5SkT3Q49xnPZH75_JKrDvfkv2Wj8KhzXT4iePgYWpin5P2eZOhzl_sKaLJwGAvuKE0myAkQnw"
  + "&svctype=4&tempid=h5_group_info";
const QQ_GROUP_SCHEME = "mqqapi://card/show_pslcard?src_type=internal&version=1&card_type=group"
  + `&uin=${QQ_GROUP_NUMBER}&source=qrcode`;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalize(value) {
  return String(value ?? "").toLowerCase().trim();
}

function stripHtml(value) {
  const box = document.createElement("div");
  box.innerHTML = String(value ?? "");
  return box.textContent || "";
}

function debounce(fn, delay = 160) {
  let timer = 0;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), delay);
  };
}

function ensureShell() {
  document.body.innerHTML = `
    <a class="skip-link" href="#main">跳到主内容</a>
    <header class="masthead">
      <div class="mast-center">
        <div class="serif site-name" id="siteName">灵界</div>
        <div class="site-sub-row">
          <span class="site-name-wrap">
            <span class="site-name-en" id="siteNameEn"></span>
            <span class="site-ver-badge" id="siteVersion">V0.1.0</span>
          </span>
        </div>
        <div class="ornament" aria-hidden="true"><i></i><b></b><i></i></div>
        <div class="site-ver" id="siteMeta">预留作者</div>
      </div>
      <div class="mast-tools">
        <button class="btn-qq btn-qq-flat" type="button" id="joinGroupTopBtn">加入 mod 讨论群</button>
      </div>
    </header>

    <div class="shell">
      <aside class="rail" id="rail" aria-label="卷目">
        <div class="rail-inner">
          <form class="rail-search" id="searchForm" role="search">
            <label class="sr-only" for="searchInput">搜索</label>
            <div class="search"><i class="ti ti-search" aria-hidden="true"></i><input id="searchInput" type="search" autocomplete="off" placeholder="搜索"></div>
            <button class="btn-clear" type="button" id="clearSearchBtn">清空</button>
          </form>
          <div class="rail-divider" aria-hidden="true"></div>
          <ul class="nav" id="nav"></ul>
          <div class="rail-foot">
            <button class="btn-qq" type="button" id="joinGroupBtn">加入 mod 讨论群</button>
            <p class="qq-hint" id="qqHint" hidden>QQ 群「${QQ_GROUP_NAME}」<b id="qqNumber">${QQ_GROUP_NUMBER}</b><button class="btn-copy" type="button" id="copyQqBtn">复制群号</button></p>
          </div>
        </div>
      </aside>
      <main class="content" id="main" tabindex="-1">
        <div class="content-inner">
          <section class="editor-panel" id="editorPanel" hidden></section>
          <div class="empty-state" id="emptyState" hidden>
            <strong>没有找到匹配条目。</strong>
            <span>可以清空搜索后再试。</span>
            <button class="btn-clear" type="button" id="emptyClearBtn">清空搜索</button>
          </div>
          <div id="sectionsRoot"></div>
        </div>
      </main>
    </div>

    <button class="to-top" type="button" id="toTopBtn" aria-label="回到顶部">回到顶部</button>

    <svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
      <pattern id="yun" width="40" height="34" patternUnits="userSpaceOnUse">
        <path d="M0,34 V22 Q10,8 20,22 Q30,8 40,22 V34 Z" fill="var(--c-white)"/>
      </pattern>
    </defs></svg>

    <div class="modal-mask" id="modal" hidden aria-hidden="true">
      <div class="modal-backdrop" data-close="modal"></div>
      <section class="modal-card" role="dialog" aria-modal="true" aria-labelledby="modalTitle" tabindex="-1">
        <button class="modal-close" type="button" data-close="modal" aria-label="关闭弹窗">×</button>
        <h3 id="modalTitle"></h3>
        <div class="modal-body" id="modalBody"></div>
      </section>
    </div>
  `;
}

function parseHash() {
  const raw = location.hash.replace(/^#/, "");
  const params = new URLSearchParams(raw);
  state.query = params.get("q") || "";
  state.activeSec = params.get("sec") || "";
  if (state.activeSec === "changelog") state.activeSec = LOG_SECTION_ID;
  state.pendingItem = params.get("item") || "";
}

function writeHash(extra = {}) {
  const params = new URLSearchParams();
  let sec = extra.sec ?? state.activeSec;
  if (sec === "changelog") sec = LOG_SECTION_ID;
  const q = extra.q ?? state.query;
  const item = extra.item ?? "";
  if (item) params.set("item", item);
  else if (sec) params.set("sec", sec);
  if (q) params.set("q", q);
  const next = params.toString() ? `#${params.toString()}` : `${location.pathname}${location.search}`;
  history.replaceState(null, "", next);
}

async function loadData() {
  if (!Sheets.loadContentJson) {
    throw new Error("缺少 data.json 读取脚本，请确认 site/js/sheetsContent.js 已正确加载。");
  }
  const result = await Sheets.loadContentJson();
  if (!result.data.sections.length || !result.data.items.length) {
    throw new Error("data.json 内容为空，请确认 sections 与 items 两个数组都有条目。");
  }
  return result.data;
}

function buildIndex() {
  state.itemById.clear();
  state.itemByName.clear();
  state.autoXrefByTerm.clear();
  state.autoXrefPattern = null;
  (state.data.items || []).forEach((item) => {
    state.itemById.set(item.id, item);
    state.itemByName.set(item.name, item);
  });
  // 自动跳转词表：所有条目按名称登记，tele 只用于别名（例如「魔兽森林」→ 蝴蝶岛）。
  // 这样任何卡片正文里写到别的条目名都会变成可点链接，不再需要逐条维护词条。
  const xrefTerms = typeof Sheets.buildXrefTerms === "function"
    ? Sheets.buildXrefTerms(state.data.items, state.data.tele)
    : [];
  xrefTerms.forEach((row) => {
    const target = state.itemById.get(row.id);
    if (target) state.autoXrefByTerm.set(normalize(row.term), target);
  });
  // 兼容旧路径：万一站点脚本版本不匹配，退回只按 tele 表登记
  if (!xrefTerms.length) {
    (state.data.tele || []).forEach((row) => {
      const terms = splitTeleTerms(row.field);
      const target = state.itemById.get(row.target_id)
        || state.itemByName.get(row.target_id)
        || (terms.length === 1 ? state.itemByName.get(terms[0]) : null);
      if (!target) return;
      terms.forEach((term) => {
        state.autoXrefByTerm.set(normalize(term), target);
      });
    });
  }
  const terms = Array.from(state.autoXrefByTerm.keys())
    .filter(Boolean)
    .sort((a, b) => b.length - a.length);
  state.autoXrefPattern = terms.length ? new RegExp(terms.map(escapeRegExp).join("|"), "gi") : null;
}

function sectionIds() {
  return new Set((state.data.sections || []).map((section) => section.id));
}

function itemSearchText(item) {
  return normalize([
    item.name,
    ...(item.tags || []),
    item.summary,
    item.detailText,
    stripHtml(item.detailHtml)
  ].join(" "));
}

function matchesQuery(item) {
  return !state.query || itemSearchText(item).includes(normalize(state.query));
}

function highlightEscaped(text) {
  const raw = String(text ?? "");
  const query = String(state.query || "").trim();
  if (!query) return escapeHtml(raw);
  const safeQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const reg = new RegExp(safeQuery, "ig");
  const matches = raw.match(reg);
  if (!matches) return escapeHtml(raw);
  const parts = raw.split(reg);
  return parts.map((part, index) => {
    const hit = matches[index] ? `<mark>${escapeHtml(matches[index])}</mark>` : "";
    return `${escapeHtml(part)}${hit}`;
  }).join("");
}

function escapeRegExp(value) {
  return String(value ?? "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function splitTeleTerms(value) {
  return String(value ?? "")
    .split(/[，,、|;\n\r]+/)
    .map((term) => term.trim())
    .filter(Boolean);
}

function xrefTargetHtml(label, item) {
  if (!item) return escapeHtml(label);
  return `<a href="#item=${encodeURIComponent(item.id)}" class="xref" data-target="${escapeHtml(item.id)}">${highlightEscaped(label)}</a>`;
}

function xrefHtml(name) {
  const item = state.itemByName.get(name);
  return xrefTargetHtml(name, item);
}

function renderAutoXrefs(text) {
  const source = String(text ?? "");
  if (!source || !state.autoXrefPattern) return highlightEscaped(source);
  state.autoXrefPattern.lastIndex = 0;
  let html = "";
  let lastIndex = 0;
  let match;
  while ((match = state.autoXrefPattern.exec(source)) !== null) {
    const hit = match[0];
    const item = state.autoXrefByTerm.get(normalize(hit));
    if (!hit || !item) continue;
    html += highlightEscaped(source.slice(lastIndex, match.index));
    html += xrefTargetHtml(hit, item);
    lastIndex = match.index + hit.length;
  }
  html += highlightEscaped(source.slice(lastIndex));
  return html;
}

// 详情正文里提到的条目，名字前面挂一张对应小图标（同上：缺失就悄悄降级，不留破图）。
// 图标优先用配方那种 64×64 小图标，没有就退回该条目的展示图；
// 卡片图是占位图（该条目本来就没图）时不再试第二次，省一次必然 404 的请求。
function xrefIconNode(item) {
  if (!item || !item.id) return null;
  const icon = resolveImagePath(`images/lingjie/icons/${item.id}.png`);
  const cardImage = item.resolved_image && item.resolved_image !== DEFAULT_PLACEHOLDER_IMAGE
    ? resolveImagePath(item.resolved_image)
    : "";
  const img = document.createElement("img");
  img.className = "xref-icon";
  img.alt = "";
  img.loading = "lazy";
  img.setAttribute("aria-hidden", "true");
  let tried = 0;
  img.addEventListener("error", () => {
    tried += 1;
    if (tried === 1 && cardImage && cardImage !== icon) {
      img.src = cardImage;
      return;
    }
    img.hidden = true;
  });
  img.src = icon;
  return img;
}

// 名字前面已经有一个行内小图标（配方那种 [路径] 图标）时不再重复加，否则会「大图小图」挤一起
function hasRecipeIconBefore(container) {
  const prev = container.lastElementChild;
  return Boolean(prev && prev.tagName === "IMG" && prev.classList.contains("recipe-icon"));
}

function appendAutoXrefs(container, text) {
  const source = String(text ?? "");
  if (!source || !state.autoXrefPattern) {
    container.appendChild(document.createTextNode(source));
    return;
  }
  state.autoXrefPattern.lastIndex = 0;
  let lastIndex = 0;
  let match;
  while ((match = state.autoXrefPattern.exec(source)) !== null) {
    const hit = match[0];
    const item = state.autoXrefByTerm.get(normalize(hit));
    if (!hit || !item) continue;
    container.appendChild(document.createTextNode(source.slice(lastIndex, match.index)));
    const icon = hasRecipeIconBefore(container) ? null : xrefIconNode(item);
    if (icon) container.appendChild(icon);
    const a = document.createElement("a");
    a.className = "xref";
    a.href = `#item=${encodeURIComponent(item.id)}`;
    a.dataset.target = item.id;
    a.textContent = hit;
    container.appendChild(a);
    lastIndex = match.index + hit.length;
  }
  container.appendChild(document.createTextNode(source.slice(lastIndex)));
}

// 行内小图标：单个中括号里放图片路径，写法与制作配方一致。
// 只有图片扩展名才会被当成图标，其他方括号内容照旧。
const INLINE_IMAGE_RE = /^\[([^[\]]+\.(?:png|jpe?g|webp|gif|svg))\]$/i;
const INLINE_IMAGE_SPLIT_RE = /(\[\[[^\]]+\]\]|\[[^[\]]+\.(?:png|jpe?g|webp|gif|svg)\])/gi;

function renderTextWithXrefs(text, options = {}) {
  const auto = options.auto !== false;
  return String(text ?? "").split(INLINE_IMAGE_SPLIT_RE).map((part) => {
    const imageMarker = part.match(/^\[\[(?:图片|image):/i);
    if (!imageMarker) {
      const inlineImage = part.match(INLINE_IMAGE_RE);
      if (inlineImage) {
        const html = imageTag(inlineImage[1], "", "recipe-icon");
        if (html) return html;
      }
    }
    const match = part.match(/^\[\[([^\]]+)\]\]$/);
    if (!imageMarker && match) return xrefHtml(match[1].trim());
    return auto ? renderAutoXrefs(part) : highlightEscaped(part);
  }).join("");
}

// 标题里尾部括号的补充说明（「合婴丹（丹劫）」「噬魂蛇（隐藏 Boss）」）：
// 卡片标题 —— 作者要求**整个去掉**：标签里已经有「丹劫」了，标题上再挂一遍重复。
// 详情弹窗标题 —— 作者要求**去掉括号、改成一个圆点「·」，字号不变**。
function splitTitleSuffix(name) {
  const raw = String(name ?? "");
  const m = raw.match(/^(.*?)\s*[（(]([^（()）]+)[)）]\s*$/);
  if (!m || !m[1].trim()) return [raw, ""];
  return [m[1].trim(), m[2].trim()];
}

function renderCardTitle(name) {
  return renderTextWithXrefs(splitTitleSuffix(name)[0], { auto: false });
}

function renderModalTitle(name) {
  const [main, suffix] = splitTitleSuffix(name);
  return suffix ? `${main}·${suffix}` : main;
}

function parseRecipe(recipe) {  const raw = String(recipe ?? "");
  if (!raw.trim()) return "";
  // 材料之间用「、」分隔；每一份材料（图标 + 名字 + 数量）各自包一个 .recipe-entry，
  // 靠 CSS 的 white-space:nowrap 让它**整体换行** —— 不然会出现图标留在上一行、
  // 名字和数量掉到下一行的断裂（作者反馈过）。
  // 材料之间用「、」分隔；每一份材料（图标 + 名字 + 数量）各自包一个 .recipe-entry，
  // 靠 CSS 的 white-space:nowrap 让它**整体换行** —— 不然会出现图标留在上一行、
  // 名字和数量掉到下一行的断裂（作者反馈过）。
  // 顿号一律不输出：换行时行尾会挂一个孤零零的「、」，而 CSS 判断不出哪一份在行尾，
  // 所以改用间距分隔（每份材料自带图标，本来就不需要顿号）。
  return raw.split("、").filter((chunk) => chunk.trim()).map((chunk) => {
    const html = chunk.split(/(\[\[[^\]]+\]\]|\[[^\]]+\])/g).filter(Boolean).map((part) => {
      const xref = part.match(/^\[\[([^\]]+)\]\]$/);
      if (xref) return xrefHtml(xref[1].trim());
      const image = part.match(/^\[([^\]]+)\]$/);
      if (image) return `<img class="recipe-icon" src="${escapeHtml(image[1].trim())}" alt="" loading="lazy" onerror="this.style.display='none'">`;
      return `<span>${highlightEscaped(part)}</span>`;
    }).join("");
    return `<span class="recipe-entry">${html}</span>`;
  }).join("");
}

function isHttpUrl(value) {
  if (Sheets.isHttpUrl) return Sheets.isHttpUrl(value);
  return /^https?:\/\//i.test(String(value ?? "").trim());
}

function looksLikeImageFilename(value) {
  if (Sheets.looksLikeImageFilename) return Sheets.looksLikeImageFilename(value);
  const text = String(value ?? "").trim();
  if (!text || isHttpUrl(text) || /[\\/]/.test(text)) return false;
  return /\.(jpe?g|png|webp|gif|svg)$/i.test(text);
}

function toLocalImagePath(filename) {
  if (Sheets.toLocalImagePath) return Sheets.toLocalImagePath(filename);
  const clean = String(filename ?? "").trim().replace(/^\/+/, "");
  if (!clean) return "";
  if (clean.startsWith(PRIMARY_IMAGE_BASE_PATH)) return clean;
  return `${PRIMARY_IMAGE_BASE_PATH}${clean}`;
}

function resolveImagePath(path) {
  if (Sheets.resolveImagePath) return Sheets.resolveImagePath(path);
  const clean = String(path ?? "").trim();
  if (!clean) return "";
  if (isHttpUrl(clean) || clean.startsWith(PRIMARY_IMAGE_BASE_PATH) || /[\\/]/.test(clean)) return clean;
  if (looksLikeImageFilename(clean)) return toLocalImagePath(clean);
  return clean;
}

function imageTag(path, alt, className = "") {
  const src = resolveImagePath(path);
  if (!src) return "";
  return `<img class="${className}" src="${escapeHtml(src)}" alt="${escapeHtml(alt)}" loading="lazy" onerror="this.style.display='none'">`;
}

function renderCarousel(item) {
  const images = Array.isArray(item.images) ? item.images.filter(Boolean) : [];
  if (!images.length) return "";
  const current = Math.min(state.carousel.get(item.id) || 0, images.length - 1);
  state.carousel.set(item.id, current);
  const controls = images.length > 1 ? `
    <div class="carNav">
      <button class="carBtn" type="button" data-action="prev" data-id="${escapeHtml(item.id)}" aria-label="上一张">‹</button>
      <button class="carBtn" type="button" data-action="next" data-id="${escapeHtml(item.id)}" aria-label="下一张">›</button>
    </div>
    <div class="dots" aria-label="图片分页">
      ${images.map((_, index) => `<button class="dot ${index === current ? "active" : ""}" type="button" data-action="dot" data-id="${escapeHtml(item.id)}" data-index="${index}" aria-label="第 ${index + 1} 张"></button>`).join("")}
    </div>
  ` : "";
  return `<div class="card-media">${imageTag(images[current], `${item.name} 展示图 ${current + 1}`, "")}${controls}</div>`;
}

function yunFoot() {
  const head = `<svg class="yun-head" style="left:6px" width="30" height="26" viewBox="0 0 24 22" aria-hidden="true"><path d="M12,21 C6,21 1,17 2,10 C2.6,5 8,5 9,10 C9.4,12 14.6,12 15,10 C16,5 21.4,5 22,10 C23,17 18,21 12,21 Z" fill="#FFFFFF"/></svg>`;
  return `<svg class="yun-band" aria-hidden="true"><rect width="100%" height="34" fill="url(#yun)"/></svg>${head}${head.replace("left:6px", "right:6px;transform:scaleX(-1)")}`;
}

function renderCard(item) {
  const tags = (item.tags || []).map((tag) => `<span class="tag">${highlightEscaped(tag)}</span>`).join("");
  const recipe = item.recipe ? `<div class="card-recipe">${parseRecipe(item.recipe)}</div>` : "";
  const hasImages = Array.isArray(item.images) && item.images.filter(Boolean).length > 0;
  return `
    <article class="card${hasImages ? "" : " no-media"}" id="${escapeHtml(item.id)}" data-item-id="${escapeHtml(item.id)}" tabindex="0">
      <div class="card-top">
        ${renderCarousel(item)}
        <div class="card-summary">
          <div class="card-head-row">
            <h3 class="card-title card-title-preview serif">${renderCardTitle(item.name)}</h3>
            <div class="card-tags">${tags}</div>
          </div>
          <p class="card-desc card-preview-desc">${renderTextWithXrefs(item.summary)}</p>
          ${recipe}
        </div>
      </div>
      <div class="card-foot"><button class="btn-detail" type="button" data-action="detail" data-id="${escapeHtml(item.id)}">查看详情</button></div>
    </article>
  `;
}

function renderHeader() {
  const site = state.data.site || {};
  const name = site.name || "灵界";
  const enName = String(site.en_name || "").trim();
  // 站名一行、英文名 + 版本徽章一行（陛下要求英文与版本号放到中文下面）
  $("#siteName").textContent = name;
  $("#siteNameEn").textContent = enName;
  document.title = enName ? `${name} ${enName}` : name;
  $("#siteVersion").textContent = String(site.version || "v0.1.0").toUpperCase();
  $("#siteMeta").textContent = site.author || "预留作者";
}

function validItems() {
  const ids = sectionIds();
  return (state.data.items || []).filter((item) => ids.has(item.section));
}

function sectionItems(sectionId) {
  return validItems().filter((item) => item.section === sectionId);
}

function isLogSection(section) {
  return section?.id === LOG_SECTION_ID;
}

function openGroup(li) {
  const ul = $(".nav-sub", li);
  if (!ul) return;
  li.classList.add("open");
  // 量不到高度（元素当时不可见）时别把 max-height 写成 0，否则子条目会被压成一条线
  const height = ul.scrollHeight;
  ul.style.maxHeight = height ? `${height}px` : "none";
}

function closeGroup(li) {
  const ul = $(".nav-sub", li);
  if (!ul) return;
  li.classList.remove("open");
  ul.style.maxHeight = "0px";
}

function toggleGroup(li) {
  if (!li) return;
  li.classList.contains("open") ? closeGroup(li) : openGroup(li);
}

function syncOpenHeights() {
  $$(".nav-group.open").forEach(openGroup);
}

function clearActive() {
  $$(".nav-row.on,.nav-sub a.on").forEach((el) => el.classList.remove("on"));
}

function setActiveSection(gid) {
  clearActive();
  $(`.nav-row[data-sec="${CSS.escape(gid)}"]`)?.classList.add("on");
}

function setActiveItemByAnchor(a) {
  clearActive();
  a.classList.add("on");
  const li = a.closest(".nav-group");
  $(".nav-row", li)?.classList.add("on");
  openGroup(li);
}

function setActiveItemById(itemId) {
  const a = $(`.nav-sub a[data-item="${CSS.escape(itemId)}"]`);
  if (a) setActiveItemByAnchor(a);
}

function sectionSpyCards(sectionId) {
  if (!spyCards) spyCards = new Map();
  if (!spyCards.has(sectionId)) {
    spyCards.set(sectionId, $$(`#sec-${CSS.escape(sectionId)} .card[data-item-id]`));
  }
  return spyCards.get(sectionId);
}

// 滚动时定位当前读到哪一条：卡片按 DOM 顺序自上而下排列，用二分找最后一张越过分隔线的卡片
function currentItemId(sectionId) {
  const cards = sectionSpyCards(sectionId);
  if (!cards.length) return null;
  const trigger = scrollTrigger();
  let lo = 0;
  let hi = cards.length - 1;
  let found = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (cards[mid].getBoundingClientRect().top - trigger <= 0) {
      found = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return found < 0 ? null : cards[found].dataset.itemId || null;
}

function setActiveSubItem(itemId) {
  $$(".nav-sub a.on").forEach((el) => el.classList.remove("on"));
  if (!itemId) return;
  $(`.nav-sub a[data-item="${CSS.escape(itemId)}"]`)?.classList.add("on");
}

function renderNav(sections) {
  const nav = $("#nav");
  const signature = sections.map((section) => {
    const count = isLogSection(section) ? (state.data.changelog || []).length : sectionItems(section.id).length;
    return `${section.id}:${count}`;
  }).join("|");
  if (nav.dataset.signature === signature) {
    setActiveSection(state.activeSec);
    syncOpenHeights();
    return;
  }
  nav.dataset.signature = signature;
  nav.innerHTML = sections.map((section) => {
    const subs = isLogSection(section)
      ? (state.data.changelog || []).slice().reverse().map((log) => `<li><a data-log="${escapeHtml(log.version)}">${escapeHtml(log.version)} · ${escapeHtml(log.date || "")}</a></li>`).join("")
      : sectionItems(section.id).map((item) => `<li><a data-item="${escapeHtml(item.id)}">${escapeHtml(item.name)}</a></li>`).join("");
    return `
      <li class="nav-group${state.activeSec === section.id ? " open" : ""}" data-g="${escapeHtml(section.id)}">
        <div class="nav-row${state.activeSec === section.id ? " on" : ""}" data-sec="${escapeHtml(section.id)}">
          <span class="nav-lbl"><span class="nav-lbl-full">${escapeHtml(section.name)}</span><span class="nav-lbl-short">${escapeHtml(section.shortName || section.name)}</span></span>
          <i class="ti ti-chevron-right nav-chev" aria-hidden="true"></i>
        </div>
        <ul class="nav-sub">${subs}</ul>
      </li>
    `;
  }).join("");
  syncOpenHeights();
}

// 各卷目为空时的提示文案：默认「暂无条目」；
// 「人物」还没实装，作者要求写成「敬请期待！」。
const EMPTY_SECTION_TEXT = { renwu: "敬请期待！" };

function emptySectionText(sectionId) {
  return EMPTY_SECTION_TEXT[sectionId] || "暂无条目";
}

function renderChangelog(section) {
  const logs = [...(state.data.changelog || [])].reverse();
  const body = logs.length ? `<div class="cards">${logs.map((log) => `
    <article class="card no-media log-card">
      <div class="card-head"><div class="card-main"><h3 class="card-title serif">${escapeHtml(log.version)}</h3><div class="card-tags"><span class="tag">${escapeHtml(log.date || "")}</span></div></div></div>
      <p class="card-desc">${(log.entries || []).map((entry) => renderTextWithXrefs(entry)).join("；")}</p>
      <div class="card-foot"><button class="btn-detail" type="button" data-action="changelog">完整更新</button></div>
      ${yunFoot()}
    </article>
  `).join("")}</div>` : `<p class="sec-empty">${escapeHtml(emptySectionText(section.id))}</p>`;
  return `<section class="section" id="sec-${escapeHtml(section.id)}" data-section="${escapeHtml(section.id)}"><div class="sec-head"><h2 class="sec-title serif">${escapeHtml(section.name)}</h2></div>${body}</section>`;
}

function renderSections() {
  const sections = state.data.sections || [];
  renderNav(sections);
  let visibleCount = 0;
  const html = sections.map((section) => {
    if (isLogSection(section)) return renderChangelog(section);
    const items = sectionItems(section.id).filter(matchesQuery);
    if (!items.length && state.query) return "";
    visibleCount += items.length;
    const body = items.length ? `<div class="cards">${items.map(renderCard).join("")}</div>` : `<p class="sec-empty">${escapeHtml(emptySectionText(section.id))}</p>`;
    return `<section class="section" id="sec-${escapeHtml(section.id)}" data-section="${escapeHtml(section.id)}"><div class="sec-head"><h2 class="sec-title serif">${escapeHtml(section.name)}</h2></div>${body}</section>`;
  }).join("");
  $("#sectionsRoot").innerHTML = html;
  spyCards = null;
  $("#emptyState").hidden = Boolean(visibleCount || !state.query);
  $("#searchInput").value = state.query;
  renderEditorPanel();
  syncOpenHeights();
  requestAnimationFrame(updateSpy);
}

function renderEditorPanel() {
  const panel = $("#editorPanel");
  const editorEnabled = new URLSearchParams(location.search).get("editor") === "1";
  if (!editorEnabled) {
    panel.hidden = true;
    return;
  }
  const ids = sectionIds();
  const issues = [];
  (state.data.items || []).forEach((item) => {
    if (!ids.has(item.section)) issues.push(`section 失配：${item.name} -> ${item.section}`);
  });
  (state.data.sections || []).forEach((section) => {
    if ("icon" in section) issues.push(`sections 不应包含 icon：${section.id}`);
  });
  panel.hidden = false;
  panel.innerHTML = `<h2>editor 自检：${issues.length} 个问题</h2><ul>${issues.map((issue) => `<li>${escapeHtml(issue)}</li>`).join("") || "<li>未发现问题。</li>"}</ul>`;
}

function lockSpy(ms = 700) {
  state.locked = true;
  window.clearTimeout(state.lockTimer);
  state.lockTimer = window.setTimeout(() => {
    state.locked = false;
    updateSpy();
  }, state.reducedMotion ? 80 : ms);
}

function clickJump(id) {
  const target = document.getElementById(id);
  if (!target) return;
  const trigger = scrollTrigger();
  lockSpy();
  const y = target.getBoundingClientRect().top + window.scrollY - (trigger - 8);
  window.scrollTo({ top: Math.max(0, y), behavior: state.reducedMotion ? "auto" : "smooth" });
  // 以前这里会给目标卷加一个 .flash 类，闪一圈金色内阴影当「落到这里」的提示；
  // 用户觉得那圈金框抢眼，去掉了。滚动本身 + 侧栏高亮已经够表明位置。
}

function visibleSections() {
  return $$('.content section[id^="sec-"]').filter((section) => section.offsetParent !== null);
}

function currentSectionId() {
  const secs = visibleSections();
  if (!secs.length) return null;
  if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) return secs[secs.length - 1].id;
  const trigger = scrollTrigger();
  let active = secs[0].id;
  for (const section of secs) {
    if (section.getBoundingClientRect().top - trigger <= 0) active = section.id;
    else break;
  }
  return active;
}

function updateSpy() {
  if (state.locked) return;
  const sectionId = currentSectionId();
  if (!sectionId) return;
  const gid = sectionId.replace(/^sec-/, "");
  if (gid !== state.activeSec) {
    state.activeSec = gid;
    setActiveSection(gid);
    writeHash({ sec: gid });
  } else {
    setActiveSection(gid);
  }
  setActiveSubItem(currentItemId(sectionId));
}

function scheduleScrollSpy() {
  if (state.ticking) return;
  state.ticking = true;
  requestAnimationFrame(() => {
    state.ticking = false;
    syncToTopBtn();
    updateSpy();
  });
}

// 右下角「回到顶部」：往下滚过一屏的一半才出现，回到顶部后自己淡出
const TO_TOP_AT = 400;

function syncToTopBtn() {
  $("#toTopBtn")?.classList.toggle("show", window.scrollY > TO_TOP_AT);
}

function wireToTop() {
  syncToTopBtn();
  $("#toTopBtn")?.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: state.reducedMotion ? "auto" : "smooth" });
  });
}

function scrollToSection(sectionId, write = true) {
  if (!document.getElementById(`sec-${sectionId}`)) return;
  state.activeSec = sectionId;
  setActiveSection(sectionId);
  openGroup($(`.nav-group[data-g="${CSS.escape(sectionId)}"]`));
  clickJump(`sec-${sectionId}`);
  if (write) writeHash({ sec: sectionId });
}

function jumpToItem(itemId, write = true) {
  const card = document.getElementById(itemId);
  if (!card) return;
  const item = state.itemById.get(itemId);
  if (item) state.activeSec = item.section;
  setActiveItemById(itemId);
  clickJump(itemId);
  card.focus({ preventScroll: true });
  if (write) writeHash({ sec: state.activeSec, item: "" });
}

function openItemModal(itemId, trigger = document.activeElement, write = true) {
  const item = state.itemById.get(itemId);
  if (!item) return;
  state.lastFocus = trigger;
  state.modalMode = "item";
  $("#modalTitle").textContent = renderModalTitle(item.name);
  const body = $("#modalBody");
  body.textContent = "";
  if (item.recipe) {
    const recipe = document.createElement("div");
    recipe.className = "card-recipe";
    recipe.innerHTML = parseRecipe(item.recipe);
    body.appendChild(recipe);
  }
  const detail = document.createElement("div");
  detail.className = "detail-content";
  const detailText = item.detailText
    || (item.detailHtml ? (Sheets.plainTextFromHtml ? Sheets.plainTextFromHtml(item.detailHtml) : stripHtml(item.detailHtml)) : "")
    || item.summary
    || "暂无详情。";
  const blocks = Sheets.parseDetailBlocks ? Sheets.parseDetailBlocks(detailText) : [{ type: "paragraph", text: detailText }];
  if (Sheets.renderDetailBlocks) {
    Sheets.renderDetailBlocks(blocks, detail, {
      resolveXref: (name) => state.itemByName.get(name),
      appendText: appendAutoXrefs
    });
  } else {
    detail.textContent = detailText;
  }
  body.appendChild(detail);
  openModal();
  requestAnimationFrame(() => positionModalCard(trigger));
  if (write) writeHash({ item: itemId });
}

function openChangelogModal(trigger = document.activeElement) {
  state.lastFocus = trigger;
  state.modalMode = "changelog";
  $("#modalTitle").textContent = "完整更新";
  const logs = [...(state.data.changelog || [])].reverse();
  $("#modalBody").innerHTML = logs.map((log) => `
    <section class="log-detail">
      <h3>${escapeHtml(log.version)} <small>${escapeHtml(log.date || "")}</small></h3>
      <ul>${(log.entries || []).map((entry) => `<li>${renderTextWithXrefs(entry)}</li>`).join("")}</ul>
    </section>
  `).join("") || "<p>暂无更新记录。</p>";
  openModal();
  requestAnimationFrame(() => positionModalCard(trigger));
}

function openModal() {
  const modal = $("#modal");
  modal.hidden = false;
  modal.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
  $(".modal-card").focus();
}

// 详情弹窗跟着「点开它的那张卡片」走：横向对齐卡片中轴、纵向对齐卡片上沿，
// 超出视口就往回收。以前它按整个浏览器窗口居中，而卡片在菜单栏右边那一列，
// 所以看起来总是偏左一点（用户反馈「点了是歪的」）。
// 没有来源卡片时（深链 #item=xxx 直接打开、更新日志弹窗）保持窗口居中。
function positionModalCard(trigger) {
  const mask = $("#modal");
  const card = $(".modal-card", mask);
  if (!mask || !card) return;
  const anchor = trigger && trigger.closest ? trigger.closest(".card") : null;
  if (!anchor || mask.hidden) {
    mask.classList.remove("anchored");
    return;
  }
  const rect = anchor.getBoundingClientRect();
  if (!rect.width && !rect.height) {
    mask.classList.remove("anchored");
    return;
  }
  const pad = 16;
  const vw = window.innerWidth;
  // 用 visualViewport 的高度更准（移动端/带地址栏时 innerHeight 会偏大，
  // 按它算出来的 top 会让卡片底部被截在屏幕外）
  const vh = Math.round((window.visualViewport && window.visualViewport.height) || window.innerHeight);
  // 锚定状态下把卡片最高高度也钉在可视区内：卡片超出屏幕时，
  // 内容由卡片自身滚动，而不是整块被截掉（作者反馈过滚轮也看不到底部）
  mask.style.setProperty("--modal-max-h", `${Math.max(240, vh - pad * 2)}px`);
  const cw = card.offsetWidth;
  const ch = Math.min(card.offsetHeight, vh - pad * 2);
  const left = Math.max(pad, Math.min(rect.left + rect.width / 2 - cw / 2, vw - cw - pad));
  const top = Math.max(pad, Math.min(rect.top, vh - ch - pad));
  mask.classList.add("anchored");
  mask.style.setProperty("--modal-left", `${Math.round(left)}px`);
  mask.style.setProperty("--modal-top", `${Math.round(top)}px`);
}

function closeModal() {
  const modal = $("#modal");
  if (modal.hidden) return;
  modal.hidden = true;
  modal.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  if (state.modalMode === "item") writeHash({ item: "", sec: state.activeSec });
  state.modalMode = "";
  if (state.lastFocus && typeof state.lastFocus.focus === "function") state.lastFocus.focus();
}

function trapFocus(event) {
  if ($("#modal").hidden || event.key !== "Tab") return;
  const panel = $(".modal-card");
  const focusables = $$("a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex='-1'])", panel);
  if (!focusables.length) return;
  const first = focusables[0];
  const last = focusables[focusables.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function clearSearch() {
  state.query = "";
  writeHash({ q: "", item: "" });
  renderSections();
  $("#searchInput").focus();
}

function handleAction(action) {
  const id = action.dataset.id;
  const item = id ? state.itemById.get(id) : null;
  if (action.dataset.action === "detail" && item) openItemModal(id, action);
  if (action.dataset.action === "changelog") openChangelogModal(action);
  if ((action.dataset.action === "prev" || action.dataset.action === "next" || action.dataset.action === "dot") && item) {
    const images = Array.isArray(item.images) ? item.images.filter(Boolean) : [];
    if (images.length < 2) return;
    let index = state.carousel.get(id) || 0;
    if (action.dataset.action === "prev") index = (index - 1 + images.length) % images.length;
    if (action.dataset.action === "next") index = (index + 1) % images.length;
    if (action.dataset.action === "dot") index = Number(action.dataset.index || 0);
    state.carousel.set(id, Math.max(0, Math.min(index, images.length - 1)));
    renderSections();
  }
}

// 点一下就能申请入群：优先打开 QQ 的分享链接（全平台都能用），
// 万一链接失效则退回用 scheme 唤起 QQ；两种情况下都把群号显示出来 + 复制按钮兜底。
// 侧边栏与顶部菜单栏各有一个按钮，共用这一段逻辑。
function wireJoinGroup() {
  const openGroup = () => {
    const hint = $("#qqHint");
    if (hint) hint.hidden = false;
    if (QQ_GROUP_INVITE_URL) {
      window.open(QQ_GROUP_INVITE_URL, "_blank", "noopener");
      return;
    }
    try {
      window.location.href = QQ_GROUP_SCHEME;
    } catch (err) {
      // 浏览器不支持这个 scheme 时忽略即可，群号已经在侧边栏显示出来了
    }
  };

  ["#joinGroupBtn", "#joinGroupTopBtn"].forEach((selector) => {
    const btn = $(selector);
    if (btn) btn.addEventListener("click", openGroup);
  });

  const copy = $("#copyQqBtn");
  if (!copy) return;
  copy.addEventListener("click", () => {
    const done = () => {
      copy.textContent = "已复制";
      window.setTimeout(() => { copy.textContent = "复制群号"; }, 1600);
    };
    const fail = () => { copy.textContent = "请手动复制"; };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(QQ_GROUP_NUMBER).then(done).catch(fail);
    } else {
      fail();
    }
  });
}

function wireEvents() {
  $("#searchForm").addEventListener("submit", (event) => event.preventDefault());
  $("#searchInput").addEventListener("input", debounce((event) => {
    state.query = event.target.value.trim();
    writeHash({ q: state.query });
    renderSections();
  }));
  $("#clearSearchBtn").addEventListener("click", clearSearch);
  $("#emptyClearBtn").addEventListener("click", clearSearch);
  wireJoinGroup();

  document.addEventListener("click", (event) => {
    const close = event.target.closest("[data-close='modal']");
    if (close) {
      closeModal();
      return;
    }
    const chev = event.target.closest(".nav-chev");
    if (chev) {
      event.preventDefault();
      event.stopPropagation();
      toggleGroup(chev.closest(".nav-group"));
      return;
    }
    const row = event.target.closest(".nav-row");
    if (row) {
      const li = row.closest(".nav-group");
      const gid = row.dataset.sec;
      // 已经展开、而且点的就是当前这一卷 → 再点一次把它收起来（以前这里只会 openGroup，
      // 所以点标题永远收不回去，只有右边的小箭头能收）。收起时不跳转，避免"收菜单还把页面拉走"。
      if (li.classList.contains("open") && state.activeSec === gid) {
        closeGroup(li);
        return;
      }
      openGroup(li);
      state.activeSec = gid;
      setActiveSection(gid);
      clickJump(`sec-${gid}`);
      writeHash({ sec: gid });
      return;
    }
    const subItem = event.target.closest(".nav-sub a[data-item]");
    if (subItem) {
      event.preventDefault();
      jumpToItem(subItem.dataset.item);
      return;
    }
    const subLog = event.target.closest(".nav-sub a[data-log]");
    if (subLog) {
      event.preventDefault();
      scrollToSection(LOG_SECTION_ID);
      return;
    }
    const xref = event.target.closest(".xref");
    if (xref) {
      event.preventDefault();
      event.stopPropagation();
      closeModal();
      jumpToItem(xref.dataset.target);
      return;
    }
    const action = event.target.closest("[data-action]");
    if (action) {
      event.stopPropagation();
      handleAction(action);
      return;
    }
    const card = event.target.closest(".card[data-item-id]");
    if (card) openItemModal(card.dataset.itemId, card);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeModal();
    trapFocus(event);
    const card = event.target.closest?.(".card[data-item-id]");
    if (card && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      openItemModal(card.dataset.itemId, card);
    }
  });

  window.addEventListener("hashchange", () => {
    parseHash();
    renderSections();
    if (state.pendingItem) openItemModal(state.pendingItem, document.body, false);
    else if (state.activeSec) requestAnimationFrame(() => scrollToSection(state.activeSec, false));
  });
  window.addEventListener("scroll", scheduleScrollSpy, { passive: true });
  window.addEventListener("resize", () => {
    syncMastHeight();
    syncOpenHeights();
    scheduleScrollSpy();
    // 弹窗开着时窗口尺寸变了，重新贴回卡片
    if (!$("#modal").hidden) positionModalCard(state.lastFocus);
  });
}

async function init() {
  ensureShell();
  syncMastHeight();
  wireToTop();
  parseHash();
  state.data = await loadData();
  buildIndex();
  renderHeader();
  renderSections();
  wireEvents();
  // 字体加载完标题高度可能变，再量一次顶栏（否则侧栏第一行会被顶栏盖住）
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(syncMastHeight).catch(() => {});
  if (state.pendingItem) openItemModal(state.pendingItem, document.body, false);
  else if (state.activeSec) requestAnimationFrame(() => scrollToSection(state.activeSec, false));
}

init().catch((err) => {
  console.error(err);
  ensureShell();
  $("#sectionsRoot").innerHTML = `<div class="empty-state"><strong>未找到或无法解析 data.json。</strong><span>${escapeHtml(err.message || "请确认 data.json 位于仓库一级目录，并包含 site / sections / items / changelog / tele 五个数组。")}</span></div>`;
});
