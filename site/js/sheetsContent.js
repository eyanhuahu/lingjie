(function () {
  const PRIMARY_IMAGE_BASE_PATH = "images/";
  const DEFAULT_PLACEHOLDER_IMAGE = "images/placeholder.jpg";
  const CONTENT_JSON_URL = "./data.json";
  const CONTENT_WORKBOOK_URL = "./content.xlsx";
  const SHEET_NAMES = ["site", "sections", "items", "changelog", "tele", "images"];
  let imageAliasMap = new Map();

  const HEADER_MAPS = {
    site: {
      "网站标题": "name", "标题": "name", "name": "name",
      "网站版本": "version", "版本": "version", "version": "version",
      "网站英文名": "en_name", "英文名": "en_name", "en_name": "en_name",
      "作者": "author", "author": "author"
    },
    sections: {
      "分类id": "id", "分类ID": "id", "id": "id",
      "分类名": "name", "分类名称": "name", "name": "name",
      "短名": "shortName", "简称": "shortName", "shortName": "shortName",
      "英文名": "nameEn", "英文短名": "shortNameEn",
      "排序值": "sort_order", "排序": "sort_order", "sort_order": "sort_order",
      "是否展示": "visible", "展示": "visible", "visible": "visible"
    },
    items: {
      "id": "id",
      "分类id": "section", "分类ID": "section", "section": "section",
      "名称": "name", "标题": "name", "name": "name",
      "英文名": "nameEn",
      "标签": "tags", "tags": "tags",
      "英文标签": "tagsEn", "tagsEn": "tagsEn",
      "图片": "image", "图片地址": "image", "image": "image",
      "制作配方": "recipe", "配方": "recipe", "recipe": "recipe",
      "英文配方": "recipeEn", "recipeEn": "recipeEn",
      "简介": "summary", "摘要": "summary", "summary": "summary",
      "英文简介": "summaryEn", "summaryEn": "summaryEn",
      "详情": "detail", "detail": "detail",
      "英文详情": "detailEn", "detailEn": "detailEn",
      "排序值": "sort_order", "排序": "sort_order", "sort_order": "sort_order",
      "是否展示": "visible", "展示": "visible", "visible": "visible"
    },
    changelog: {
      "日志版本": "version", "版本": "version", "version": "version",
      "日期": "date", "date": "date",
      "内容": "content", "content": "content",
      "英文内容": "contentEn", "contentEn": "contentEn",
      "是否展示": "visible", "展示": "visible", "visible": "visible"
    },
    tele: {
      "导向id": "target_id", "导向ID": "target_id", "target_id": "target_id",
      "字段": "field", "词条": "field", "关键词": "field", "名称": "field", "field": "field", "term": "field", "terms": "field",
      "说明": "note", "note": "note",
      "是否展示": "visible", "展示": "visible", "visible": "visible"
    },
    images: {
      "图片名": "name", "name": "name",
      "文件名": "filename", "filename": "filename",
      "说明": "note", "note": "note",
      "是否展示": "visible", "展示": "visible", "visible": "visible"
    }
  };

  function compactHeader(header) {
    return String(header ?? "").trim().replace(/\s+/g, "").toLowerCase();
  }

  function mapHeader(sheetName, header) {
    const map = HEADER_MAPS[sheetName] || {};
    const raw = String(header ?? "").trim();
    return map[raw] || map[compactHeader(raw)] || "";
  }

  function isHidden(value) {
    return ["false", "否", "no", "0"].includes(String(value ?? "").trim().toLowerCase());
  }

  function sortValue(row) {
    const value = Number(row.sort_order);
    return Number.isFinite(value) ? value : Number.POSITIVE_INFINITY;
  }

  function rowsToObjects(rows) {
    const nonEmptyRows = rows.filter((cells) => cells.some((cell) => String(cell ?? "").trim() !== ""));
    if (!nonEmptyRows.length) return [];
    const headers = nonEmptyRows[0].map((header) => String(header ?? "").trim());
    return nonEmptyRows.slice(1).map((cells) => {
      const obj = {};
      headers.forEach((header, index) => {
        obj[header] = String(cells[index] ?? "").trim();
      });
      return obj;
    });
  }

  function firstCell(row) {
    const firstKey = Object.keys(row)[0];
    return String(row[firstKey] ?? "").trim();
  }

  function normalizeSheetRows(sheetName, rows) {
    return rows
      .filter((row) => {
        const first = firstCell(row);
        return first && !first.startsWith("#");
      })
      .map((row) => {
        const normalized = {};
        Object.entries(row).forEach(([header, value]) => {
          const key = mapHeader(sheetName, header);
          if (key) normalized[key] = String(value ?? "").trim();
        });
        return normalized;
      });
  }

  function splitList(value) {
    return String(value ?? "")
      .split(/[，,、|;\n\r]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function isHttpUrl(value) {
    return /^https?:\/\//i.test(String(value ?? "").trim());
  }

  function looksLikeImageFilename(value) {
    const text = String(value ?? "").trim();
    if (!text || isHttpUrl(text) || /[\\/]/.test(text)) return false;
    return /\.(jpe?g|png|webp|gif|svg)$/i.test(text);
  }

  function imageAlias(value) {
    return imageAliasMap.get(String(value ?? "").trim()) || "";
  }

  function toLocalImagePath(filename) {
    const clean = String(filename ?? "").trim().replace(/^\/+/, "");
    if (!clean) return "";
    if (clean.startsWith(PRIMARY_IMAGE_BASE_PATH)) return clean;
    return `${PRIMARY_IMAGE_BASE_PATH}${clean}`;
  }

  function resolveImagePath(path) {
    const clean = String(path ?? "").trim();
    if (!clean) return "";
    const alias = imageAlias(clean);
    if (alias) return resolveImagePath(alias);
    if (isHttpUrl(clean) || clean.startsWith(PRIMARY_IMAGE_BASE_PATH)) return clean;
    if (looksLikeImageFilename(clean)) return toLocalImagePath(clean);
    return "";
  }

  function resolveImage(row) {
    return resolveImagePath(row?.image) || DEFAULT_PLACEHOLDER_IMAGE;
  }

  function plainTextFromHtml(html) {
    const template = document.createElement("template");
    template.innerHTML = String(html ?? "")
      .replace(/<\/p>\s*<p[^>]*>/gi, "\n\n")
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<\/li>\s*<li[^>]*>/gi, "\n")
      .replace(/<\/h[1-6]>\s*/gi, "\n\n")
      .replace(/<h[1-6][^>]*>/gi, "");
    return template.content.textContent || "";
  }

  // 详情正文的结构识别。
  // 整篇文字一个粗细、一个层级时读起来很累（尤其是一堆数字），所以把三类内容认出来交给 CSS：
  //   heading 小标题   —— 「升阶方式」「击杀掉落」「每阶经验门槛（…）」
  //   sub     缩进条目 —— 以全角空格开头的一行（原本只靠空格缩进，看不出层级）
  //   table   数据表   —— 「凡境　50 · 100 · …」这种「短标签 + 全角空格 + 内容」的行
  // 注意：正文里这几种常常**挤在同一段**（标题行紧跟缩进行，中间没有空行），
  // 所以按行分类再分组，而不是一整段判一个类型。
  // 规则写得保守：拿不准就当普通文字，宁可不加样式也不能看错。
  const DETAIL_TABLE_ROW_RE = /^([^\s　]{1,8})　(\S.*)$/;
  const DETAIL_HEADING_LABEL_RE = /^[^。，、；：！？\n]{2,12}（[^）]*）$/;

  function isDetailHeadingLine(line) {
    const t = String(line).trim();
    if (!t) return false;
    // 「技能」「突破」「死亡惩罚」这类：短，且没有任何句读符号
    if (t.length <= 8 && !/[。，、；：！？（）()\[\]【】]/.test(t)) return true;
    // 「核心强化 —— 生命值」这类：短标签 + 破折号
    if (/^[^。，、；：！？\n]{2,12} —— \S+$/.test(t)) return true;
    // 「每境属性加成（达到该境界后生效）」这类：短标签 + 括号说明
    return DETAIL_HEADING_LABEL_RE.test(t);
  }

  function detailLineKind(rawLine) {
    const t = String(rawLine).trim();
    if (!t) return null;
    if (rawLine.startsWith("　")) return "sub";
    if (DETAIL_TABLE_ROW_RE.test(t)) return "table";
    if (isDetailHeadingLine(t)) return "heading";
    return "text";
  }

  // 把一段拆成若干块：连续同类型的行合成一块；数据表至少要 2 行才值得做成表格
  function expandDetailParagraph(text) {
    const blocks = [];
    let cur = null;
    const flush = () => {
      if (!cur) return;
      if (cur.type === "table" && cur.lines.length < 2) {
        // 孤零零一行「xx　yy」当普通文字处理，避免误做成表格
        blocks.push({ type: "text", text: cur.lines.join("\n") });
      } else {
        blocks.push({ type: cur.type, text: cur.lines.join("\n") });
      }
      cur = null;
    };
    String(text).split("\n").forEach((line) => {
      const kind = detailLineKind(line);
      if (kind === null) return;
      if (cur !== null && cur.type === kind) {
        cur.lines.push(line);
        return;
      }
      flush();
      cur = { type: kind, lines: [line] };
    });
    flush();
    return blocks;
  }

  function parseDetailBlocks(detailText) {
    const text = String(detailText ?? "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
    if (!text) return [];

    const blocks = [];
    text.split(/\n{2,}/).forEach((part) => {
      const trimmed = part.trim();
      const imageMatch = trimmed.match(/^\[\[(?:图片|image):([^|\]]+)(?:\|([^\]]+))?\]\]$/i);
      if (imageMatch) {
        const raw = imageMatch[1].trim();
        blocks.push({
          type: "image",
          src: resolveImagePath(raw),
          raw,
          caption: String(imageMatch[2] ?? "").trim()
        });
        return;
      }
      // 注意：这里**不能**把每行前面的全角缩进 trim 掉，否则同一组缩进行里
      // 首行会掉出「缩进条目」分类，样式忽有忽无。只去掉首尾空行。
      const lines = part.split("\n");
      while (lines.length && !lines[0].trim()) lines.shift();
      while (lines.length && !lines[lines.length - 1].trim()) lines.pop();
      expandDetailParagraph(lines.join("\n")).forEach((block) => blocks.push(block));
    });
    return blocks;
  }

  // 详情正文里的行内小图标：单个中括号里放一个图片路径，
  // 写法与「制作配方」字段完全一致，例如：
  //     阵眼：四季核心（[images/inventoryimages1/deerclops_eyeball.png] 巨鹿眼球 1、…）
  // 只认图片扩展名，避免把正文里别的方括号内容误当图片。
  const INLINE_IMAGE_PATTERN = "\\[[^\\[\\]]+\\.(?:png|jpe?g|webp|gif|svg)\\]";
  const INLINE_IMAGE_SPLIT_RE = new RegExp(`(\\[\\[[^\\]]+\\]\\]|${INLINE_IMAGE_PATTERN})`, "gi");
  const INLINE_IMAGE_RE = new RegExp(`^${INLINE_IMAGE_PATTERN}$`, "i");

  function appendInlineText(container, text, options = {}) {
    const source = String(text ?? "");
    const resolveXref = typeof options.resolveXref === "function" ? options.resolveXref : null;
    source.split(INLINE_IMAGE_SPLIT_RE).forEach((part) => {
      const imageMarker = part.match(/^\[\[(?:图片|image):/i);
      if (!imageMarker && INLINE_IMAGE_RE.test(part)) {
        const src = resolveImagePath(part.slice(1, -1).trim());
        if (src) {
          const img = document.createElement("img");
          img.className = "recipe-icon";
          img.src = src;
          img.alt = "";
          img.loading = "lazy";
          // 与制作配方一致：文件缺失就悄悄隐藏，不破坏正文排版。
          img.addEventListener("error", () => {
            img.hidden = true;
          });
          container.appendChild(img);
          return;
        }
      }
      const xref = part.match(/^\[\[([^\]]+)\]\]$/);
      if (!imageMarker && xref && resolveXref) {
        const target = resolveXref(xref[1].trim());
        if (target) {
          const a = document.createElement("a");
          a.className = "xref";
          a.href = `#item=${encodeURIComponent(target.id)}`;
          a.dataset.target = target.id;
          a.textContent = xref[1].trim();
          container.appendChild(a);
          return;
        }
      }
      if (!imageMarker && typeof options.appendText === "function") {
        options.appendText(container, part);
        return;
      }
      container.appendChild(document.createTextNode(part));
    });
  }

  function renderDetailBlocks(blocks, container, options = {}) {
    container.textContent = "";
    (blocks || []).forEach((block) => {
      if (block.type === "image") {
        const figure = document.createElement("figure");
        figure.className = "detail-image-block";

        if (block.src) {
          const img = document.createElement("img");
          img.src = block.src;
          img.alt = block.caption || block.raw || "详情图片";
          img.loading = "lazy";
          figure.appendChild(img);

          if (block.caption) {
            const caption = document.createElement("figcaption");
            caption.textContent = block.caption;
            figure.appendChild(caption);
          }

          const error = document.createElement("div");
          error.className = "detail-image-error";
          error.hidden = true;
          error.textContent = `图片未找到：${block.raw || block.src}。请确认图片已上传到 images/，且文件名大小写完全一致。`;
          figure.appendChild(error);
          img.addEventListener("error", () => {
            img.hidden = true;
            const caption = figure.querySelector("figcaption");
            if (caption) caption.hidden = true;
            error.hidden = false;
          });
        } else {
          const error = document.createElement("div");
          error.className = "detail-image-error";
          error.textContent = `图片未找到：${block.raw || ""}。请确认图片已上传到 images/，且文件名大小写完全一致。`;
          figure.appendChild(error);
        }

        container.appendChild(figure);
        return;
      }

      // 小标题：单独一行短标签，给个明显的层级
      if (block.type === "heading") {
        const h = document.createElement("h4");
        h.className = "detail-h";
        appendInlineText(h, block.text, options);
        container.appendChild(h);
        return;
      }

      // 数据表：短标签（境界名等）+ 内容，两栏对齐，隔行浅底色
      if (block.type === "table") {
        const wrap = document.createElement("div");
        wrap.className = "detail-table";
        String(block.text).split("\n").forEach((line) => {
          const t = line.trim();
          const m = t.match(DETAIL_TABLE_ROW_RE);
          if (m) {
            const row = document.createElement("div");
            row.className = "detail-row";
            const key = document.createElement("span");
            key.className = "detail-row-key";
            appendInlineText(key, m[1], options);
            const val = document.createElement("span");
            val.className = "detail-row-val";
            appendInlineText(val, m[2], options);
            row.appendChild(key);
            row.appendChild(val);
            wrap.appendChild(row);
          } else if (t) {
            const note = document.createElement("div");
            note.className = "detail-note";
            appendInlineText(note, t, options);
            wrap.appendChild(note);
          }
        });
        container.appendChild(wrap);
        return;
      }

      // 缩进条目：全角空格开头的行，按缩进层级显示成带竖线的条目
      if (block.type === "sub") {
        const wrap = document.createElement("div");
        wrap.className = "detail-sub-group";
        String(block.text).split("\n").forEach((line) => {
          if (!line.trim()) return;
          let level = 0;
          while (line.charAt(level) === "　") level += 1;
          const item = document.createElement("div");
          item.className = `detail-sub detail-sub-${Math.min(level, 3)}`;
          appendWithLeadLabel(item, line.slice(level), options);
          wrap.appendChild(item);
        });
        container.appendChild(wrap);
        return;
      }

      const p = document.createElement("p");
      appendTextBlock(p, block.text, options);
      container.appendChild(p);
    });
  }

  // 供校验脚本使用：只分类、不渲染，方便统计各类块的数量
  function classifyDetailText(detailText) {
    return parseDetailBlocks(detailText).map((block) => block.type);
  }

  // 正文里「短标签：内容」开头的短标签（技能名、字段名：晶爪猛击： / 生成范围：）单独包一层，
  // CSS 里加粗上色 —— 不然整段一个粗细，眼睛抓不住重点。
  // 规则保守：只在段落或条目**开头**认，长度 2~14，且不含句读符号；拿不准就当普通文字。
  const LEAD_LABEL_RE = /^([^。，、；：！？\n]{2,14})[：:]\s*/;

  function splitLeadLabel(text) {
    const source = String(text ?? "");
    const m = source.match(LEAD_LABEL_RE);
    if (!m) return null;
    return [m[1], source.slice(m[0].length)];
  }

  function appendWithLeadLabel(container, text, options) {
    const lead = splitLeadLabel(text);
    if (!lead) {
      appendInlineText(container, text, options);
      return;
    }
    const label = document.createElement("b");
    label.className = "detail-lead";
    appendInlineText(label, `${lead[0]}：`, options);
    container.appendChild(label);
    appendInlineText(container, lead[1], options);
  }

  // 普通文字块里**逐行**套短标签规则。
  // 连续的非空行会被合并成一个 text 块，只在整块开头匹配的话，
  // 只有第一行会加粗（「魔气环绕」粗了、「饥饿诅咒」没粗），所以必须按行处理。
  // 行间的换行单独作为文本节点塞进去，靠 CSS 的 white-space:pre-line 断行。
  function appendTextBlock(container, text, options) {
    const lines = String(text ?? "").split("\n");
    lines.forEach((line, index) => {
      if (index > 0) container.appendChild(document.createTextNode("\n"));
      appendWithLeadLabel(container, line, options);
    });
  }

  function readU16(view, offset) {
    return view.getUint16(offset, true);
  }

  function readU32(view, offset) {
    return view.getUint32(offset, true);
  }

  async function inflateRaw(bytes) {
    if (typeof DecompressionStream === "undefined") {
      throw new Error("当前浏览器不支持静态解析 xlsx，请使用现代浏览器打开页面。");
    }
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }

  async function unzipEntries(arrayBuffer) {
    const bytes = new Uint8Array(arrayBuffer);
    const view = new DataView(arrayBuffer);
    const decoder = new TextDecoder();
    let eocd = -1;
    for (let i = bytes.length - 22; i >= 0; i -= 1) {
      if (readU32(view, i) === 0x06054b50) {
        eocd = i;
        break;
      }
    }
    if (eocd < 0) throw new Error("content.xlsx 文件结构无效。");

    const total = readU16(view, eocd + 10);
    let offset = readU32(view, eocd + 16);
    const entries = new Map();
    for (let i = 0; i < total; i += 1) {
      if (readU32(view, offset) !== 0x02014b50) throw new Error("content.xlsx 文件目录损坏。");
      const method = readU16(view, offset + 10);
      const compressedSize = readU32(view, offset + 20);
      const nameLength = readU16(view, offset + 28);
      const extraLength = readU16(view, offset + 30);
      const commentLength = readU16(view, offset + 32);
      const localOffset = readU32(view, offset + 42);
      const name = decoder.decode(bytes.slice(offset + 46, offset + 46 + nameLength));

      const localNameLength = readU16(view, localOffset + 26);
      const localExtraLength = readU16(view, localOffset + 28);
      const dataStart = localOffset + 30 + localNameLength + localExtraLength;
      const compressed = bytes.slice(dataStart, dataStart + compressedSize);
      const data = method === 0 ? compressed : await inflateRaw(compressed);
      entries.set(name.replace(/\\/g, "/"), data);
      offset += 46 + nameLength + extraLength + commentLength;
    }
    return entries;
  }

  function xmlText(entries, path) {
    const data = entries.get(path);
    return data ? new TextDecoder().decode(data) : "";
  }

  function parseXml(xml) {
    return new DOMParser().parseFromString(xml, "application/xml");
  }

  function relTarget(basePath, target) {
    const stack = [];
    `${basePath}/${target}`.split("/").forEach((part) => {
      if (!part || part === ".") return;
      if (part === "..") stack.pop();
      else stack.push(part);
    });
    return stack.join("/");
  }

  function columnIndex(ref) {
    const letters = String(ref || "").match(/[A-Z]+/i)?.[0] || "A";
    return letters.toUpperCase().split("").reduce((value, char) => value * 26 + char.charCodeAt(0) - 64, 0) - 1;
  }

  function parseSharedStrings(entries) {
    const xml = xmlText(entries, "xl/sharedStrings.xml");
    if (!xml) return [];
    return Array.from(parseXml(xml).getElementsByTagName("si")).map((si) => {
      return Array.from(si.getElementsByTagName("t")).map((t) => t.textContent || "").join("");
    });
  }

  function parseWorksheet(xml, sharedStrings) {
    if (!xml) return [];
    return Array.from(parseXml(xml).getElementsByTagName("row")).map((rowEl) => {
      const cells = [];
      Array.from(rowEl.getElementsByTagName("c")).forEach((cell) => {
        const index = columnIndex(cell.getAttribute("r"));
        const type = cell.getAttribute("t");
        let value = "";
        if (type === "inlineStr") {
          value = Array.from(cell.getElementsByTagName("t")).map((t) => t.textContent || "").join("");
        } else {
          const raw = cell.getElementsByTagName("v")[0]?.textContent || "";
          value = type === "s" ? (sharedStrings[Number(raw)] || "") : raw;
        }
        cells[index] = value;
      });
      return cells.map((cell) => cell ?? "");
    });
  }

  async function parseXlsx(arrayBuffer) {
    const entries = await unzipEntries(arrayBuffer);
    const workbookXml = xmlText(entries, "xl/workbook.xml");
    const relsXml = xmlText(entries, "xl/_rels/workbook.xml.rels");
    if (!workbookXml || !relsXml) throw new Error("content.xlsx 缺少工作簿信息。");

    const workbook = parseXml(workbookXml);
    const rels = parseXml(relsXml);
    const relMap = new Map(Array.from(rels.getElementsByTagName("Relationship")).map((rel) => {
      return [rel.getAttribute("Id"), relTarget("xl", rel.getAttribute("Target") || "")];
    }));
    const sharedStrings = parseSharedStrings(entries);
    const rows = {};
    Array.from(workbook.getElementsByTagName("sheet")).forEach((sheet) => {
      const name = sheet.getAttribute("name") || "";
      const relId = sheet.getAttribute("r:id");
      const target = relMap.get(relId);
      if (name && target) rows[name] = rowsToObjects(parseWorksheet(xmlText(entries, target), sharedStrings));
    });
    return rows;
  }

  function normalizeSite(rows) {
    const row = normalizeSheetRows("site", rows)[0] || {};
    return {
      name: row.name || "灵界",
      en_name: row.en_name || "",
      version: row.version || "v0.1.0",
      author: row.author || "预留作者"
    };
  }

  function normalizeSections(rows) {
    return normalizeSheetRows("sections", rows)
      .filter((row) => row.id && !isHidden(row.visible))
      .sort((a, b) => sortValue(a) - sortValue(b))
      .map((row) => ({
        id: row.id,
        name: row.name || row.id,
        shortName: row.shortName || "",
        nameEn: row.nameEn || "",
        shortNameEn: row.shortNameEn || "",
      }));
  }

  function normalizeImages(rows) {
    return normalizeSheetRows("images", rows)
      .filter((row) => (row.name || row.filename) && !isHidden(row.visible))
      .map((row) => ({ name: row.name || "", filename: row.filename || "", note: row.note || "" }));
  }

  function normalizeItems(rows) {
    return normalizeSheetRows("items", rows)
      .filter((row) => row.id && !isHidden(row.visible))
      .sort((a, b) => sortValue(a) - sortValue(b))
      .map((row) => {
        const images = splitList(row.image);
        return {
          id: row.id,
          section: row.section || "uncategorized",
          name: row.name || row.id,
          nameEn: row.nameEn || "",
          tags: splitList(row.tags),
          tagsEn: splitList(row.tagsEn),
          images,
          resolved_image: resolveImage({ image: images[0] || "" }),
          recipe: row.recipe || "",
          recipeEn: row.recipeEn || "",
          summary: row.summary || "",
          summaryEn: row.summaryEn || "",
          detailText: row.detail || "",
          detailHtml: row.detail || "",
          detailTextEn: row.detailEn || "",
        };
      });
  }

  function normalizeChangelog(rows) {
    // 更新日志**按换行拆条目**（一条一行）。
    // 不能直接用通用的 splitList：它连「，」都会切开，一条完整的更新说明会被碎成好几行。
    // 没有换行时（表格里写成整行）再退回 splitList，保持兼容。
    const byLine = (value) => String(value || "").split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    return normalizeSheetRows("changelog", rows)
      .filter((row) => row.version && !isHidden(row.visible))
      .map((row) => ({
        version: row.version,
        date: row.date || "",
        entries: byLine(row.content).length > 1
          ? byLine(row.content)
          : (splitList(row.content).length ? splitList(row.content) : [row.content || ""]),
        entriesEn: byLine(row.contentEn)
      }));
  }

  function normalizeTele(rows) {
    return normalizeSheetRows("tele", rows)
      .filter((row) => !isHidden(row.visible))
      .filter((row) => row.target_id || row.field)
      .map((row) => ({
        target_id: row.target_id || "",
        field: row.field || "",
        note: row.note || ""
      }));
  }

  function buildContentFromSheets(sheetRows) {
    const images = normalizeImages(sheetRows.images || []);
    imageAliasMap = new Map(images.filter((image) => image.name && image.filename).map((image) => [image.name, image.filename]));
    const data = {
      site: normalizeSite(sheetRows.site || []),
      sections: normalizeSections(sheetRows.sections || []),
      items: normalizeItems(sheetRows.items || []),
      changelog: normalizeChangelog(sheetRows.changelog || []),
      tele: normalizeTele(sheetRows.tele || []),
      images
    };
    const sectionIds = new Set(data.sections.map((section) => section.id));
    if (data.items.some((item) => !sectionIds.has(item.section))) data.sections.push({ id: "uncategorized", name: "未分类" });
    if (data.changelog.length && !data.sections.some((section) => section.id === "log")) data.sections.push({ id: "log", name: "更新日志" });
    return data;
  }

  async function loadContentWorkbook() {
    const response = await fetch(CONTENT_WORKBOOK_URL, { cache: "no-store" });
    if (!response.ok) throw new Error("未找到 content.xlsx，请确认它位于仓库一级目录。");
    const rows = await parseXlsx(await response.arrayBuffer());
    return { rows, data: buildContentFromSheets(rows), source: CONTENT_WORKBOOK_URL };
  }

  // 自动跳转词表。
  // 规则：**每个条目都按自己的名称自动登记**，于是任何卡片正文里写到别的条目名都会变成链接；
  //       `tele` 表只用来登记别名（例如「魔兽森林」→ 蝴蝶岛），登记时覆盖同名条目；
  //       名字带括号说明的条目再额外登记「括号前的简称」（见下）。
  // 返回 [{ term, id }]，按词长从长到短排序——保证「魔核碎片」不会被「魔核」抢先匹配。
  const BASE_NAME_SUFFIX_RE = /\s*[（(][^）)]*[）)]\s*$/;

  function buildXrefTerms(items, tele) {
    const byId = new Map();
    const byName = new Map();
    (items || []).forEach((item) => {
      if (item.id) byId.set(item.id, item);
      if (item.name) byName.set(item.name, item);
    });

    const terms = new Map();
    (items || []).forEach((item) => {
      const key = String(item.name || "").toLowerCase().trim();
      if (key) terms.set(key, item.id);
    });
    (tele || []).forEach((row) => {
      const list = String(row.field || "")
        .split(/[，,、|;\n\r]+/)
        .map((term) => term.trim())
        .filter(Boolean);
      const target = byId.get(row.target_id)
        || byName.get(row.target_id)
        || (list.length === 1 ? byName.get(list[0]) : null);
      if (!target) return;
      list.forEach((term) => terms.set(term.toLowerCase().trim(), target.id));
    });

    // 条目名带括号说明的（「超凡丹（丹劫）」「噬魂蛇（隐藏 Boss）」「玄灵培育池（未实装）」），
    // 正文里一般只写括号前的简称，只登记全名的话这些引用全都链不上。
    // 简称放在最后登记，且已被占用（同名条目或 tele 别名）时不覆盖，
    // 匹配是「长词优先」，所以「噬魂蛇皮」不会被「噬魂蛇」抢走。
    (items || []).forEach((item) => {
      const name = String(item.name || "").trim();
      const base = name.replace(BASE_NAME_SUFFIX_RE, "").trim().toLowerCase();
      if (!base || base === name.toLowerCase()) return;
      if (!terms.has(base)) terms.set(base, item.id);
    });

    return Array.from(terms, ([term, id]) => ({ term, id }))
      .sort((a, b) => b.term.length - a.term.length);
  }

  // 站点当前使用的内容源：仓库一级目录的 data.json
  // 形状与 content.xlsx 解析产物一致（"表名" -> 行对象数组，键为第一行的中文表头），
  // 因此下游所有归一化逻辑（排序 / 是否展示 / 标签 / 图片别名 / 词条跳转）完全复用。
  async function loadContentJson() {
    let response;
    try {
      response = await fetch(CONTENT_JSON_URL, { cache: "no-store" });
    } catch (err) {
      throw new Error("无法读取 data.json（请确认它位于仓库一级目录，且页面通过 HTTP 打开而不是本地文件）。");
    }
    if (!response.ok) throw new Error("未找到 data.json，请确认它位于仓库一级目录。");
    let rows;
    try {
      rows = await response.json();
    } catch (err) {
      throw new Error("data.json 不是合法 JSON，请检查是否漏了逗号、引号或多写了注释。");
    }
    if (!rows || typeof rows !== "object" || Array.isArray(rows)) {
      throw new Error("data.json 顶层必须是一个对象，且包含 site / sections / items / changelog / tele 五个数组。");
    }
    return { rows, data: buildContentFromSheets(rows), source: CONTENT_JSON_URL };
  }

  window.SheetsContent = {
    PRIMARY_IMAGE_BASE_PATH,
    DEFAULT_PLACEHOLDER_IMAGE,
    CONTENT_JSON_URL,
    CONTENT_WORKBOOK_URL,
    SHEET_NAMES,
    HEADER_MAPS,
    parseXlsx,
    buildContentFromSheets,
    loadContentJson,
    loadContentWorkbook,
    isHidden,
    isHttpUrl,
    looksLikeImageFilename,
    toLocalImagePath,
    resolveImage,
    resolveImagePath,
    parseDetailBlocks,
    renderDetailBlocks,
    classifyDetailText,
    appendInlineText,
    buildXrefTerms,
    plainTextFromHtml
  };
})();
