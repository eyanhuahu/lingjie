# 差异核对-A-入魔

一句话总结：文档《生物入魔》设计稿的三档数值有多处与代码不符——生命加成实际是按 `base + (base/(base+decay))*bonus*decay` 随基础血量衰减的公式（轻度 base=100 只 +65.63%、中度魔法反弹实际 5%、魔甲无「点数」概念、吸食残骸只给深度入魔的首领且限 40 距离、镜像混淆不封锁攻击、腺体解毒实际扣除 50 + 腺体原本治疗量），而天数配置、Boss 必定深度、理智吸取、护盾、蚀骨毒分段、魔化狂暴、祭天等条款与代码一致。

核对基准（均为代码原文，未做任何修改）：

- `scripts/main/combat/demonization.lua`（下称 demonization.lua）
- `scripts/prefabs/effects/lj_debuffs.lua`（下称 lj_debuffs.lua）
- `scripts/components/lj_demonization_info.lua`
- `scripts/main/config/lj_demonization_defs.lua`（下称 defs.lua）
- 另按需查证了实际被引用的 `modinfo.lua`、`scripts/main/config/tuning.lua`、`scripts/main/localization/language_zh.lua`、`scripts/main/combat/poison_cures.lua`、`scripts/prefabs/alchemy/lj_pill.lua`、`scripts/components/lj_soul_banner.lua`。

## 逐条对比

