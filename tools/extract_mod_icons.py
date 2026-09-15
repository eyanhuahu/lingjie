# -*- coding: utf-8 -*-
"""从 mod 的 KTEX 图集里批量导出物品图标。

背景：饥荒 mod 的物品图标打包成 `.tex`（KTEX 容器 + DXT5/BC3 压缩），
      需要用同目录的 `.xml` 里的 UV 坐标切出每个图标。本脚本纯 Python 实现，
      不依赖任何外部反编译工具。

用法：
    python tools/extract_mod_icons.py <mod.zip> <输出目录>

    # 也可以直接给磁盘上的 tex/xml：
    python tools/extract_mod_icons.py --tex a.tex --xml a.xml --out images/lingjie/icons

默认从 zip 里取 fig 这两条路径（灵界 mod 的图标图集）：
    lj_mod/images/ethereal_realm_icons/ethereal_realm_icons.tex
    lj_mod/images/ethereal_realm_icons/ethereal_realm_icons.xml
"""

import argparse
import io
import os
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image

DEFAULT_TEX = "lj_mod/images/ethereal_realm_icons/ethereal_realm_icons.tex"
DEFAULT_XML = "lj_mod/images/ethereal_realm_icons/ethereal_realm_icons.xml"


# ---------------------------------------------------------------------------
# DXT5 / BC3
# ---------------------------------------------------------------------------
def _rgb565(v):
    r, g, b = (v >> 11) & 0x1F, (v >> 5) & 0x3F, v & 0x1F
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))


def decode_dxt5(data, width, height):
    out = bytearray(width * height * 4)
    bw, bh = (width + 3) // 4, (height + 3) // 4
    if len(data) < bw * bh * 16:
        raise ValueError("DXT5 数据不足")

    pos = 0
    for by in range(bh):
        for bx in range(bw):
            block = data[pos:pos + 16]
            pos += 16
            a0, a1 = block[0], block[1]
            bits = int.from_bytes(block[2:8], "little")
            c0, c1 = struct.unpack_from("<HH", block, 8)
            r0, g0, b0 = _rgb565(c0)
            r1, g1, b1 = _rgb565(c1)
            pal = [(r0, g0, b0), (r1, g1, b1)]
            if c0 > c1:
                pal.append(((2 * r0 + r1) // 3, (2 * g0 + g1) // 3, (2 * b0 + b1) // 3))
                pal.append(((r0 + 2 * r1) // 3, (g0 + 2 * g1) // 3, (b0 + 2 * b1) // 3))
            else:
                pal.append(((r0 + r1) // 2, (g0 + g1) // 2, (b0 + b1) // 2))

            cidx = int.from_bytes(block[12:16], "little")
            for i in range(16):
                px, py = bx * 4 + (i % 4), by * 4 + (i // 4)
                if px >= width or py >= height:
                    continue
                r, g, b = pal[(cidx >> (2 * i)) & 0x3]
                ai = (bits >> (3 * i)) & 0x7
                if a0 > a1:
                    a = a0 if ai == 0 else a1 if ai == 1 else ((8 - ai) * a0 + (ai - 1) * a1) // 7
                else:
                    a = (a0 if ai == 0 else a1 if ai == 1
                         else 0 if ai == 6 else 255 if ai == 7
                         else ((6 - ai) * a0 + (ai - 1) * a1) // 5)
                off = (py * width + px) * 4
                out[off:off + 4] = bytes((r, g, b, a))
    return bytes(out)


# ---------------------------------------------------------------------------
# KTEX 容器
# ---------------------------------------------------------------------------
def load_ktex(data):
    """返回 (width, height, 头部字节数, DXT5 负载)。"""
    if data[:4] != b"KTEX":
        raise ValueError("不是 KTEX 容器（前四字节 %r）" % data[:4])
    width, height = struct.unpack_from("<HH", data, 8)

    total = 0
    w, h = width, height
    while True:
        total += max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * 16
        if w == 1 and h == 1:
            break
        w, h = max(1, w // 2), max(1, h // 2)
    header = len(data) - total
    if header < 0:
        raise ValueError("文件比完整 mip 链还短，格式判定有误")
    return width, height, header, data[header:]


def read_elements(xml_bytes):
    root = ET.fromstring(xml_bytes)
    out = []
    for el in root.iter("Element"):
        out.append((
            (el.get("name") or "").rsplit(".", 1)[0],
            float(el.get("u1")), float(el.get("v1")),
            float(el.get("u2")), float(el.get("v2")),
        ))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zipfile", nargs="?", help="mod 的 zip 包")
    ap.add_argument("out", nargs="?", help="输出目录")
    ap.add_argument("--tex")
    ap.add_argument("--xml")
    ap.add_argument("--tex-name", default=DEFAULT_TEX)
    ap.add_argument("--xml-name", default=DEFAULT_XML)
    ap.add_argument("--scale", type=int, default=1, help="导出放大倍数（默认 1）")
    args = ap.parse_args()

    if args.tex and args.xml:
        tex_bytes = open(args.tex, "rb").read()
        xml_bytes = open(args.xml, "rb").read()
    elif args.zipfile:
        z = zipfile.ZipFile(args.zipfile)
        tex_bytes = z.read(args.tex_name)
        xml_bytes = z.read(args.xml_name)
    else:
        ap.error("要么给 zip 包，要么同时给 --tex 与 --xml")

    if not args.out:
        ap.error("必须指定输出目录")

    width, height, header, payload = load_ktex(tex_bytes)
    rgba = decode_dxt5(payload, width, height)
    atlas = Image.frombytes("RGBA", (width, height), rgba)
    elements = read_elements(xml_bytes)

    os.makedirs(args.out, exist_ok=True)
    count = 0
    for name, u1, v1, u2, v2 in elements:
        left, top = int(round(u1 * width)), int(round(v1 * height))
        right, bottom = int(round(u2 * width)), int(round(v2 * height))
        tile = atlas.crop((left, top, max(right, left + 1), max(bottom, top + 1)))
        if args.scale > 1:
            tile = tile.resize((tile.width * args.scale, tile.height * args.scale), Image.NEAREST)
        tile.save(os.path.join(args.out, name + ".png"))
        count += 1

    sys.stdout.write("图集 %dx%d，头部 %d 字节，共导出 %d 个图标 -> %s\n"
                     % (width, height, header, count, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
