# -*- coding: utf-8 -*-
"""把荒界纳物箱界面上的 5 个按钮合成到箱体 UI 图上。

为什么要合成：按钮在游戏里是**独立的 UI 贴图**（来自 images/ethereal_realm_ui 图集），
不属于箱体的动画帧，所以单独导出的箱体 UI 上没有按钮。

坐标来源（lj_mod/scripts/main/ui/containers.lua）：
    箱体面板 pos = (0, 250)，按钮 pos 是各自的中心点：
    sort(-415,230) collect(-85,250) fresh(85,250) store(250,-185) close(400,-85)
DST 的 UI 坐标 +y 朝上、图片像素 +y 朝下，所以合成时要翻过来。
按钮有几个本来就落在箱体图之外（下方 / 右侧），所以画布会**自动扩大到刚好包住全部内容**。

用法：
    python tools/compose_box_ui.py [面板图] [按钮目录] [输出]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(ROOT, ".work", "huangjie_open.png")
BUTTONS = os.path.join(ROOT, ".work", "ui_buttons")
OUT = os.path.join(ROOT, "images", "lingjie", "anim", "huangjie_box_ui.png")

PANEL_POS = (0, 250)          # 面板中心在 UI 坐标里的位置
PAD = 8                       # 画布四周留一点白
BUTTONS_LIST = [
    ("lj_huangjie_box_sort_normal.png", -415, 230),
    ("lj_huangjie_box_collect.png", -85, 250),
    ("lj_huangjie_box_fresh.png", 85, 250),
    ("lj_huangjie_box_store_normal.png", 250, -185),
    ("lj_huangjie_box_close_normal.png", 400, -85),
]


def main():
    panel_path = sys.argv[1] if len(sys.argv) > 1 else PANEL
    btn_dir = sys.argv[2] if len(sys.argv) > 2 else BUTTONS
    out = sys.argv[3] if len(sys.argv) > 3 else OUT

    panel = Image.open(panel_path).convert("RGBA")
    sprites = []
    for name, bx, by in BUTTONS_LIST:
        path = os.path.join(btn_dir, name)
        if not os.path.exists(path):
            print("  缺按钮贴图：" + name)
            continue
        sprites.append((Image.open(path).convert("RGBA"), bx, by, name))

    # 统一换到「UI 坐标」（+y 朝上）里算包围盒
    boxes = [(PANEL_POS[0] - panel.width / 2, PANEL_POS[1] - panel.height / 2,
              PANEL_POS[0] + panel.width / 2, PANEL_POS[1] + panel.height / 2)]
    for img, bx, by, _ in sprites:
        boxes.append((bx - img.width / 2, by - img.height / 2, bx + img.width / 2, by + img.height / 2))

    min_x = min(b[0] for b in boxes) - PAD
    max_x = max(b[2] for b in boxes) + PAD
    min_y = min(b[1] for b in boxes) - PAD
    max_y = max(b[3] for b in boxes) + PAD
    W = int(round(max_x - min_x))
    H = int(round(max_y - min_y))
    print("画布 %dx%d（UI 范围 x %.0f~%.0f  y %.0f~%.0f）" % (W, H, min_x, max_x, min_y, max_y))

    def to_px(ux, uy):
        """UI 坐标 -> 画布像素坐标（y 翻向）"""
        return ux - min_x, max_y - uy

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx, cy = to_px(PANEL_POS[0], PANEL_POS[1])
    canvas.alpha_composite(panel, (int(round(cx - panel.width / 2)), int(round(cy - panel.height / 2))))
    print("  面板中心 -> (%d,%d)" % (round(cx), round(cy)))

    for img, bx, by, name in sprites:
        px, py = to_px(bx, by)
        canvas.alpha_composite(img, (int(round(px - img.width / 2)), int(round(py - img.height / 2))))
        print("  %-34s 中心=(%d,%d)" % (name, round(px), round(py)))

    canvas.save(out)
    print("已合成 -> %s (%dx%d)" % (out, W, H))


if __name__ == "__main__":
    main()