| 项目 | 文档说法 | 代码实际（标注文件名与行号） | 结论 |
| --- | --- | --- | --- |
| 入魔触发方式 | 开局随机入魔 | 每个生物生成时（`AddPrefabPostInitAny` + `AddComponentPostInit("combat")`，延迟一帧）随机抽等级：`({"small","medium","high"})[math.random(CanDeepDemonize() and 3 or 2)]`，demonization.lua:1741-1815、1686-1689 | 一致 |
| 天数可调 30/60/90、默认 60 | 30/60/90，默认 60 | `AddorGetConfig("demonization_day", 60, ...)`，选项 30/60/90，modinfo.lua:115-123；`TUNING.DEMONIZATION_DAY = GetModConfigData("demonization_day") or 60`，demonization.lua:23；`GetWorldDay() >= TUNING.DEMONIZATION_DAY` 才可能抽到 deep，demonization.lua:402-408 | 一致 |
| Boss 必定深度入魔 | Boss 生物必定深度入魔 | `level = inst:HasTag("epic") and "high" or ...`，demonization.lua:1685-1689；epic 在 `ScheduleDemonization` 中直接 `ApplyDemonization`，不受天数限制，demonization.lua:1793-1797 | 一致 |
| 无仇恨值时回血 | 生命每秒回复 2% | 回血写在 5 秒心跳里：`DoPeriodicTask(5, OnTick/OnTick_Medium/OnTick_High)`，demonization.lua:601、653、1428；回血量为 `maxhealth * 0.02`，demonization.lua:507；且必须先连续 10 秒无有效目标（`regen_delay = 10`，defs.lua:5；`GetTime() - inst._lj_demon_out_of_combat >= regen_delay`，demonization.lua:505-508），受击会清零该计时（`ResetDemonizationRegen`，demonization.lua:512-514、1682）。实际为「脱战 10 秒后每 5 秒回复最大生命 2%」 | 不符 |
| 轻度：生命值 +70%（100→170、2000→3400） | +70% | 加成由公式 `base + (base/(base+decay))*bonus*decay` 决定（defs.lua:15-20，bonus=0.7 defs.lua:4），decay 默认 1500（tuning.lua:5）。base=100 实得 165.625（+65.63%），base=2000 实得 2600（+30%）。详见「计算过程」 | 不符 |
| 轻度：魔气环绕 5 范围内玩家每 5 秒流失 1 点理智 | 5 范围、每 5 秒 1 点 | `FindEntities_Registered(x, y, z, 5, ...)` + `sanity:DoDelta(-1)`，每 5 秒执行一次，demonization.lua:581-594、601 | 一致 |
| 轻度：饥饿诅咒 30% 概率、饥饿消耗加快 20%、持续 30 秒 | 30%、+20%、30 秒 | `math.random() < 0.3` → `ApplyHungerDebuff`，demonization.lua:569-571；`hunger.burnratemodifiers:SetModifier(source, 1.2, "lj_hunger_debuff")`（1.2 倍）与 `DoTaskInTime(30, ...)` 移除，demonization.lua:517-539 | 一致 |
| 轻度：暗影迟缓 20% 概率、移速 -20%、持续 10 秒 | 20%、-20%、10 秒 | `math.random() < 0.2` → `ApplySlowDebuff`，demonization.lua:573-575；`SetExternalSpeedMultiplier(source, "lj_slow_debuff", 0.8)` 与 `DoTaskInTime(10, ...)` 移除，demonization.lua:542-563 | 一致 |
| 轻度：击杀后掉落魔核碎片 + 生物原生材料 | 碎片 + 原生材料 | `for i = 1, math.random(1, 10) do lootdropper:AddChanceLoot("lj_magic_debris", 1)`，demonization.lua:626-630；`lj_magic_debris` 中文名「魔核碎片」，language_zh.lua:3。原生战利品表未被改动（small 分支只 AddChanceLoot）。掉落数量文档未写：实为 1~10 个 | 一致 |
| 轻度名称「魔气初染」 | 轻度入魔（魔气初染） | 代码等级键为 `small/medium/high`（demonization.lua:1688），显示文本为「入魔程度: 轻度/中度/深度」，language_zh.lua:500-504。未出现「魔气初染」字样 | 代码中未找到 |
| 中度：生命值 +120%（100→220、2000→4400） | +120% | 同公式，bonus=1.2（defs.lua:4）。base=100 实得 212.5（+112.5%），base=2000 实得 3028.5714（+51.43%） | 不符 |
| 中度：魔甲提升至 15 点（减免 12% 物理伤害） | 15 点、-12% | `externaldamagetakenmultipliers:SetModifier(inst, 0.88, "lj_magic_armor")`，demonization.lua:736-738：只有 0.88 的受伤乘数（即 -12%），代码中不存在「15 点」这个数值或点数体系 | 不符 |
| 中度：魔气环绕 10 范围内每 5 秒流失 3 点理智 | 10 范围、5 秒、3 点 | `FindEntities_Registered(x, y, z, 10, ...)` + `sanity:DoDelta(-3)`，每 5 秒，demonization.lua:633-646、653 | 一致 |
| 中度：饥饿诅咒同上 | 同上 | medium 同样注册 `onhitother` → `OnCombatTick`（30%、1.2 倍、30 秒），demonization.lua:740、565-577 | 一致 |
| 中度：暗影迟缓同上 | 同上 | 同上，20%、0.8 倍、10 秒，demonization.lua:740、565-577 | 一致 |
| 中度：魔法反弹＝受玩家伤害时 10% 概率反射 2% 伤害 | 10% 概率、反射 2% | `math.random() < 0.10` 成立后 `attacker.components.health:DoDelta(-damage * 0.05, ...)`，demonization.lua:692-696：反射比例是 **5%**，不是 2%（2% 出现在深度分支 demonization.lua:881-885） | 不符 |
| 中度：限定易伤＝生命降到 50% 触发护盾、期间不受伤害、持续 25 秒、冷却 5 分钟 | 50%、25 秒、5 分钟 | `GetPercent() <= 0.5` → `SetInvincible(true)`，`DoTaskInTime(25, ...)` 关闭，`DoTaskInTime(300, ...)` 解除冷却标记，demonization.lua:698-724 | 一致 |
| 中度：吸食残骸＝每当有玩家死亡，恢复自身损失生命值的 10% | 玩家死亡即回 10% | 该效果实为玩家 `death` 事件里扫描 40 距离内的 `epic`，且只对 `boss.lj_high_buff_active`（深度入魔）生效：`DoDelta(missing_hp * 0.1, ...)`，demonization.lua:1846-1869。即：只作用于深度入魔的首领、限玩家死亡点 40 距离内，不适用于中度入魔生物 | 不符 |
| 中度：掉落魔核、魔核碎片 + 生物原生材料 | 魔核 + 碎片 + 原生材料 | `AddChanceLoot("lj_magic_core", 1)` 循环 `math.random(1, 6)` 次、`AddChanceLoot("lj_magic_debris", 1)` 循环 `math.random(1, 10)` 次，demonization.lua:749-757；`lj_magic_core` 中文名「魔核」，language_zh.lua:6。数量文档未写：魔核 1~6、碎片 1~10 | 一致 |
| 深度：生命值 +180%（100→280、2000→5600） | +180% | 同公式，bonus=1.8（defs.lua:4）。base=100 实得 268.75（+168.75%），base=2000 实得 3542.8571（+77.14%） | 不符 |
| 深度：魔甲提升至 25 点（减免 20% 物理伤害 + 5 位面防御） | 25 点、-20%、+5 位面防御 | `externaldamagetakenmultipliers:SetModifier(inst, 0.8, "lj_high_armor")`（-20%）与 `planardefense:AddBonus(inst, 5, "lj_high_armor")`，demonization.lua:1445-1452；5 位面防御一致，但代码中没有「25 点」这个数值 | 不符 |
| 深度：移动速度 +10% | +10% | `locomotor:SetExternalSpeedMultiplier(inst, "lj_high_speed", 1.1)`，demonization.lua:1454-1455 | 一致 |
| 深度：体型增大 1.2 倍 | ×1.2 | `Transform:SetScale(scale_x * 1.2, scale_y * 1.2, scale_z * 1.2)`，demonization.lua:1471-1474；对三只外观豁免生物（`lj_moon_lion`、`lj_chiyan_scorpion_dragon`、`lj_soul_devouring_snake`，demonization.lua:149-154）不放大，文档未提该例外 | 一致 |
| 深度：魔气环绕 10 范围内每 5 秒流失 5 点理智 | 10 范围、5 秒、5 点 | `FindEntities_Registered(x, y, z, 10, ...)` + `sanity:DoDelta(-5)`，每 5 秒，demonization.lua:1403-1416、1428 | 一致 |
| 深度：镜像混淆＝攻击时 10% 概率触发、玩家 5 秒内操作反向（左=右、前=后） | 10%、5 秒、方向反向 | `math.random() < 0.1` → `_lj_runindirection_flip = true`，`DoTaskInTime(5, ...)` 复位，demonization.lua:1011-1027；方向翻转由 `direction = (direction + 180) % 360` 实现（`RunInDirection` 钩子），demonization.lua:1817-1839 | 一致 |
| 深度：镜像混淆期间无法攻击 | 期间无法攻击 | 代码中对 `_lj_runindirection_flip` 的处理只有 `RunInDirection` 方向翻转（demonization.lua:1817-1839）与套装免疫解除（demonization.lua:980-989、1873-1874），全仓库未找到与之关联的攻击封锁逻辑 | 代码中未找到 |
| 深度：毒入骨髓＝普通攻击附带蚀骨毒，单次 240 秒不可叠加（可重置，上限 240 秒） | 240 秒、不可叠加、可重置、上限 240 秒 | `OnCombatTick_High` 在 `onhitother` 中 `player:AddDebuff("lj_soul_snake_poison_debuff", ...)`，demonization.lua:991-1001；该 debuff `duration = SOUL_POISON_DURATION = 240`、`refresh = REFRESH_RESET`（重置而非叠加），lj_debuffs.lua:725-731、159-183 | 一致 |
| 深度：毒分段伤害 0~80 秒每 10 秒 6 点、80~160 秒每 10 秒 10 点、160~240 秒每 10 秒 14 点 | 6/10/14，间隔 10 秒 | `GetSoulPoisonDamage(elapsed)`：`<80 → 6`、`<160 → 10`、其余 `14`，lj_debuffs.lua:41-48；周期 `interval = SOUL_POISON_INTERVAL = 10`，lj_debuffs.lua:727、742-744；`elapsed = SOUL_POISON_DURATION - timeleft`，lj_debuffs.lua:752-753。附加事实：`initial_delay = 0`（lj_debuffs.lua:745），命中当刻会立即结算一跳，文档未写 | 一致 |
| 深度：解毒可用特定丹药 | 「特定丹药」 | 清心丸：`eater:RemoveDebuff("lj_soul_snake_poison_debuff")`，lj_pill.lua:47-57（`StillnessPillOnEaten`） | 一致 |
| 深度：解毒可用腺体（扣 50 血，血量不足 50 则保留 5 点） | 扣 50 血、保底 5 点 | `spidergland` 的 `healer.onhealfn`：`local damage = math.min(50 + normal_heal, math.max(0, currenthealth - 5))` 后 `DoDelta(-damage, ...)`，poison_cures.lua:1-25。保底 5 点一致，但实际扣除量是 **50 + 腺体原本治疗量**（先结算原版治疗再抵扣），不是固定 50 | 不符 |
| 深度：影灵随行＝唤醒时额外召唤一个半血生命值的影体 | 唤醒时召唤、半血 | `OnEntityWake_High` 内 `DoTaskInTime(0.1, SpawnEpicShadowClone)`，demonization.lua:1423-1433；影体 `health:SetMaxHealth(clone.components.health.maxhealth * 0.5)`，demonization.lua:1329-1331（此时影体自身尚未入魔，故为「该生物基础最大生命的一半」）。附加限制：仅 `epic`、非其他模组生物（外观豁免的三只除外）、每个本体只召唤一次（`_lj_has_spawned_shadow`），demonization.lua:1033-1049、1389 | 一致 |
| 深度：影体不携带魔化效果 | 不携带魔化效果 | `ApplyDemonization` 开头即 `inst._lj_is_shadow_clone` 直接 return，demonization.lua:1664-1673；影体在 `SetupEpicShadowClone` 里立刻打上 `_lj_is_shadow_clone`（demonization.lua:1316-1322），故延迟一帧的 `ScheduleDemonization` 也会跳过，demonization.lua:1758-1767 | 一致 |
| 深度：影体无护甲保护 | 无护甲保护 | 影体只走 `SetupEpicShadowClone`，不执行 `medium_buff`/`high_buff`，因此不会获得 `lj_magic_armor`/`lj_high_armor` 受伤乘数与 `planardefense` 加成（对比 demonization.lua:736-738、1445-1452 与 1316-1335） | 一致 |
| 深度：影体魂幡可直接炼化 | 魂幡可直接炼化 | 影体被加标签 `clone:AddTag("lj_can_be_refined")`，demonization.lua:1321；魂幡 `ONEOF_TAGS = { "shadowcreature", "nightmarecreature", "lj_can_be_refined" }`，lj_soul_banner.lua:8；`RefineClone` 要求 `target._lj_is_shadow_clone and target:HasTag("lj_can_be_refined")`，lj_soul_banner.lua:239-250 | 一致 |
| 深度：魔化狂暴＝生命值低于 30% 时伤害 +30%、魔甲脱落，冷却 5 分钟 | <30%、+30%、魔甲脱落、5 分钟 | `hp_percent <= 0.30 and not inst._lj_frenzy_cooldown` → `externaldamagemultipliers:SetModifier(inst, 1.3, "lj_frenzy")`，demonization.lua:913-919；移除 `lj_high_armor` 的受伤乘数与位面防御加成，demonization.lua:926-932；`DoTaskInTime(300, ...)` 结束并解除，demonization.lua:947-960 | 一致 |
| 深度：魔化狂暴时技能释放频率翻倍 | 频率翻倍 | 用 `EPIC_TIMER_SCALE = 0.5` 把 `timer` 中名字含 `attack/cooldown/cd/skill` 的计时剩余时间减半、并对之后新建的同类计时同样减半，demonization.lua:806-836、858-872；仅对 `epic` 生效（`if inst:HasTag("epic") then HookEpicTimer(inst) end`），demonization.lua:921-924 | 一致 |
| 深度：祭天＝死亡后召唤天劫，每 6 秒雷击、一击必杀、有标识、标识 1.5 秒后落地、持续 60 秒 | 6 秒间隔、必杀、标识、1.5 秒、60 秒 | `StartTribulation`：`tribulation_time = 60`、`strike_interval = 6`、`DoPeriodicTask(6, ...)`，demonization.lua:771-783；标识用 `reticuleaoesummontarget` 在死亡点 ±15 内随机落点，demonization.lua:791-796；`DoTaskInTime(1.5, ...)` 后 `StrikeLightning`，demonization.lua:797-802；雷击对 3 距离内玩家 `DoDelta(-9999, nil, "lj_tribulation_thunder", true, nil, true)`（9999 点、无视无敌与吸收），demonization.lua:760-769；死亡时通过 `_lj_tribulation_death_fn` 触发，demonization.lua:1496-1500 | 一致 |
| 深度：掉落魔晶 + 生物原生材料（产量翻倍） | 魔晶 + 原生材料、翻倍 | `GenerateLoot` 被包装为「每条战利品插入两次 + 追加一个 `lj_magic_crystal`」，demonization.lua:1506-1522；`lj_magic_crystal` 中文名「魔晶」，language_zh.lua:10。附加事实：`DemonizationDefs.fixed_loot`（`lj_moon_lion`、`lj_chiyan_scorpion_dragon`、`lj_soul_devouring_snake`，defs.lua:6-11）跳过该包装，三只均带 `epic` 标签（各自 boss 文件内 `inst:AddTag("epic")`），因此这三只深度入魔时既不翻倍也不追加魔晶 | 不符 |

