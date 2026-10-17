#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查站点的自制字体子集有没有缺字。

背景：卡片标题用的 "Lingjie Titles"（思源宋体 Heavy 的子集）只收录了做子集那一刻
的「名称 + 标签 + 卷目名」。之后新增条目时，如果标题里出现子集里没有的字，
浏览器不会报错，只会**静默回退**成系统宋体——看起来就是同一行里混用两种字体。

用法：
    python tools/check_fonts.py          # 有缺字时退出码 1
    python tools/check_fonts.py --quiet  # 只打印结论

缺字时的处理：按 script 末尾打印的命令重新子集化
（源字体下载地址与 fontTools 用法见 注释.md 的「卡片标题的字体」一节）。
"""

import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data.json")
FONTS = os.path.join(ROOT, "site", "fonts")

# 字体文件 -> (中文名, 用途说明)。字体名与 styles.css 的 @font-face 保持一致。
FACES = {
    "lingjie-titles-heavy.woff2": ("Lingjie Titles", "所有卡片标题（.card-title-preview）"),
    "zihun-tanyue-shoushu.woff2": ("Lingjie Title", "站名（.site-name）"),
    "bellefair.ttf": ("DST Bellefair", "顶栏英文名与版本徽章"),
}

RESUBMIT_CMD = """重新子集化（缺字时跑一次）：

  # 1) 源字体（22.9MB，放 .work/font/ 即可，不用提交）
  Invoke-WebRequest -Uri "https://github.com/notofonts/noto-cjk/raw/main/Serif/OTF/SimplifiedChinese/NotoSerifCJKsc-Black.otf" -OutFile ".work/font/NotoSerifSC-Black.otf"

  # 2) 把下面的字全部写进 --text（本脚本的 --print-text 能直接生成这一行）
  python tools/check_fonts.py --print-text > .work/font/chars.txt
  python -m fontTools.subset ".work/font/NotoSerifSC-Black.otf" `
      --text-file=".work/font/chars.txt" --flavor=woff2 --no-hinting `
      --output-file=site/fonts/lingjie-titles-heavy.woff2
"""

LATIN = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .·-")


def load_data():
    return json.load(io.open(DATA, encoding="utf-8"))


def title_charset(d):
    """卡片标题会渲染到的全部文字。"""
    out = []
    for it in d["items"]:
        out.append(it.get("名称") or "")
        out.append(it.get("标签") or "")
    for sec in d["sections"]:
        out.append(sec.get("分类名") or "")
        out.append(sec.get("短名") or "")
    out.append(d["site"][0].get("网站标题") or "")
    return "".join(out)


def needed_text(d, face):
    if face == "Lingjie Titles":
        return title_charset(d)
    if face == "Lingjie Title":
        return d["site"][0].get("网站标题") or ""
    if face == "DST Bellefair":
        return (d["site"][0].get("网站英文名") or "") + (d["site"][0].get("网站版本") or "") + LATIN
    return ""


def cmap_of(path):
    from fontTools.ttLib import TTFont

    f = TTFont(path)
    chars = set()
    for table in f["cmap"].tables:
        chars |= set(table.cmap.keys())
    return chars


def main(argv):
    quiet = "--quiet" in argv
    d = load_data()

    if "--print-text" in argv:
        text = "".join(sorted({c for c in title_charset(d) if c not in "\n\r\t"}))
        sys.stdout.write(text)
        return 0

    try:
        import fontTools  # noqa: F401
    except ImportError:
        print("跳过字体检查：没装 fonttools（pip install fonttools brotli）")
        return 0

    bad = 0
    for fname, (face, use) in FACES.items():
        path = os.path.join(FONTS, fname)
        if not os.path.exists(path):
            print("缺文件：site/fonts/%s" % fname)
            bad += 1
            continue
        have = cmap_of(path)
        need = {c for c in needed_text(d, face) if c not in "\n\r\t "}
        missing = sorted(c for c in need if ord(c) not in have)
        if missing:
            bad += 1
            if not quiet:
                print("✗ %s（%s）缺 %d 个字：%s" % (face, use, len(missing), "".join(missing)[:160]))
        elif not quiet:
            print("✓ %-15s %-34s 收录 %d 字，覆盖 %d 字，不缺" % (face, use, len(have), len(need)))

    if bad:
        print("\n有 %d 款字体缺字，会出现字体混排（同一行里两种字体）。" % bad)
        print(RESUBMIT_CMD)
        return 1
    if not quiet:
        print("\n字体子集齐了 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
