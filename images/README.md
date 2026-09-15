这里存放图片。

规则：

1. 图片文件名建议使用英文小写、数字、短横线、下划线。
2. 推荐格式：.png / .jpg / .jpeg / .webp。
3. 不建议使用中文、空格、括号、特殊符号。
4. `data.json` 的「图片」字段只填写文件名，例如 1234.png。
5. 详情里插图写 `[[图片:1234.png|图片说明]]`，且必须单独占一段。
6. 文件名大小写必须完全一致。
7. `inventoryimages1` ~ `inventoryimages4` 是《饥荒》原版物品图标，按字母顺序分批存放，**没有规律**。
   配方里引用图标时必须写完整相对路径，例如 `[images/inventoryimages2/nitre.png] 硝石 2`。
8. `lingjie/icons/` 放**灵界 mod 的物品图标**，文件名 = 物品预制体 id，例如 `lj_magic_crystal.png`。
   已从 mod 的 `ethereal_realm_icons` 图集导出全部 74 个。
   重新导出：`python tools/extract_mod_icons.py <mod的zip包> images/lingjie/icons`
9. `lingjie/` 下以后新增的**展示图**（截图、大图）请另开目录，不要混进 `icons/`。