## 文档完全没提到、但代码里存在的入魔机制

1. **入魔豁免与白名单**：影怪黑名单（`crawlinghorror`、`terrorbeak`、`crawlingnightmare`、`nightmarebeak`、`ruinsnightmare`、`shadow_knight`、`shadow_bishop`、`shadow_rook`）不入魔，demonization.lua:1706-1721、1745-1747；被动小动物由 `IsPassiveSmallAnimal` 判定并清除入魔（保留有攻击配置的小生物），demonization.lua:1724-1739、1769-1791；`player`/`companion`/`wall`/`equipmentmodel`/`swc2hm` 与 `_lj_is_shadow_clone` 全部跳过，demonization.lua:1758-1767；无 `locomotor` 的非 epic 生物跳过，demonization.lua:1764。
2. **被玩家雇佣的生物清除全部入魔**：`IsLedByPlayer` + `startfollowing` 监听，还原最大生命、体型、掉落表、冻结/睡眠抗性、移速重算函数、颜色，demonization.lua:1675-1679、1699-1705、1528-1662。
3. **深度入魔附带的其他抗性**：`freezable:SetResistance(9999)`、`sleeper:SetResistance(9999)`、`sg.mem.noelectrocute = true`、`grogginess:AddImmunitySource(inst)`，demonization.lua:1476-1490。
4. **深度入魔忽略一切减速**：重写 `locomotor.RecalculateExternalSpeedMultiplier`，只累乘 `> 1` 的倍率，demonization.lua:1454-1468。
5. **深度入魔的颜色与外观豁免**：中度染 `DEMONIZATION_COLOURS.mid`、深度染 `DEMONIZATION_COLOURS.deep`（demonization.lua:142-146、733、1441），三只固定掉落首领保留原外观（demonization.lua:149-165）；噩梦猪人（`daywalker`/`daywalker2`）头颅用独立动画另行着色（demonization.lua:364-400）。
6. **魔化狂暴期间完全无法回血**：狂暴激活时 `health.DoDelta` 被包装为「`amount > 0` 一律返回 0」，demonization.lua:934-945，狂暴结束后才恢复原函数（demonization.lua:1584-1587）。
7. **深度入魔也有护盾，且触发区间不同**：深度为 `hp_percent <= 0.50 and hp_percent > 0.30` 才触发 25 秒无敌护盾（5 分钟冷却），demonization.lua:887-911；中度是无条件 `<= 0.5`，demonization.lua:698-724。
8. **深度入魔同时保留饥饿诅咒、暗影迟缓与另一种反弹**：`OnCombatTick_High` 里 30% 饥饿诅咒、20% 减速、10% 镜像混淆，demonization.lua:991-1029；`OnAttacked_High` 里 10% 概率反射 `damage * 0.02`（2%），demonization.lua:875-885。
9. **影体的一整套附属机制**：本体与影体同组互不仇恨（`SetTarget`/`CanHitTarget`/`IsValidTarget` 三重过滤，demonization.lua:221-326）；影体不掉落任何战利品（demonization.lua:1069-1080）；影体行为树注入跟随节点 + 每 2 秒兜底跟随与目标同步（demonization.lua:1211-1279、1360-1381）；影体到达 `minhealth` 或被击杀即消失（demonization.lua:1180-1209）；本体死亡/移除时清除影体（demonization.lua:1350-1358）；影体对特定首领做特殊处理（克劳斯沿用宝石鹿数量、龙蝇不掉鳞、熊獾不掉毛、邪天翁不生成羽毛、蚁狮位面相关禁用，demonization.lua:1281-1314）；影体带 `disablesw2hm` 防止暗影世界模组二次复制（demonization.lua:1319）。
10. **镜像混淆的免疫条件**：身体穿完好的 `lj_keel_armour` 且头部戴完好的 `lj_crystalcrown` 时免疫，装备变化或耐久变化时立即解除，demonization.lua:965-989、1873-1874。
11. **祭天的落点特效与治疗特效**：玩家死亡附近有深度入魔首领时播放 `statue_transition_2`，demonization.lua:1862-1865。
12. **与「暗影世界」模组（workshop-2886753796）的兼容钩子**：强制其 `GetModConfigData("Shadow World")` 返回 false，demonization.lua:5-20。
13. **入魔状态存档**：`lj_demonization_info` 组件保存 `level`/`cleared`/`health_percent`/`base_maxhealth`，components/lj_demonization_info.lua:7-45；读档时按生命比例恢复，避免先恢复基础血量时截掉强化生命，demonization.lua:479-493、demonization.lua:438-442。
14. **入魔血量衰减阈值本身是可配置项**：`demonization_health_decay` 可选 1000/1500/3000，默认 1500，modinfo.lua:125-133；`TUNING.ETHEREAL_REALM.DEMONIZATION_HEALTH_DECAY = GetModConfigData("demonization_health_decay") or 1500`，tuning.lua:5。
15. **信息显示兼容**：ShowMe 的 `GetTestString` 与 Insight 的 `AddComponentDescriptor` 登记，demonization.lua:29-140。
16. **掉落数量是随机区间**：碎片 `math.random(1, 10)`、魔核 `math.random(1, 6)`，demonization.lua:626-630、749-757。
17. **理智吸取任务的挂起/恢复**：`entitywake` 时重建 5 秒周期任务、`entitysleep` 时取消（三档各自一份，`san_task_small`/`san_task_medium`/`san_task_high`），demonization.lua:596-609、648-661、1417-1433。

