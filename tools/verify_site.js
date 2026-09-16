// 灵界 Wiki —— 用真实站点代码验证 data.json
//
// 作用：直接把 site/js/sheetsContent.js 跑起来，喂进 data.json，
//       确认前台归一化后的结果正确（卷目、条目、词条跳转、图片解析）。
//       这样不用开浏览器也能验证数据能不能被站点正确读取。
//
// 用法：
//     node tools/verify_site.js
//
// 退出码 0 = 通过；1 = 失败。

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.dirname(__dirname);
const DATA_JSON = path.join(ROOT, "data.json");
const SHEETS_JS = path.join(ROOT, "site", "js", "sheetsContent.js");

const failures = [];
const warnings = [];

function check(cond, msg) {
  if (!cond) failures.push(msg);
}

// ---- 1. 读出 data.json ----
let data;
try {
  data = JSON.parse(fs.readFileSync(DATA_JSON, "utf8"));
} catch (err) {
  console.error("data.json 读取/解析失败：" + err.message);
  process.exit(1);
}

// ---- 2. 在沙箱里加载真实站点脚本 ----
// 极简 DOM 桩：够 renderDetailBlocks / appendInlineText 用，用来验证详情正文的渲染结果。
function makeElement(tag) {
  return {
    tagName: String(tag || "").toUpperCase(),
    children: [],
    attributes: {},
    content: { textContent: "" },
    className: "",
    hidden: false,
    dataset: {},
    style: {},
    src: "",
    alt: "",
    loading: "",
    _text: "",
    _html: "",
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    addEventListener() {},
    removeEventListener() {},
    setAttribute(k, v) {
      this.attributes[k] = String(v);
    },
    getAttribute(k) {
      return Object.prototype.hasOwnProperty.call(this.attributes, k) ? this.attributes[k] : null;
    },
    querySelector() {
      return null;
    },
    classList: { add() {}, remove() {}, contains: () => false },
    get textContent() {
      return this.children.length ? this.children.map((c) => c.textContent || "").join("") : this._text;
    },
    set textContent(v) {
      this._text = String(v ?? "");
      this.children = [];
    },
    get innerHTML() {
      return this._html;
    },
    set innerHTML(v) {
      this._html = String(v ?? "");
    },
  };
}

function walkElement(el, visit) {
  visit(el);
  for (const child of el.children || []) walkElement(child, visit);
}

const sandbox = {
  console,
  TextDecoder,
  Blob,
  Response,
  DecompressionStream,
  fetch: (url) => {
    const target = String(url);
    if (target.indexOf("data.json") >= 0) {
      return Promise.resolve(
        new Response(fs.readFileSync(DATA_JSON, "utf8"), {
          status: 200,
          headers: { "content-type": "application/json" },
        })
      );
    }
    return Promise.resolve(new Response("not found", { status: 404 }));
  },
  window: {},
  document: {
    createElement: (tag) => makeElement(tag),
    createTextNode: (t) => ({ tagName: "#TEXT", textContent: String(t ?? ""), children: [] }),
  },
  DOMParser: class {
    parseFromString() {
      throw new Error("verify 环境未提供 DOMParser");
    }
  },
};
sandbox.window = sandbox;
sandbox.self = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(SHEETS_JS, "utf8"), sandbox, { filename: "sheetsContent.js" });

const Sheets = sandbox.window.SheetsContent;
check(Sheets && typeof Sheets.buildContentFromSheets === "function", "sheetsContent.js 未导出 buildContentFromSheets");
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

// ---- 3. 用站点自己的逻辑归一化 ----
const built = Sheets.buildContentFromSheets(data);

// 站点要求 sections 与 items 都非空，否则 app.js 会抛「解析失败」
check(built.sections.length > 0, "归一化后 sections 为空");
check(built.items.length > 0, "归一化后 items 为空");

// 逐一核对：raw data.json 的可见条目都必须活下来
const rawVisible = data.items.filter((r) => !Sheets.isHidden(r["是否展示"]));
check(
  built.items.length === rawVisible.length,
  `条目数不符：data.json 可见 ${rawVisible.length} 条，归一化后 ${built.items.length} 条`
);

