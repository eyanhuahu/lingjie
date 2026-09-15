# 物品图标

这里放**灵界 mod 的物品图标**，用于：
- 卡片预览图（`data.json` 的「图片」字段）
- 制作配方里的材料图标

## 来源

从 mod 自带的图标图集里解出来的：

```
lj_mod/images/ethereal_realm_icons/ethereal_realm_icons.tex   （KTEX 容器 + DXT5 压缩，1024×512）
lj_mod/images/ethereal_realm_icons/ethereal_realm_icons.xml   （74 个图标的 UV 坐标）
```

饥荒的 `.tex` 是编译过的纹理，普通软件打不开。用仓库里的脚本解：

```bash
python tools/extract_mod_icons.py <mod的zip包> images/lingjie/icons
```

脚本是纯 Python 实现的（DXT5 解码 + 按 XML 坐标切图），不需要任何外部反编译工具。

## 命名规则

**文件名 = 物品的预制体 id**，例如 `lj_magic_crystal.png` 对应魔晶。
这样 `data.json` 里的配方可以直接写：

```text
[images/lingjie/icons/lj_magic_crystal.png] 魔晶 2
```

物品 id 与图标名一一对应，新增物品时只要把同名 PNG 丢进来即可。

## 注意

- 这里是**图标**（64×64 的小图）。以后要放的**展示图**（截图、大图）请另开目录，不要混在这里。
- 图标总共有 74 个，其中少数不是物品图（如 `lj_remains_altar_tech` 是科技站图标），不影响使用。
- 这些图标是 mod 原作者的素材，请勿用于其他用途。