## 计算过程（生命加成公式的实际数值）

公式来源：`scripts/main/config/lj_demonization_defs.lua`

- defs.lua:19：`return base + (base / (base + decay)) * bonus * decay`
- defs.lua:15-18：`base` 取 `math.max(0, tonumber(base) or 0)`，`decay = math.max(1, tonumber(decay) or M.health_decay)`，`bonus = math.max(0, tonumber(bonus) or 0)`
- defs.lua:4：`health_bonus = { small = .7, medium = 1.2, high = 1.8 }`
- defs.lua:3：`health_decay = 1500`（仅作 `decay` 为空时的兜底）
- tuning.lua:5：实际传入的 `decay` 是 `TUNING.ETHEREAL_REALM.DEMONIZATION_HEALTH_DECAY = GetModConfigData("demonization_health_decay") or 1500`，默认 1500
- demonization.lua:479-487：`health.maxhealth = DemonizationDefs.GetMaxHealth(DemonizationDefs.GetBaseMaxHealth(inst), DemonizationDefs.health_bonus[level], TUNING.ETHEREAL_REALM.DEMONIZATION_HEALTH_DECAY)`
- defs.lua:23-29：`base` 是入魔前的最大生命（优先 `inst._lj_demon_base.maxhealth`，其次 `health.maxhealth`）

