# -*- coding: utf-8 -*-
"""把「淬铁灵剑」手持外观做成网站鼠标光标图。

素材来源（dst-app 导出，见 tools/export_sword_held.lua）：
    lj_ordinary_sword.zip 的 **BUILD** 动画第 1 帧 —— 这就是游戏里握在手上那一版
    （bank/build 都是 lj_ordinary_sword；物品栏/地面用的是 idle 动画的
     lj_ordinary_sword_1 符号，两版方向相反，别搞混）。

处理：裁掉透明边 → 缩放到指定剑长 → 逆时针转 45°（剑尖朝左上，像普通箭头那样）
      → 留 2px 边距放进正方形画布 → 输出 RGBA PNG，并打印热点坐标。

用法：
    python tools/make_sword_cursor.py                     # 用 .work/sword_build.png
    python tools/make_sword_cursor.py <源图> [输出路径] [剑长像素]
"""

import io
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = os.path.join(ROOT, ".work", "sword_build.png")
DEFAULT_OUT = os.path.join(ROOT, "images", "cursor_sword.png")
DEFAULT_LEN = 76          # 剑的像素长度（转 45° 后的对角线长）；52 太细看不清，76 正好
ANGLE = 45                # 逆时针 45°：剑尖从正上方转到左上方
PAD = 2                   # 画布四周留白，免得剑尖正好贴在边缘
ALPHA_MIN = 40            # 认为「有像素」的 alpha 阈值


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    length = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_LEN

    if not os.path.exists(src):
        raise SystemExit("找不到源图：%s" % src)

    img = Image.open(src).convert("RGBA")
    img = img.crop(img.getbbox())                      # 去掉透明边

    scale = float(length) / img.height
    img = img.resize((max(1, int(round(img.width * scale))), length), Image.LANCZOS)

    img = img.rotate(ANGLE, expand=True, resample=Image.BICUBIC)
    img = img.crop(img.getbbox())

    canvas = Image.new("RGBA", (img.width + PAD * 2, img.height + PAD * 2), (0, 0, 0, 0))
    canvas.paste(img, (PAD, PAD))

    # 热点取剑尖：朝左上最远的那个不透明像素
    px = canvas.load()
    best = None
    for y in range(canvas.height):
        for x in range(canvas.width):
            if px[x, y][3] < ALPHA_MIN:
                continue
            score = x + y
            if best is None or score < best[0]:
                best = (score, x, y)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.save(out)
    print("已生成 %s  (%dx%d)" % (out, canvas.width, canvas.height))
    print("热点（剑尖）坐标：%d %d" % (best[1], best[2]) if best else "热点：没找到不透明像素")


if __name__ == "__main__":
    main()
