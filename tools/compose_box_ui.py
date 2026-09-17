# -*- coding: utf-8 -*-
"""把荒界纳物箱界面上的 5 个按钮合成到箱体 UI 图上。

为什么要合成：按钮在游戏里是**独立的 UI 贴图**（来自 images/ethereal_realm_ui 图集），
不属于箱体的动画帧，所以单独导出的箱体 UI 上没有按钮。

## 坐标怎么来的（踩过三次坑，别改回去）

mod 源码 `lj_mod/scripts/main/ui/containers.lua`：
    · 容器面板 widget.pos = (0, 250)；槽位 11×3 行 + 1 行 10 格：
        行 y = 155 / 75 / -5，最后一行 y = -90；列 x = (i-5)*70
    · 按钮 HUANGJIE_BUTTONS（控件坐标，中心点）：
        sort(-415,230) collect(-85,250) fresh(85,250) store(250,-185) close(400,-85)

**坑一**：以为面板中心 = pos → 两个按钮跑到图外飘着。
**坑二**：改成"看着摆" → 位置偏下。
**坑三**：只单独挪了「封」→ 用户要求「整体移动，不要单独移动」。

**正确映射**：导出的面板 PNG **上沿**对应 pos.y、水平居中对应 pos.x：
        X = 面板宽/2 + 控件x          Y = pos.y − 控件y
反推依据：按这个映射，4 行槽位落在图上 y = 95 / 175 / 255 / 340，
跟箱子图上三层架子的实际位置（≈100 / 180 / 255）完全对得上 —— 槽位必须摆在架子上。

**整组平移**：映射出来后有按钮会压在面板上沿之外（游戏里不裁剪，但插图里露出来不好看），
所以最后把**整组**按最小位移平移一次，让 5 个按钮全部落进面板内、且保留源码里的相对布局
（绝不单独挪某一个）。平移量在下面打印出来，方便核对。

用法：
    python tools/compose_box_ui.py [面板图] [按钮目录] [输出]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(ROOT, ".work", "panel_clean.png")
BUTTONS = os.path.join(ROOT, ".work", "ui_buttons")
OUT = os.path.join(ROOT, "images", "lingjie", "anim", "huangjie_box_ui.png")

PANEL_POS_Y = 250             # 面板上沿对应的控件 y（见文件头推导）
MARGIN = 6                    # 整组平移后，按钮离面板边缘至少留这么多像素
BUTTONS_LIST = [
    ("lj_huangjie_box_sort_normal.png", -415, 230),    # 整理
    ("lj_huangjie_box_collect.png", -85, 250),         # 收纳
    ("lj_huangjie_box_fresh.png", 85, 250),            # 返鲜
    ("lj_huangjie_box_store_normal.png", 250, -185),   # 安全入库
    ("lj_huangjie_box_close_normal.png", 400, -85),    # 封
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

    # 整组平移（绝不单独挪某一个）：
    #   水平 —— 整组居中。源码里按钮本来就是以面板中心对称排布的（如收纳 -85 / 返鲜 +85）。
    #   竖直 —— 整组下移，刚好让包围盒不超出面板上下边。
    boxes = [(px - img.width / 2, py - img.height / 2, px + img.width / 2, py + img.height / 2)
             for img, (px, py), _ in sprites]
    left = min(b[0] for b in boxes)
    right = max(b[2] for b in boxes)
    top = min(b[1] for b in boxes)
    bottom = max(b[3] for b in boxes)
    shift_x = (W - (left + right)) / 2
    shift_y = 0.0
    if top < MARGIN:
        shift_y += MARGIN - top
    if bottom + shift_y > H - MARGIN:
        shift_y -= bottom + shift_y - (H - MARGIN)
    print("整组平移：x %+.1f  y %+.0f（面板 %dx%d，按钮包围盒 x %.0f~%.0f  y %.0f~%.0f）"
          % (shift_x, shift_y, W, H, left, right, top, bottom))

    for img, (px, py), name in sprites:
        nx = px + shift_x
        ny = py + shift_y
        panel.alpha_composite(img, (int(round(nx - img.width / 2)), int(round(ny - img.height / 2))))
        print("  %-34s 中心=(%d,%d)" % (name, round(nx), round(ny)))

    panel.save(out)
    print("已合成 -> %s (%dx%d)" % (out, W, H))


if __name__ == "__main__":
    main()