### 默认 decay = 1500 时的实际结果

| 基础血量 base | 轻度 bonus=0.7 实际最大生命 | 相对增幅 | 中度 bonus=1.2 实际最大生命 | 相对增幅 | 深度 bonus=1.8 实际最大生命 | 相对增幅 |
| --- | --- | --- | --- | --- | --- | --- |
| 100 | 165.6250 | +65.63% | 212.5000 | +112.50% | 268.7500 | +168.75% |
| 200 | 323.5294 | +61.76% | 411.7647 | +105.88% | 517.6471 | +158.82% |
| 500 | 762.5000 | +52.50% | 950.0000 | +90.00% | 1175.0000 | +135.00% |
| 2000 | 2600.0000 | +30.00% | 3028.5714 | +51.43% | 3542.8571 | +77.14% |

计算示例（base = 100、轻度）：额外生命 = `(100 / (100 + 1500)) * 0.7 * 1500 = 0.0625 * 1050 = 65.625`，最大生命 = `100 + 65.625 = 165.625`（+65.63%），**不是**文档的 170（+70%）。
计算示例（base = 2000、轻度）：额外生命 = `(2000 / 3500) * 0.7 * 1500 = 0.5714286 * 1050 = 600`，最大生命 = `2600`（+30%），**不是**文档的 3400（+70%）。
计算示例（base = 2000、中度）：额外生命 = `0.5714286 * 1800 = 1028.5714`，最大生命 = `3028.5714`（+51.43%），**不是**文档的 4400。
计算示例（base = 2000、深度）：额外生命 = `0.5714286 * 2700 = 1542.8571`，最大生命 = `3542.8571`（+77.14%），**不是**文档的 5600。