const sectionIds = new Set(built.sections.map((s) => s.id));
for (const item of built.items) {
  if (!sectionIds.has(item.section)) {
    failures.push(`条目 ${item.id} 的分类「${item.section}」不存在，前台不会显示`);
  }
  if (!item.name) failures.push(`条目 ${item.id} 没有名称`);
  if (!item.detailText) warnings.push(`条目 ${item.id} 详情为空`);
}
check(
  !built.sections.some((s) => s.id === "uncategorized"),
  "出现了 uncategorized 卷目，说明有条目的分类失配"
);

// ---- 4. 卡片图片：有图就必须真实存在（不存在的图会在前台留白）----
const withImages = built.items.filter((it) => Array.isArray(it.images) && it.images.filter(Boolean).length);
let missingCardImages = 0;
for (const it of withImages) {
  for (const img of it.images.filter(Boolean)) {
    const p = path.join(ROOT, String(img).split("/").join(path.sep));
    if (!fs.existsSync(p)) {
      missingCardImages += 1;
      failures.push(`条目 ${it.id} 的卡片图不存在：${img}`);
    }
  }
}

// ---- 5. 词条自动跳转 ----
const byId = new Map(built.items.map((it) => [it.id, it]));
const byName = new Map(built.items.map((it) => [it.name, it]));
let xrefOk = 0;
for (const row of built.tele) {
  const terms = String(row.field || "").split(/[，,、|;\n\r]+/).map((t) => t.trim()).filter(Boolean);
  const target = byId.get(row.target_id) || byName.get(row.target_id) || (terms.length === 1 ? byName.get(terms[0]) : null);
  if (!target) {
    failures.push(`词条「${row.field}」->「${row.target_id}」解析不到目标，自动跳转不会生效`);
  } else {
    xrefOk += 1;
  }
}

// ---- 5b. 所有条目名都要能自动跳转 ----
// 规则：每个条目按自己的名称登记成跳转词，tele 只用于别名。
// 曾经的问题：只登记 tele 表里的 37 个词，于是「尘火日志」这种没登记的物品名在正文里点不动。
check(typeof Sheets.buildXrefTerms === "function", "sheetsContent.js 未导出 buildXrefTerms（所有条目名自动跳转要用它）");
const xrefTerms = typeof Sheets.buildXrefTerms === "function"
  ? Sheets.buildXrefTerms(built.items, built.tele)
  : [];
const xrefTermMap = new Map(xrefTerms.map((row) => [row.term, row.id]));

let selfLinked = 0;
for (const item of built.items) {
  const key = String(item.name || "").toLowerCase().trim();
  if (!key) continue;
  if (xrefTermMap.get(key) !== item.id) {
    failures.push(`条目「${item.name}」没有登记成跳转词，正文里引用它不会变成链接`);
  } else {
    selfLinked += 1;
  }
}

// 长词优先：短名不能把长名截断（魔核 / 魔核碎片、日志 / 尘火日志）
const order = xrefTerms.map((row) => row.term);
for (const [longer, shorter] of [["魔核碎片", "魔核"], ["尘火日志", "日志"], ["彼岸花根", "彼岸花"]]) {
  const a = order.indexOf(longer.toLowerCase());
  const b = order.indexOf(shorter.toLowerCase());
  if (a < 0 || b < 0) {
    failures.push(`跳转词表里缺少「${longer}」或「${shorter}」`);
  } else if (a > b) {
    failures.push(`跳转词表排序错误：「${longer}」应排在「${shorter}」前面，否则会被短词抢先匹配`);
  }
}

