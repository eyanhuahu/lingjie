# -*- coding: utf-8 -*-
"""把荒界纳物箱界面上的 5 个按钮合成到箱体 UI 图上。

为什么要合成：按钮在游戏里是**独立的 UI 贴图**（来自 images/ethereal_realm_ui 图集），
不属于箱体的动画帧，所以单独导出的箱体 UI 上没有按钮。

⚠️ 关于位置（踩过的坑，别再改回去）：
mod 源码里 HUANGJIE_BUTTONS 给的是**容器控件坐标系**里的坐标（控件原点 + 0.6 缩放）。
箱体面板的动画是挂在控件原点下的，但**导出的 PNG 画布跟控件原点对不齐** ——
按源码坐标硬套，按钮会跑到箱体外面飘着（用户反馈「位置不对」）。
所以这里改用**wiki 正文自己的描述**定位（正文写的是：左上角「整理」、右下角「封」、
右下方「安全入库」，收纳 / 返鲜在箱子上方），位置用面板尺寸的比例给出，画布就等于面板本身。
按钮贴图里的相对大小是对的（1 控件单位 = 1 图集像素），只有锚点需要靠描述校准。

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

# (贴图文件名, 中心点相对面板宽/高的比例)
BUTTONS_LIST = [
    ("lj_huangjie_box_sort_normal.png", 0.09, 0.22),    # 整理：左上角
    ("lj_huangjie_box_collect.png", 0.42, 0.20),        # 收纳：上方偏左
    ("lj_huangjie_box_fresh.png", 0.58, 0.20),          # 返鲜：上方偏右
    ("lj_huangjie_box_store_normal.png", 0.80, 0.72),   # 安全入库：右下
    ("lj_huangjie_box_close_normal.png", 0.90, 0.52),   # 封：右侧偏下
]


def main():
    panel_path = sys.argv[1] if len(sys.argv) > 1 else PANEL
    btn_dir = sys.argv[2] if len(sys.argv) > 2 else BUTTONS
    out = sys.argv[3] if len(sys.argv) > 3 else OUT

    panel = Image.open(panel_path).convert("RGBA")
    W, H = panel.size
    print("面板 %s  %dx%d" % (os.path.basename(panel_path), W, H))

    for name, rx, ry in BUTTONS_LIST:
        path = os.path.join(btn_dir, name)
        if not os.path.exists(path):
            print("  缺按钮贴图：" + name)
            continue
        btn = Image.open(path).convert("RGBA")
        cx = W * rx
        cy = H * ry
        left = int(round(cx - btn.width / 2))
        top = int(round(cy - btn.height / 2))
        panel.alpha_composite(btn, (left, top))
        print("  %-34s 中心=(%d,%d) 尺寸=%dx%d" % (name, round(cx), round(cy), btn.width, btn.height))

    panel.save(out)
    print("已合成 -> %s (%dx%d)" % (out, W, H))


if __name__ == "__main__":
    main()