### 与文档举例的逐项判定

| 文档写法 | 公式实际值 | 判定 |
| --- | --- | --- |
| 轻度 +70%，100 → 170 | 100 → 165.625（+65.63%） | 不符 |
| 轻度 2000 → 3400 | 2000 → 2600（+30%） | 不符 |
| 中度 +120%，100 → 220 | 100 → 212.5（+112.50%） | 不符 |
| 中度 2000 → 4400 | 2000 → 3028.5714（+51.43%） | 不符 |
| 深度 +180%，100 → 280 | 100 → 268.75（+168.75%） | 不符 |
| 深度 2000 → 5600 | 2000 → 3542.8571（+77.14%） | 不符 |

### 公式的性质（决定了文档「固定百分比」的说法不成立）

- 额外生命上限为 `bonus * decay`：decay=1500 时轻度 1050、中度 1800、深度 2700；基础血量越大越接近上限，百分比越低。文档给的 +70%/+120%/+180% 只有在 `base` 趋近 0 时才近似成立（base=0 时公式返回 0，defs.lua:16、19）。
- `decay` 可被模组配置改动（modinfo.lua:125-133：1000/1500/3000），同一基础血量的结果会随配置变化：

| decay | base | 轻度 | 中度 | 深度 |
| --- | --- | --- | --- | --- |
| 1000 | 100 | 163.6364 | 209.0909 | 263.6364 |
| 1000 | 2000 | 2466.6667 | 2800.0000 | 3200.0000 |
| 1500 | 100 | 165.6250 | 212.5000 | 268.7500 |
| 1500 | 2000 | 2600.0000 | 3028.5714 | 3542.8571 |
| 3000 | 100 | 167.7419 | 216.1290 | 274.1935 |
| 3000 | 2000 | 2840.0000 | 3440.0000 | 4160.0000 |