// 用真实的正则拼法验证一次：风干的羽毛正文里的「尘火日志」必须匹配到尘火日志这张卡
function escapeRegExp(value) {
  return String(value ?? "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
const xrefPattern = order.length ? new RegExp(order.map(escapeRegExp).join("|"), "gi") : null;
const feather = built.items.find((it) => it.id === "lj_dried_camel_feathers");
if (xrefPattern && feather) {
  const hits = feather.detailText.match(xrefPattern) || [];
  const wanted = hits.map((h) => xrefTermMap.get(h.toLowerCase().trim())).filter(Boolean);
  if (!wanted.includes("lj_dust_log")) {
    failures.push("风干的羽毛正文里的「尘火日志」没有匹配到 lj_dust_log，点不动");
  }
  // 「日志」这个短词不能把「尘火日志」截成两半
  if (hits.some((h) => h.trim() === "日志") && feather.detailText.includes("尘火日志")) {
    const bad = hits.filter((h) => h.trim() === "日志").length;
    failures.push(`风干的羽毛正文里「日志」被单独匹配了 ${bad} 次，说明短词抢了长词的匹配`);
  }
}

// ---- 6. 配方：确认图标语法能被 parseRecipe 正确切分 ----
function splitRecipe(recipe) {
  return String(recipe || "")
    .split(/(\[\[[^\]]+\]\]|\[[^\]]+\])/g)
    .filter(Boolean)
    .map((part) => {
      if (/^\[\[([^\]]+)\]\]$/.test(part)) return { type: "xref", value: part.slice(2, -2) };
      const m = part.match(/^\[([^\]]+)\]$/);
      if (m) return { type: "icon", value: m[1].trim() };
      return { type: "text", value: part };
    });
}
let recipes = 0;
let icons = 0;
let missingIconFiles = 0;
for (const item of built.items) {
  if (!item.recipe) continue;
  recipes += 1;
  for (const seg of splitRecipe(item.recipe)) {
    if (seg.type !== "icon") continue;
    icons += 1;
    const fsPath = path.join(ROOT, seg.value.split("/").join(path.sep));
    if (!fs.existsSync(fsPath)) {
      missingIconFiles += 1;
      failures.push(`条目 ${item.id} 的配方图标文件不存在：${seg.value}`);
    }
  }
}

// ---- 7. 详情正文里的图片：必须真实存在，且必须真的渲染出来 ----
// 两种写法都要照顾到：
//   行内小图标  [images/xxx.png]        与制作配方同款，渲染成 <img class="recipe-icon">
//   整段插图    [[图片:images/xxx.png|说明]]  独立成段，渲染成 .detail-image-block 的 <img>
// 曾经的问题：详情走的渲染函数只认 [[...]]，导致行内那种在前台显示成裸路径文本。
const INLINE_PART_SPLIT_RE = /(\[\[[^\]]+\]\]|\[[^[\]]+\.(?:png|jpe?g|webp|gif|svg)\])/gi;
const INLINE_PART_RE = /^\[([^[\]]+\.(?:png|jpe?g|webp|gif|svg))\]$/i;
// 只在「漏渲染」检查里用：排除 [[图片:xxx.png]] 这种双中括号写法
const INLINE_LEFTOVER_RE = /(?<!\[)\[[^[\]]+\.(?:png|jpe?g|webp|gif|svg)\](?!\])/i;
const BLOCK_IMAGE_RE = /^\[\[(?:图片|image):([^|\]]+)(?:\|[^\]]*)?\]\]$/i;

function inlineImageRefs(text) {
  return String(text || "")
    .split(INLINE_PART_SPLIT_RE)
    .map((part) => part.match(INLINE_PART_RE))
    .filter(Boolean)
    .map((m) => m[1].trim());
}

// 整段插图必须独占一段（前后留空行），与站点 parseDetailBlocks 的判定一致
function blockImageRefs(text) {
  return String(text || "")
    .split(/\n{2,}/)
    .map((part) => part.trim().match(BLOCK_IMAGE_RE))
    .filter(Boolean)
    .map((m) => m[1].trim());
}

