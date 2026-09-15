# -*- coding: utf-8 -*-
"""
灵界 Wiki 内容校验器

检查 data.json 是否结构完整、引用自洽、配方图标路径真实存在。
每次改完 data.json 都建议跑一遍：

    python tools/validate_content.py

退出码 0 = 全部通过；1 = 有错误（错误会让前台缺内容或图片 404）。
"""

import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON = os.path.join(ROOT, "data.json")
IMAGES_DIR = os.path.join(ROOT, "images")

REQUIRED_TOP = ["site", "sections", "items", "changelog", "tele"]
HEADERS = {
    "site": ["网站标题", "网站版本", "作者"],
    "sections": ["分类id", "分类名", "排序值", "是否展示"],
    "items": ["id", "分类id", "名称", "标签", "图片", "制作配方", "简介", "详情", "排序值", "是否展示"],
    "changelog": ["日志版本", "日期", "内容"],
    "tele": ["导向id", "字段"],
}

errors = []
warnings = []

# 图标索引：文件名(小写) -> 相对路径，用于"路径写错时告诉你正确路径"
ICON_INDEX = {}
if os.path.isdir(IMAGES_DIR):
    for dirpath, _dirnames, filenames in os.walk(IMAGES_DIR):
        for fn in filenames:
            base = os.path.splitext(fn)[0].lower()
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace("\\", "/")
            ICON_INDEX.setdefault(base, rel)


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def icon_hint(path_text):
    """图标路径不存在时，尝试给出正确路径。"""
    base = os.path.splitext(os.path.basename(path_text.replace("\\", "/")))[0].lower()
    hit = ICON_INDEX.get(base)
    if hit:
        return "；它实际在 %s" % hit
    return "；images/ 下也没有叫 %s 的图标" % (base + ".png")


