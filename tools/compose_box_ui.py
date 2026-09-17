# -*- coding: utf-8 -*-
"""把荒界纳物箱界面上的 5 个按钮合成到箱体 UI 图上。

为什么要合成：按钮在游戏里是**独立的 UI 贴图**（来自 images/ethereal_realm_ui 图集），
不属于箱体的动画帧，所以单独导出的箱体 UI 上没有按钮。

## 坐标怎么来的（踩过两次坑，别改回去）

mod 源码 `lj_mod/scripts/main/ui/containers.lua`：
    · 容器面板 widget.pos = (0, 250)，槽位是 11×3 行 + 1 行 10 格：
        行 y = 155 / 75 / -5，最后一行 y = -90；列 x = (i-5)*70
    · 按钮 HUANGJIE_BUTTONS（控件坐标，中心点）：
        sort(-415,230) collect(-85,250) fresh(85,250) store(250,-185) close(400,-85)

**第一次错**：以为面板中心 = pos，结果两个按钮跑到图外飘着。
**第二次错**：改用"看着摆"，位置偏下，用户又指正。

**正确映射**：导出的面板 PNG **上沿**对应 pos.y、水平居中对应 pos.x，即
        X = 面板宽/2 + 控件x          Y = pos.y - 控件y
反推依据：按这个映射，4 行槽位落在图上的 y = 95 / 175 / 255 / 340，
跟箱子图上三层架子的实际位置（≈100 / 180 / 255）完全对得上 —— 槽位必须摆在架子上，
所以这个映射是对的。按钮有几个会压在面板上沿之外（游戏里不裁剪），
所以画布会自动向外扩到刚好包住全部内容。

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

PANEL_POS_Y = 250             # 面板上沿对应的控件 y（见文件头推导）
PAD = 6
BUTTONS_LIST = [
    ("lj_huangjie_box_sort_normal.png", -415, 230),    # 整理：左上角
    ("lj_huangjie_box_collect.png", -85, 250),         # 收纳：上沿偏左
    ("lj_huangjie_box_fresh.png", 85, 250),            # 返鲜：上沿偏右
    ("lj_huangjie_box_store_normal.png", 250, -185),   # 安全入库：右下
    ("lj_huangjie_box_close_normal.png", 400, -85),    # 封：右侧偏下
]


def main():
    panel_path = sys.argv[1] if len(sys.argv) > 1 else PANEL
    btn_dir = sys.argv[2] if len(sys.argv) > 2 else BUTTONS
    out = sys.argv[3] if len(sys.argv) > 3 else OUT

    panel = Image.open(panel_path).convert("RGBA")
    W, H = panel.size

    def to_px(ux, uy):
        """控件坐标 -> 面板图坐标系（面板左上角为原点）"""
        return W / 2 + ux, PANEL_POS_Y - uy

    sprites = []
    for name, ux, uy in BUTTONS_LIST:
        path = os.path.join(btn_dir, name)
        if not os.path.exists(path):
            print("  缺按钮贴图：" + name)
            continue
        sprites.append((Image.open(path).convert("RGBA"), to_px(ux, uy), name))

    xs = [0, W] + [p[0] - img.width / 2 for img, p, _ in sprites] + [p[0] + img.width / 2 for img, p, _ in sprites]
    ys = [0, H] + [p[1] - img.height / 2 for img, p, _ in sprites] + [p[1] + img.height / 2 for img, p, _ in sprites]
    min_x, max_x = min(xs) - PAD, max(xs) + PAD
    min_y, max_y = min(ys) - PAD, max(ys) + PAD
    CW, CH = int(round(max_x - min_x)), int(round(max_y - min_y))
    print("面板 %dx%d -> 画布 %dx%d" % (W, H, CW, CH))

    canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    canvas.alpha_composite(panel, (int(round(-min_x)), int(round(-min_y))))
    print("  面板左上角 -> (%d,%d)" % (round(-min_x), round(-min_y)))

    for img, (px, py), name in sprites:
        left = int(round(px - min_x - img.width / 2))
        top = int(round(py - min_y - img.height / 2))
        canvas.alpha_composite(img, (left, top))
        print("  %-34s 中心=(%d,%d)" % (name, round(px - min_x), round(py - min_y)))

    canvas.save(out)
    print("已合成 -> %s" % out)


if __name__ == "__main__":
    main()