let detailRefs = 0;
let detailBlockRefs = 0;
let detailRefsMissing = 0;
let detailIconsRendered = 0;
let detailItemsWithRefs = 0;
for (const item of built.items) {
  const refs = inlineImageRefs(item.detailText);
  const blockRefs = blockImageRefs(item.detailText);
  detailRefs += refs.length;
  detailBlockRefs += blockRefs.length;
  if (refs.length || blockRefs.length) detailItemsWithRefs += 1;
  for (const ref of refs.concat(blockRefs)) {
    const fsPath = path.join(ROOT, ref.split("/").join(path.sep));
    if (!fs.existsSync(fsPath)) {
      detailRefsMissing += 1;
      failures.push(`条目 ${item.id} 详情正文引用的图片不存在：${ref}`);
    }
  }

  // 用真实渲染函数跑一遍，确认引用真的变成了 <img>，且正文不留裸路径
  const root = sandbox.document.createElement("div");
  const blocks = Sheets.parseDetailBlocks(item.detailText || "");
  Sheets.renderDetailBlocks(blocks, root, {
    resolveXref: () => null,
    appendText: (container, text) => container.appendChild(sandbox.document.createTextNode(text)),
  });
  let iconsHere = 0;
  const leftovers = [];
  walkElement(root, (el) => {
    if (el.tagName === "IMG") iconsHere += 1;
    if (el.tagName === "#TEXT" && INLINE_LEFTOVER_RE.test(el.textContent || "")) leftovers.push(el.textContent);
  });
  detailIconsRendered += iconsHere;
  const expected = refs.length + blockRefs.length;
  if (iconsHere !== expected) {
    failures.push(`条目 ${item.id} 详情正文的图片渲染数量不符：引用 ${expected} 个（行内 ${refs.length} + 整段 ${blockRefs.length}），渲染出 ${iconsHere} 个`);
  }
  if (leftovers.length) {
    failures.push(`条目 ${item.id} 详情正文仍有未渲染的图片路径文本：${leftovers[0].slice(0, 60)}`);
  }
}

// ---- 8. 走一遍站点真正使用的加载入口 loadContentJson ----
(async () => {
  check(typeof Sheets.loadContentJson === "function", "sheetsContent.js 未导出 loadContentJson（站点无法读取 data.json）");
  let loaded = null;
  try {
    loaded = await Sheets.loadContentJson();
  } catch (err) {
    failures.push(`loadContentJson() 抛错：${err.message}`);
  }
  if (loaded) {
    check(!!loaded.data, "loadContentJson() 没有返回 data");
    check(loaded.source === "./data.json", `loadContentJson() 的 source 不是 ./data.json：${loaded.source}`);
    check(
      loaded.data.items.length === built.items.length,
      `loadContentJson() 与 buildContentFromSheets() 结果不一致：${loaded.data.items.length} vs ${built.items.length}`
    );
  }

  // ---- 9. 输出 ----
  console.log("站点代码验证结果（真实 sheetsContent.js）");
  console.log(`  卷目 ${built.sections.length} 个`);
  console.log(`  条目 ${built.items.length} 个（data.json 可见 ${rawVisible.length} 个）`);
  console.log(`  词条自动跳转：别名 ${xrefOk} / ${built.tele.length} 条生效；共 ${xrefTerms.length} 个跳转词，其中条目名自带 ${selfLinked} 个`);
  console.log(`  配方法 ${recipes} 条，其中图标 ${icons} 个，缺失 ${missingIconFiles} 个`);
  console.log(`  详情正文图片：${detailItemsWithRefs} 个条目共 ${detailRefs} 处行内图标 + ${detailBlockRefs} 处整段插图，渲染出 ${detailIconsRendered} 个，缺失 ${detailRefsMissing} 个`);
  console.log(`  卡片图片：${withImages.length} 个条目带图，缺失 ${missingCardImages} 个`);
  console.log(`  加载入口：${loaded ? "loadContentJson() 正常" : "loadContentJson() 失败"}`);
  if (built.sections.length) {
    console.log("  卷目清单：");
    for (const s of built.sections) {
      const n = built.items.filter((it) => it.section === s.id).length;
      console.log(`    ${s.id.padEnd(10)} ${s.name.padEnd(10)} ${n} 条`);
    }
  }
  const sample = built.items[0];
  if (sample) {
    console.log("  样例条目：");
    console.log(`    id=${sample.id} 名称=${sample.name} 分类=${sample.section}`);
    console.log(`    标签=${JSON.stringify(sample.tags)}`);
    console.log(`    配方=${sample.recipe}`);
    console.log(`    详情长度=${sample.detailText.length} 字`);
  }
  if (warnings.length) {
    console.log(`\n警告 ${warnings.length} 条：`);
    for (const w of warnings) console.log("  ! " + w);
  }
  if (failures.length) {
    console.log(`\n失败 ${failures.length} 条：`);
    for (const f of failures) console.log("  x " + f);
    process.exit(1);
  }
  console.log("\n没有失败项 ✓");
})();