def main():
    if not os.path.exists(DATA_JSON):
        sys.stderr.write("找不到 data.json：%s\n" % DATA_JSON)
        return 1
    with io.open(DATA_JSON, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except ValueError as exc:
            sys.stderr.write("data.json 不是合法 JSON：%s\n" % exc)
            return 1

    # 1. 顶层键
    for key in REQUIRED_TOP:
        if key not in data:
            err("data.json 缺少顶层键：%s" % key)
        elif not isinstance(data[key], list):
            err("顶层键 %s 必须是数组" % key)
    if errors:
        report()
        return 1

    # 2. 表头完整性
    for sheet, headers in HEADERS.items():
        for i, row in enumerate(data[sheet]):
            for h in headers:
                if h not in row:
                    err("%s 第 %d 行缺少列：%s" % (sheet, i + 1, h))

    # 3. 卷目
    sec_ids = []
    for row in data["sections"]:
        sid = (row.get("分类id") or "").strip()
        if not sid:
            err("sections 存在空的分类id")
            continue
        if not re.match(r"^[A-Za-z0-9_\-]+$", sid):
            err("分类id 含非 ASCII 或非法字符：%s" % sid)
        if sid in sec_ids:
            err("分类id 重复：%s" % sid)
        sec_ids.append(sid)
        if not (row.get("分类名") or "").strip():
            warn("卷目 %s 没有分类名" % sid)
    sec_set = set(sec_ids)

    # 4. 条目
    seen_ids = {}
    seen_names = {}
    used_sections = {}
    for i, row in enumerate(data["items"]):
        iid = (row.get("id") or "").strip()
        name = (row.get("名称") or "").strip()
        sec = (row.get("分类id") or "").strip()
        line = "items 第 %d 行(%s)" % (i + 1, iid or "无 id")

        if not iid:
            err("%s：id 为空" % line)
            continue
        if not re.match(r"^[A-Za-z0-9_\-]+$", iid):
            err("%s：id 含空格 / 中文等非法字符" % line)
        if iid in seen_ids:
            err("%s：id 重复" % line)
        seen_ids[iid] = True

        if not name:
            err("%s：名称为空" % line)
        if name in seen_names:
            warn("%s：名称与 %s 重复（玩家搜索时可能混淆）" % (line, seen_names[name]))
        seen_names[name] = iid

        if sec not in sec_set:
            err("%s：分类id「%s」不在 sections 中，该条目不会显示" % (line, sec))
        else:
            used_sections[sec] = used_sections.get(sec, 0) + 1

        if not (row.get("详情") or "").strip():
            warn("%s：详情为空" % line)
        if not (row.get("简介") or "").strip():
            warn("%s：简介为空" % line)

        # 配方里的图标路径必须真实存在
        for m in re.finditer(r"\[([^\]\[]+)\]", row.get("制作配方") or ""):
            target = m.group(1).strip()
            if not target:
                continue
            if target.startswith("http://") or target.startswith("https://"):
                continue
            fs = os.path.join(ROOT, target.replace("/", os.sep))
            if not os.path.exists(fs):
                err("%s：配方图标不存在 -> %s%s" % (line, target, icon_hint(target)))

        # 详情里的 [[图片:xxx]]
        for m in re.finditer(r"\[\[(?:图片|image):([^|\]]+)", row.get("详情") or "", re.I):
            target = m.group(1).strip()
            if target.startswith("http://") or target.startswith("https://"):
                continue
            cand = [target, os.path.join("images", target)]
            if not any(os.path.exists(os.path.join(ROOT, c.replace("/", os.sep))) for c in cand):
                warn("%s：详情引用的图片未找到 -> %s" % (line, target))

        # 详情里的行内小图标 [images/xxx.png]（单个中括号 + 图片扩展名）
        # 前后加断言，避免把上面的 [[图片:xxx.png]] 也算进来
        for m in re.finditer(r"(?<!\[)\[([^\]\[]+\.(?:png|jpe?g|webp|gif|svg))\](?!\])", row.get("详情") or "", re.I):
            target = m.group(1).strip()
            if target.startswith("http://") or target.startswith("https://"):
                continue
            fs = os.path.join(ROOT, target.replace("/", os.sep))
            if not os.path.exists(fs):
                err("%s：详情里的行内图标不存在 -> %s%s" % (line, target, icon_hint(target)))

        # 卡片图片字段
        img = (row.get("图片") or "").strip()
        if img:
            cand = [img, os.path.join("images", img)]
            if not any(os.path.exists(os.path.join(ROOT, c.replace("/", os.sep))) for c in cand):
                warn("%s：图片字段指向的文件不存在 -> %s" % (line, img))

    # 5. 没有条目的卷目
    for sid in sec_ids:
        if sid == "log":
            continue
        if sid not in used_sections:
            warn("卷目「%s」下没有任何条目，前台会显示「暂无条目」" % sid)

    # 6. tele 引用
    seen_terms = {}
    for i, row in enumerate(data["tele"]):
        tid = (row.get("导向id") or "").strip()
        term = (row.get("字段") or "").strip()
        line = "tele 第 %d 行(%s)" % (i + 1, term or tid or "空")
        if not tid and not term:
            err("%s：导向id 与 字段 都为空" % line)
            continue
        candidates = [t.strip() for t in re.split(r"[，,、|;\n\r]+", tid) if t.strip()]
        if not candidates:
            candidates = [t.strip() for t in re.split(r"[，,、|;\n\r]+", term) if t.strip()]
        for cand in candidates:
            if cand not in seen_ids and cand not in seen_names:
                err("%s：导向id「%s」既不是条目 id 也不是条目名称，自动跳转会静默失效" % (line, cand))
        if term in seen_terms:
            err("%s：字段「%s」与第 %s 行重复" % (line, term, seen_terms[term]))
        seen_terms[term] = i + 1

    # 7. 统计
    sys.stdout.write("data.json 校验结果\n")
    sys.stdout.write("  卷目 %d 个，条目 %d 个，词条 %d 条，更新日志 %d 条\n" % (
        len(data["sections"]), len(data["items"]), len(data["tele"]), len(data["changelog"])))
    for row in sorted(data["sections"], key=lambda r: int(r.get("排序值") or 9999)):
        sid = row["分类id"]
        sys.stdout.write("    %-10s %-10s %d 条\n" % (sid, row.get("分类名", ""), used_sections.get(sid, 0)))
    report()
    return 1 if errors else 0


def report():
    if warnings:
        sys.stdout.write("\n警告 %d 条：\n" % len(warnings))
        for w in warnings:
            sys.stdout.write("  ! %s\n" % w)
    if errors:
        sys.stdout.write("\n错误 %d 条：\n" % len(errors))
        for e in errors:
            sys.stdout.write("  x %s\n" % e)
    else:
        sys.stdout.write("\n没有错误 ✓\n")


if __name__ == "__main__":
    sys.exit(main())
