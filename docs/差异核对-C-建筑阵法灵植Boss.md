# 差异核对-C：建筑 / 阵法 / 灵植 / 异火线索 / 生物与 Boss

一句话总结：文档 21 组说法中约六成与代码一致，但**丹炉锤毁返还、荒界箱三个解锁项、远古残骸修复后的境界变化方向、四季阵最少阵旗数、多处 Boss 冷却与范围/伤害**与代码明确不符，另有「1~3 级魂幡」「彼岸花种」「玄灵培育池」在代码中找不到任何实现，而「魔兽森林」在代码注释里确实指向蝴蝶岛二号板块（冬季）。

> 阅读约定：源码根目录为 `lj_mod/`，下表路径均相对 `lj_mod/scripts/`。行号取自本次实际读取的文件内容。文中「地皮/格」= 4 世界单位，「码」= 1 世界单位（与 `scripts/main/config/tuning.lua:8` 的注释一致）。

---

## 逐条核对表

| 项目 | 文档说法 | 代码实际（标注文件名与行号） | 结论 |
| --- | --- | --- | --- |
| 1 丹炉·格数 | 5 格（4 格材料 + 1 格墟火/玄焰） | `main/ui/containers.lua:99-132`（5 个 slotpos）；`containers.lua:135-144` 第 5 格只收 `lj_flame`；`main/config/lj_alchemy_defs.lua:181` `ingredient_slots = 4` | 一致 |
| 1 丹炉·锤毁返还 | 返还 2 木板/2 砖块/5 硝石 | `prefabs/structures/lj_alchemy_furnace.lua:233` `SetLoot({ "boards", "boards", "cutstone", "cutstone", "nitre" ×5 })` | 一致 |
| 1 丹炉·失败不返还 | （未提及） | `lj_alchemy_furnace.lua:32-35`：丹劫炸毁时仅销毁内容物，不返还材料 | 文档缺失 |
| 2 悟道台·打坐收益 | 每 3 秒 +1 精神、+1 灵力；停饥饿；每 10 秒 +1 经验 | `components/lj_realm_value.lua:200-211`（`% 3` 回精神/灵力，`% 10` 加经验）；`lj_realm_value.lua:175-177` `burnratemodifiers:SetModifier(...,0,...)` | 一致 |
| 2 悟道台·锤毁返还 | 草6/石头6/噩梦燃料3 | `prefabs/structures/lj_wudao_chair.lua:16-21`（cutgrass×6、rocks×6、nightmarefuel×3） | 一致 |
| 2 悟道台·突破 | （未提及） | `lj_realm_value.lua:214` 瓶颈期打坐满 `meditation_duration`（`main/config/lj_realm_defs.lua:7` = 10 秒）可突破；3/6/9 阶才需悟道台（`lj_realm_value.lua:7-9`） | 文档缺失 |
| 3 荒界纳物箱·格数 | 3×11+1×10 格 | `main/ui/containers.lua:164-172`；注释 `containers.lua:146` 明写 43 格 | 一致 |
| 3 荒界箱·魔核解锁收集 | 魔核解锁 10 格范围收集 | `prefabs/structures/lj_huangjie_box.lua:270`（`lj_magic_core` → `_lj_collect_enabled`）；`lj_huangjie_box.lua:249` 范围 `TUNING.ETHEREAL_REALM.HUANGJIE_BOX_COLLECT_RANGE or 10`，而 `main/config/tuning.lua:4` 该值为 `GetModConfigData("huangjie_box_collect_range") or 10`（可被模组配置改成 `"all"`，见 `lj_huangjie_box.lua:251`） | 一致（默认值一致，可配置） |
| 3 荒界箱·蓝宝石解锁返鲜 | 蓝宝石解锁返鲜 | `lj_huangjie_box.lua:271,278`（`bluegem` → `_lj_fresh_enabled`）；`lj_huangjie_box.lua:88-89` 每秒恢复 1% 新鲜度 | 一致 |
| 3 荒界箱·魔晶解锁无限堆叠 | 魔晶解锁无限堆叠 | `lj_huangjie_box.lua:272,280`（`lj_magic_crystal` → `_lj_stack_enabled`）；`lj_huangjie_box.lua:115` `container:EnableInfiniteStackSize(...)` | 一致 |
| 4 聚气淬具匣·格数 | 7×7+1 格，第一格可展示武器 | `main/ui/containers.lua:218-238`（先插 1 格再插 7×7，共 50 格；注释 `containers.lua:217` 写「共50格」）；`containers.lua:240-248` slot==1 只收手持武器 | 一致 |
| 4 聚气匣·魔晶恢复耐久 | 魔晶提供缓慢恢复耐久 | `prefabs/structures/lj_cuiju_box.lua:206-218`（`lj_magic_crystal` 解锁）；`lj_cuiju_box.lua:113,123-134,165` 每 60 秒恢复最大耐久的 1% | 一致 |
| 5 灵虚光盏·格数 | 2 格 | `main/ui/containers.lua:46-70`（两个 slotpos，只收 `lj_flame`） | 一致 |
| 5 光盏·分裂火照明与时长 | 放入分裂的墟火/玄焰 +10 码照明、维持 8 分钟 | `prefabs/structures/lj_reiki_tablelamp.lua:53` `SetRadius(flame_count * 10)`；`lj_reiki_tablelamp.lua:68` `StartTimer(CONSUME_TIMER, 8 * 60)`，到点消耗分裂火（`lj_reiki_tablelamp.lua:96-114`） | 一致 |
| 5 光盏·本体永久照明 | 放入异火永久照明 | `lj_reiki_tablelamp.lua:38` 用「非 `lj_flame_source`」判定临时火；`lj_reiki_tablelamp.lua:79-84` 无临时火即停计时器 → 本体（`lj_flame_source`）不消耗、持续照明（`lj_flame.lua:279` 为本体加 `lj_flame_source`） | 一致 |
| 6 灵玉台 | 夜晚放入月魄凝液瓶吸收天地灵气，至少 30 秒 | `prefabs/structures/lj_reiki_table.lua:53` `CHARGE_TIME = 30`；`lj_reiki_table.lua:67-74` 仅在 `TheWorld.state.isnight` 时 `ResumeTimer`，否则 `PauseTimer` | 一致（30 秒为计时总长，非夜晚时段暂停，实际会更久） |
| 7 残骸修复·材料 | 木板10、融灵草3、紫晶塑体花1、化石碎片3 | `main/crafting/recipes.lua:47-52` `Ingredient("boards",10)`、`lj_reiki_cutgrass`（`main/localization/language_zh.lua:321` =「采下的融灵草」）3、`lj_purple_magic_bloom`（`language_zh.lua:336` =「紫晶塑体花瓣」）1、`fossil_piece` 3 | 一致 |
| 7 残骸修复·境界门槛 | 须至少辟谷境 | `prefabs/structures/lj_remains_altar.lua:18` `realm.major >= 3`；`main/localization/language_zh.lua:478` `[3] = "辟谷"`，提示语 `language_zh.lua:457`「须至少辟谷境才可修复。」 | 一致 |
| 7 残骸修复·修复完成效果 | **提升**一个大境界 | `lj_remains_altar.lua:21-26` `DropBuilderMajorRealm` → `lj_realm_value.lua:275-290` `DropOneMajor` 实际是**下降**一个大境界（9 小阶） | 不符（方向相反） |
| 7 残骸·解锁清单 | 灵韵、星陨、1~3级魂幡、骸龙甲、晶羽冠、四季核心、灵植核心、镇魔枢核、恒温晶核 | 灵韵 `recipes.lua:147-163`、星陨 `recipes.lua:128-144`、骸龙甲 `recipes.lua:166-181`、晶羽冠 `recipes.lua:184-199`、四季核心 `recipes.lua:273-288`、灵植核心 `recipes.lua:291-307`、镇魔枢核 `recipes.lua:310-328`、恒温晶核 `recipes.lua:331-348`，均为 `TECH.ETHEREAL_REALM_ONE`（`recipes.lua:29`，即祭坛科技树 `recipes.lua:30-32`）。**魂幡不是配方**（`language_zh.lua:32` 注释「由炼丹炉特殊炼制，不在普通制作栏解锁」），组件只有 `unlocked` 布尔（`components/lj_soul_banner.lua:159`），全仓库搜不到等级字段 | 部分不符（魂幡无等级） |
| 8 阵旗·范围划分 | 给阵法划分范围 | `prefabs/formations/lj_flag.lua:61` 加 `lj_formation_node`；`components/lj_formation_manager.lua:86-87` 用 `MIN_FLAG_DISTANCE`/`MAX_LINK_DISTANCE`/`MIN_FLAGS`/`MAX_SPAN` 建网找闭环 | 一致 |
| 8 阵旗·最远连接距离 | 最远 3 格范围相互连接 | `main/config/lj_formation_defs.lua:4-5`：`MIN_FLAG_DISTANCE = 12`（3 格，**最小**间距）、`MAX_LINK_DISTANCE = 24`（6 格，**最大**连接距离）；`main/formations/util.lua:50-56` 也按 12 限制放置 | 不符（3 格是最小间距，最大连接为 6 格） |
| 9 四季调和阵·最少阵旗 | 12×12 需最少 4 阵旗 | `lj_formation_defs.lua:3` `MIN_FLAGS = 8`；`lj_formation_manager.lua:87` `FindLoops(network, DEFS.MIN_FLAGS, DEFS.MAX_SPAN)` | 不符（最少 8 面） |
| 9 四季调和阵·范围 | 12×12 | `lj_formation_defs.lua:6` `MAX_SPAN = 48`（12 格）；`lj_formation_manager.lua:87` | 一致 |
| 9 生机回春阵 | 范围内提供光照、植物不枯萎 | `lj_formation_manager.lua:240-274` 生成 `lj_formation_light`（`prefabs/effects/lj_formation_light.lua:11` 半径 10）；`main/formations/effects.lua:146-156` `witherable:Stop()`、枯萎即复苏；另外还包含夜间生长、成熟不腐烂（`effects.lua:62-129`） | 一致（且多于文档） |
| 9 驱灵锁魔阵 | 只拦生物不拦玩家 | `main/formations/util.lua:64-75` `IsWardCreature` 排除 `player`/`playerghost`；`lj_formation_manager.lua:363-425` 只约束该函数判定为生物者 | 一致 |
| 9 极温庇护阵·中和极端温度 | 中和极端温度、抵消冰火伤害、每 60 秒回 30 点理智 | `main/formations/effects.lua:174-193` 体温锁 `DEFS.TEMPERATURE`（`lj_formation_defs.lua:8` = 25）；`main/formations/register.lua:147-175` 拦截 `DoFireDamage`、`cause` 为 cold/hot/fire/ice 的伤害、`stimuli` 为 fire/ice/cold 的 `GetAttacked`；`lj_formation_manager.lua:322` 理智 `DEFS.SANITY_PER_SECOND`（`lj_formation_defs.lua:9` = 30/60） | 一致 |
| 10 玄阵枢纽·格数与多重效果 | 4 格，可放多个阵眼提供多重效果 | `main/ui/containers.lua:73-96`（4 个 slotpos，只收 `lj_formation_nucleus`）；`lj_formation_manager.lua:184-196` 按核心种类做位掩码并集（重复不叠加） | 一致 |
| 10 玄阵枢纽·锤毁返还 | 锤毁全额返还 | `prefabs/formations/lj_supernatural_power_pivot.lua:87-90` `SetLoot({ "lj_magic_crystal", "twigs", "twigs", "transistor", "transistor" })` 与配方 `main/crafting/recipes.lua:253-259` 完全对应，且 `droprecipeloot = false`（`lj_supernatural_power_pivot.lua:89`） | 一致 |
| 11 融灵草·生成地 | 森林地皮蜘蛛巢与魔兽森林夜蝠巢穴附近 | 主陆：`map/lj_resource_worldgen.lua:76-82` 只对位于 `WORLD_TILES.FOREST` 的 `spiderden` 附近生成；蝴蝶岛：`main/world/butterfly_winter.lua:119-129` 在每个 `lj_bat_nest` 旁生成，且 `butterfly_winter.lua:125` 限定在鸟粪地皮 `GUANO` 上 | 一致（但两处地皮条件不同：主陆要求森林地皮，岛上要求鸟粪地皮） |
| 11 融灵草·每巢数量 | 每个巢穴附近 1~3 个 | `butterfly_winter.lua:122` `math.random(CONFIG.grass_min, CONFIG.grass_max)`，`map/lj_butterfly_winter_data.lua:14-15` `grass_min = 1 / grass_max = 3`；主陆 `lj_resource_worldgen.lua:78` `math.random(1,3)` | 一致 |
| 11 融灵草·采摘产出 | 草1+融灵草1，5% 额外得融灵草根 | `prefabs/plants/lj_reiki_grass.lua:21-22`（cutgrass + `lj_reiki_cutgrass`）；`lj_reiki_grass.lua:4,25-27,37-39` `REIKI_GRASS_ROOT_CHANCE = 0.05` → `lj_reiki_dug_grass`（`language_zh.lua:320` =「融灵草根」） | 一致 |
| 11 融灵草·生长周期 | 同原版树枝 | `lj_reiki_grass.lua:106` `REIKI_GRASS_REGROW_TIME = TUNING.SAPLING_REGROW_TIME`；DST `scripts/tuning.lua:1762` `SAPLING_REGROW_TIME = total_day_time*4` | 一致 |
| 11 融灵草·可催熟 | 可催熟 | `lj_reiki_grass.lua:138-140` 使用原版 `pickable` 组件（`SetUp(nil, REGROW_TIME)`），未覆写催熟路径；本次未找到被显式禁用的代码 | 代码中未找到（未发现专门实现，也未发现禁用） |
| 11 融灵草·全季节生长 | 全季节生长 | `lj_reiki_grass.lua:163` `MakeNoGrowInWinter(inst)`——冬季不生长 | 不符 |
| 11 融灵草·采集后留根 | 采集后留根部 | `lj_reiki_grass.lua:51-61` 采摘只播动画与掉落，实体不删除；`lj_reiki_grass.lua:146-147` `max_cycles = TUNING.GRASS_CYCLES`（DST `tuning.lua:1782` = 20）；`lj_reiki_grass.lua:93-104` 只有 `DIG` 才移除实体 | 一致 |
| 12 彼岸花·骨架旁数量 | 前辈骨架旁每骨架 1 朵 | `map/lj_resource_worldgen.lua:83-96`：每个 `skeleton` 若自身 4 单位内没有 `lj_red_magic_flower` 则 `PlaceNear(...)` 放 1 朵 | 一致（主陆） |
| 12 彼岸花·岛上骨架 | （未提及） | `main/world/butterfly_winter.lua:151-153` 每个岛屿骨架额外放 1 朵 `lj_red_magic_flower`，与别的 `lj_red_magic_flower` 是否已在 `lj_resource_worldgen.lua:93` 生成过无关 | 文档缺失 |
| 12 彼岸花·玩家死亡骨架 | 玩家死亡留下的骨架 1 天后附近生长 | `main/world/resources.lua:2-13` 给 `skeleton_player` 加 `lj_remains_flower`；`components/lj_remains_flower.lua:2,10,29-50` `DAY = TUNING.TOTAL_DAY_TIME` 后生成 1 朵，位置无空地时每 60 秒重试 | 一致 |
| 12 彼岸花·采摘产出 | 花瓣1+彼岸花1，5% 额外得彼岸花种 | `prefabs/plants/lj_red_magic_flower.lua:21-22`（petals + `lj_red_magic_cutflower`）；`lj_red_magic_flower.lua:4,25-27` `RED_MAGIC_FLOWER_ROOT_CHANCE = 0.05` → `lj_red_magic_dug_flower`，中文名「彼岸花根」（`language_zh.lua:327`），全仓库没有「彼岸花种」 | 不符（额外产物是根，不是种） |
| 13 紫晶塑体花·生成地 | 曼德拉草原附近 | `map/lj_resource_worldgen.lua:8-12` `AddRoomPreInit("MandrakeHome", ...)` 令曼德拉草房间 `countprefabs.lj_purple_magic_flower = 1` | 一致 |
| 13 紫晶花·每日生成 | 每日在自身 4 格范围内生成一朵花 | `prefabs/plants/lj_purple_magic_flower.lua:33` `FLOWER_SPAWN_RANGE = 16`（4 格）；`lj_purple_magic_flower.lua:99,101-105` 计时器周期 `TUNING.TOTAL_DAY_TIME`；失败重试 24 次（`:66-78`）；另有上限 10 朵（`:81` `CountNearbyFlowers(inst) >= 10`） | 一致（代码另有 10 朵上限） |
| 13 紫晶花·无法烧毁 | 无法烧毁，需斧头砍伐 | `lj_purple_magic_flower.lua:393-398` 只加 `workable` + `ACTIONS.CHOP`，全文件没有 `Make*Burnable`（对比 `lj_reiki_grass.lua:161` 有） | 一致 |
| 13 紫晶花·旁边有月狮 | 旁边有月蚀晶翼狮 | `lj_purple_magic_flower.lua:197` `SpawnPrefab("lj_moon_lion")`；`:169-184` 建立守护关系；`:174` `guardian.persists = false` | 一致 |
| 13 紫晶花·无法移植 | 无法移植 | `lj_purple_magic_flower.lua:393-398` 只有 CHOP，没有 `deployable`/`DIG`（对比 `lj_reiki_grass.lua:154-159` 有 DIG 与 `lj_reiki_dug_grass` 可种） | 一致 |
| 13 紫晶花·生长周期 | 20 天 | `lj_purple_magic_flower.lua:119` `StartTimer(GROW_TIMER, 20 * DAY_TIME)` | 一致 |
| 13 紫晶花·狮王存在时无法砍伐掉落 | 狮王存在时无法砍伐掉落 | `lj_purple_magic_flower.lua:270-276` `OnChopped` 在 `IsGuardianValid` 时重置工作量、不出花瓣；`:294-301` `SetShouldRecoilFn` 阻止最后一斧落成 | 一致 |
| 14 异火线索·刷新 | 线索物品 20 天一刷新 | `main/config/lj_log_defs.lua:58` `cooldown_days = 20` | 一致 |
| 14 异火线索·五种异火与 Boss | 冰霜业火/龙炎心火/狂鬃焰/灵煊尘火/紫鳞妖焰，各对应一个线索物品与一个 Boss | 名称：`main/localization/language_zh.lua:171,179,187,201,209`；线索与 Boss：`lj_log_defs.lua:4-49`（ice→`lj_frozen_log`→`deerclops`；dragon→`lj_charred_scales`→`dragonfly`；mighty→`lj_rotten_backpack`→`bearger`；dust→`lj_dried_camel_feathers`→`antlion`；purple→`lj_swollen_scroll`→`lj_soul_devouring_snake`） | 一致（5 个 Boss 中 4 个是原版 Boss，仅紫鳞对应本模组 Boss） |
| 14 狂鬃焰赋能 | 分裂的使耐久翻倍，本体额外 +15 免伤并翻倍 | `components/lj_flame_item.lua:8-9`（本体 level=2、分裂 level=1）；`components/lj_mighty_armour.lua:93-102` level 0→先翻倍最大与当前耐久；`lj_mighty_armour.lua:1,62-66` `DAMAGE_MULTIPLIER = .85`，level≥2 且耐久>0 时 `externaldamagetakenmultipliers:SetModifier(..., .85)`（即承受 85% 伤害） | 一致 |
| 15 墟火/异火·落地照明与灭火 | 放在地上提供 20 码照明并熄灭周围普通火焰 | `prefabs/alchemy/lj_flame.lua:254,274` `BODY_LIGHT_RADIUS = 20`；`lj_flame.lua:81-87,194-196` 每秒在 20 范围内熄灭燃烧/焖烧/火焰特效 | 一致 |
| 15 异火·物品栏焚毁 | 放物品栏/背包超 10 秒自动焚毁物品 | `lj_flame.lua:129` `CONTAINER_CLEAN_INTERVAL = 10`；`lj_flame.lua:132-176` 每 10 秒焚毁**一件**可焚物品，并用 `owner._lj_flame_last_clean_time` 限制同一容器不重复触发；`lj_flame.lua:116` 白名单容器（虚空戒/灵虚葫/丹炉/光盏）不焚毁 | 一致（机制为「每 10 秒一件」而非「超 10 秒全部焚毁」） |
| 15 灵虚葫·吸收代价 | 每秒扣 1 灵力、2 生命，持续 60 秒 | `components/lj_reiki_gourd_proxy.lua:181` `StartFlameBurn(60)`；`components/lj_reiki_gourd.lua:145,156,186-192` 每秒 `DoDelta(-1)` 灵力、`DoDelta(-2, ..., "lj_reiki_gourd_flame")` 生命 | 一致（代码还会点燃主人一次，`lj_reiki_gourd.lua:181-184`） |
| 15 异火·分裂消耗 | 分裂消耗 10 灵力 | `main/interactions/actions.lua:228` `SpendSpirit(doer, 10)`；失败退还见 `actions.lua:234` | 一致 |
| 16 炽岩蝎龙·血量护甲 | 血量 30000，护甲 30 | `prefabs/bosses/lj_chiyan_scorpion_dragon.lua:892-893` `SetMaxHealth(30000)`、`SetAbsorptionAmount(.3)` | 一致 |
| 16 蝎龙·免控 | 不吃冰冻/僵直/击退 | `lj_chiyan_scorpion_dragon.lua:868-869` `heavybody` + `no_stun`；`lj_chiyan_scorpion_dragon.lua:930` `MakeLargeBurnableCharacter`（可点燃，不可冻结） | 一致 |
| 16 蝎龙·召唤 | 每掉 10000 血召唤 4 只毒蝎幼虫（250 血、攻击 40、毒伤 3/秒持续 8 秒），CD 30 秒 | 阈值按生命**比例** 2/3、1/3（`lj_chiyan_scorpion_dragon.lua:921-926`），30000 血对应 10000/20000；`:515-526` 每次召唤 4 只；`:731,734` 幼虫 250 血、40 伤害；`:80` `summon = 30`；毒：`prefabs/effects/lj_debuffs.lua:697-723` `duration = 8`、每秒 `DoDelta(-3, ...)` | 一致 |
| 16 蝎龙·普通横扫 | 普攻横扫范围 4 格每钳 60 伤 CD 4 秒 | 范围 `lj_chiyan_scorpion_dragon.lua:141` `MELEE_RANGE = 4`（4 码=1 格），每钳 `:148` 60 伤；`main/config/lj_formation_defs.lua` 无关，钳击冷却在 `lj_chiyan_scorpion_dragon.lua:76` `melee = 8`，技能间还有全局空档 `:191` 4 秒 | 不符（范围是 4 码≈1 格，文档写 4 格；钳击 CD 为 8 秒，不是 4 秒） |
| 16 蝎龙·尾巴横扫 | 4 下后尾巴横扫 90 AOE + 2 格击退 | `lj_chiyan_scorpion_dragon.lua:151,167` 每钳累计、满 4 次横扫；`:158` 90 伤；`:159-164` `knockback radius = 2`；状态图 `stategraphs/SGlj_chiyan_scorpion_dragon.lua:72,113` 分别在钳击与横扫帧调用 | 一致（击退半径 2 码=0.5 格） |
| 16 蝎龙·陨石崩击 | CD 15 秒 120 伤 | 伤害 `lj_chiyan_scorpion_dragon.lua:259` 120（另有 `:262-265` 击退）；冷却 `:77` `meteor = 18` | 不符（CD 为 18 秒） |
| 16 蝎龙·沙砾喷发 | 身前 5 格锥形减速 40% + 每秒 10 伤持续 3 秒 CD 15 秒 | `lj_chiyan_scorpion_dragon.lua:212-225` `SAND_RANGE = 20`（5 格），实现是在范围内**每个**可锁定目标脚下生成原版 `sandspike`（`prefabs` 列表 `:22`），无锥形判定、无 40% 减速、无每秒 10 伤；冷却 `:78` `sand = 20` | 不符（伤害与减速来自原版 sandspike，代码未定义 10/秒与 40%；CD 20 秒） |
| 16 蝎龙·冲撞 | 蓄力 2 秒冲锋 8 格 100 伤 CD 30 秒 | 蓄力 `stategraphs/SGlj_chiyan_scorpion_dragon.lua:248` `SetTimeout(1)`（1 秒）；冲刺参数 `lj_chiyan_scorpion_dragon.lua:410-412` `CHARGE_MAX_DISTANCE = 32`（8 格）、`CHARGE_SPEED = 20`；伤害 `:459` 100；冷却 `:79` `charge = 30` | 不符（蓄力为 1 秒，其余一致） |
| 16 蝎龙·掉落 | 蝎龙骨1、怪物肉4、魔晶2、魔核6、魔核碎片10、橙宝石2、绿宝石2、黄宝石2 | `lj_chiyan_scorpion_dragon.lua:907-917` 与文档逐项相同 | 一致 |
| 17 噬魂蛇·血量护甲普攻 | 血量 12000，普攻撕咬 40 伤，护甲 15%；另处又写撕咬 50 伤 | `prefabs/bosses/lj_soul_devouring_snake.lua:520-521` 12000 / `.15`；`:524` `SetDefaultDamage(50)`；`:84,92,525` `BITE_CD = 3` | 不符（普攻为 50，非 40） |
| 17 噬魂蛇·掉鳞 | 每受 2000 血掉鳞片，玩家无法拾取可用异火烧毁 | `lj_soul_devouring_snake.lua:369,378-399` `SCALE_DAMAGE_THRESHOLD = 2000`，按生命比例差累计掉 `lj_snake_skin`；`lj_soul_devouring_snake.lua:151-165` 掉落后 5 秒才可吞；`prefabs/materials/lj_soul_snake_skin.lua` 中存在与否本次未逐一读取 | 一致（掉鳞逻辑）/ 未验证（不可拾取与可烧毁，仅见 `:182` 判定「正在燃烧或已烧焦的鳞片不可吞」） |
| 17 噬魂蛇·吞鳞回血 | 半血后吞鳞回血每个 1000 | `lj_soul_devouring_snake.lua:304-308,401` 半血解锁；`:205-214` `DoDelta(1000, false, "lj_soul_snake_devour")` | 一致 |
| 17 噬魂蛇·毒沼喷涌 | 减速 60% 持续 4 分钟 CD 15 秒 | `prefabs/effects/lj_soul_snake_fx.lua:72` `SetExternalSpeedMultiplier(...,.4)`（降为 40% 速度＝减速 60%）；`:127` `DoTaskInTime(240, StopSwamp)`；冷却 `lj_soul_devouring_snake.lua:93` `swamp = 15` | 一致（毒沼半径 2.5 码，见 `lj_soul_snake_fx.lua:54`） |
| 17 噬魂蛇·定身石化 | 4×4 范围 3 秒 CD 30 秒 | 范围 `lj_soul_devouring_snake.lua:257` `PETRIFY_RANGE = 16`（4 格半径的圆，即 8×8 格），由 `stategraphs/SGlj_soul_devouring_snake.lua:182` 无参调用 `DoPetrify()`；石化时长 `prefabs/effects/lj_debuffs.lua:772-778` `duration = 3`（玩家状态由 `lj_soul_devouring_snake.lua:274` 传 3）；冷却 `lj_soul_devouring_snake.lua:94` `petrify = 30` | 不符（范围是半径 4 格的圆，不是 4×4 格） |
| 17 噬魂蛇·剧毒禁锢 | 缠住 5 秒 | `prefabs/effects/lj_debuffs.lua:781-788` `lj_soul_snake_bind_debuff` `duration = 5` | 一致 |
| 17 噬魂蛇·掉落 | 噬魂蛇皮3、怪物肉5、魔晶2、魔核6、魔核碎片10、红宝石2、紫鳞妖火1 | `lj_soul_devouring_snake.lua:538-547` 与文档逐项相同（`lj_purplemonster_flame` 即紫鳞妖焰） | 一致 |
| 18 月蚀晶翼狮·血量护甲 | 血量 24000，攻击间隔 2.8 秒，护甲 15% | `prefabs/bosses/lj_moon_lion.lua:1050-1051` 24000 / `.15`；`lj_moon_lion.lua:1054` `SetDefaultDamage(0)`——本体普攻 0 伤，全部伤害由技能帧打出；`combat:SetAttackPeriod` 未调用 | 不符（无普攻，也就没有 2.8 秒攻击间隔） |
| 18 月狮·普攻 60 | 普攻 60 | 无普攻；最接近的是 `lj_moon_lion.lua:717` 60% 概率选两段爪，状态图 `stategraphs/SGlj_moon_lion.lua:131,137` 各 35 伤（合计 70），`SGlj_moon_lion.lua:99` 单段爪 70 伤 | 不符 |
| 18 月狮·花朵回血 | 周围 5 格地皮内有花则每朵每 10 秒回 60 血 | `lj_moon_lion.lua:738` `FLOWER_RANGE = 20`（5 格）；`:741-751` `DoDelta(#flowers * 60)`；`:760` 每 10 秒一次；花由飞弹落点生成（`:202-205`） | 一致 |
| 18 月狮·采集打断 | 被采集花朵会打断回血并触发狮吼震慑 | `lj_moon_lion.lua:766-785` 监听 `plantkilled`，范围内玩家采花时重排回血计时并强制一次狮吼（`_lj_force_roar`） | 一致 |
| 18 月狮·曼德拉草昏睡 | 靠近曼德拉草昏睡 8 秒 | `lj_moon_lion.lua:831` `MANDRAKE_SLEEP_TIME = 8`；`:820-828` 检测半径 4（1 格）；`:834-852` 触发后 `GoToSleep(8)` 并进入 60 秒冷却；`:788-790` 不会自然入睡 | 一致 |
| 18 月狮·晶爪猛击 | 70 伤 CD 4 秒身前 3 格 | 伤害 70、扇形半径 `lj_moon_lion.lua:538` `CLAW_RANGE = 3`（3 码≈0.75 格）；冷却 `:647` `claw = 8` | 不符（范围是 3 码不是 3 格；CD 为 8 秒） |
| 18 月狮·鳞粉飞弹 | 3 枚每发 40，爆炸半径 1.5 格，CD 12 秒，飞行 8 格 | 三路弹道 `lj_moon_lion.lua:46-51`；每发 40 `:199`；爆炸半径 `:199` `DealAreaDamage(..., 1.5, 40)`（1.5 码）；冷却 `:648` `missile = 18`；最大射程 `:220` `MISSILE_MAX_RANGE = 32`（8 格） | 不符（爆炸半径 1.5 码、CD 18 秒） |
| 18 月狮·狮吼震慑 | 全屏 6 格无伤但僵直 1.2 秒、武器掉落、CD 10 秒 | 范围 `lj_moon_lion.lua:583` `ROAR_RANGE = 24`（6 格）；`:586-592` 对范围内玩家 `ApplyHitstunPulses(inst, target, 1.2)` 并 `DisarmPlayer`；僵直靠 `:118` 推送 `damage = 0` 的受击事件；冷却 `:642` `ROAR_CD = 20` | 不符（CD 为 20 秒） |
| 18 月狮·裂地囚步 | 以自身 8 地皮为中心生成限时陷坑 3 秒、两段各 60 伤、减速 70% | 范围 `lj_moon_lion.lua:594` `GROUND_BIND_RANGE = 32`（8 格）；`:597-625` 在范围内玩家脚下生成临时 `antlion_sinkhole`；`:530-531` 三段塌陷，`:501-503` 仅第 1、3 段各 60 伤（共 2 次 60）、第 3 段结束时清理（约 3 秒）；`:413` 另有每秒 1 点持续伤害；`:514` 注释明写「只造成伤害，不减速」 | 不符（无减速；另有每秒 1 伤持续伤害） |
| 19 妖蝠 | 初始血量 300，攻击 25，攻击频率 5 秒；1 格地皮内撕咬，超范围冲刺；掉落怪物肉1或蝙蝠翅膀1 | `prefabs/creatures/lj_bats.lua:282,286` 300 血 / 25 伤；`:287` 攻击周期用 `TUNING.BAT_ATTACK_PERIOD`（DST `scripts/tuning.lua:981` = 1 秒）；`:151,163-167` 近战 `MELEE_RANGE = 4`（1 格）否则 `sprint_pre`，冲刺距离 `stategraphs/SGlj_bat.lua:49` `SPRINT_DISTANCE = 12`（3 格）；`:296` 掉落只有 `monstermeat`，全仓库没有 `batwing` | 不符（攻击周期 1 秒；无蝙蝠翅膀掉落） |
| 20 暗影血蝠·基础 | 血量 2000，伤害 55 | `lj_bats.lua:282,286`（`lj_demon_bat` = `is_demon` true）；中文名见 `main/localization/language_zh.lua:102` | 一致 |
| 20 暗影血蝠·音波 | 4×4 地皮范围、每 1.5 秒僵直 0.5 秒、持续 9 秒、CD 30 秒 | `prefabs/effects/lj_bat_sound_wave.lua:79` 查找半径 8（2 格，即 4×4 格）；`:98,126` 每 0.5 秒 `Pulse` 一次，`:84-88` 推 `damage = 0` 的受击事件（形成一次受击僵直）；`:127` 持续 9 秒；`lj_bats.lua:322` CD 30 秒 | 不符（脉冲每 0.5 秒一次，不是 1.5 秒） |
| 20 暗影血蝠·召唤 | 半血后召唤妖蝠 CD 15 秒 | `lj_bats.lua:139-143` 生命 ≤50% 才可召唤；`:203-222` 每次生成 1 只 `lj_blood_bat`；`:325` CD 15 秒 | 一致 |
| 20 暗影血蝠·掉落 | 血蝠精血1、怪物肉2 | `lj_bats.lua:294` `SetLoot({ "lj_bat_blood", "monstermeat", "monstermeat" })`，`lj_bat_blood` 中文名「血蝠精血」（`language_zh.lua:104`） | 一致 |
| 21 夜蝠巢穴·妖蝠 | 每个巢穴 6 只妖蝠（5 分钟刷 1 只，最多 6） | `prefabs/creatures/lj_bat_nest.lua:252-254` `childname = "lj_blood_bat"`、`SetMaxChildren(6)`、`SetRegenPeriod(300, 0)`；`:255` 另有 `SetSpawnPeriod(20, 0)`（20 秒放出 1 只）；`:231-232` 只有 `structure`+`bat_nest` 标签，**没有** `workable` 组件（不可破坏） | 一致 |
| 21 夜蝠巢穴·暗影血蝠 | 1 只暗影血蝠（45 分钟刷 1 只，最多 1） | `lj_bat_nest.lua:26,31-41` `DEMON_BAT_REGEN = 2700`；`:49-52,67-84` 同时只跟踪并保留 1 只；`:149-159` 白天收回、黄昏放出 | 一致 |

---

## 文档完全没提到、但代码里存在的内容

以下均为本次实际读到的实现，文档说法中没有任何对应条目。

**建筑与容器**

1. 丹炉有完整的「丹劫」失败系统：按品阶 `low/mid/high` 设置炼制时长 2/4/8 分钟、成功率 50%/50%/20%、丹劫间隔（`main/config/lj_alchemy_defs.lua:5-33`），放入强异火（`lj_flame_strong`）必定成功（`components/lj_alchemy_furnace.lua:471`）；炸毁时不返还材料（`prefabs/structures/lj_alchemy_furnace.lua:32-35`）。
2. 荒界箱除返鲜/收集/无限堆叠外，还有「整理（按名称排序）」「封（关闭）」「安全入库（只收箱内已有种类）」三个按钮（`main/ui/containers.lua:358-362`、`prefabs/structures/lj_huangjie_box.lua:186-236,444-451`）。
3. 悟道台打坐可触发小阶/大境界突破（`components/lj_realm_value.lua:163-243`）；死亡掉一个小阶并被锁定，需服清心丸解除（`lj_realm_value.lua:26-30,260-299`）。
4. 灵玉台可插回/取回月魄凝液瓶，并按台上记录的灵液比例还原瓶子（`prefabs/structures/lj_reiki_table.lua:82-127,208-228`）。
5. 灵虚光盏在分裂火耗尽后自动熄灭并切回 `idle_off`（`prefabs/structures/lj_reiki_tablelamp.lua:96-114`）。
6. 残骸祭坛可以被锤回「破碎残骸」状态并重新施工（`prefabs/structures/lj_remains_altar.lua:162-173`）。
7. 聚气淬具匣的展示槽会调用武器的 `onequipfn` 实时显示手中物件，并在移除/锤毁时清理符号（`prefabs/structures/lj_cuiju_box.lua:55-86,239-273`）。

**阵法**

8. 阵旗之间存在最小间距 12（3 格，`main/formations/util.lua:50-56`）、最大连接 24（6 格）与闭环外接矩形 48（12 格）三重限制；同一枢纽落在两个闭环内、或两个闭环互相重叠都会 `CONFLICT` 失效（`components/lj_formation_manager.lua:106-128`）。
9. 未放枢纽的闭环会在阵旗焦点中显示为 `NO_PIVOT` 状态（`lj_formation_manager.lua:140-151`），并有 7 种状态名（`main/config/lj_formation_defs.lua:23-32`）。
10. 四季核心额外消除作物的季节压力并把 `good_seasons` 覆盖为四季（`main/formations/effects.lua:45-59,140-144`）。
11. 灵植核心还让作物夜间生长、成熟不腐烂、腐烂可复苏、移植枯竭可复原（`main/formations/effects.lua:62-171`）。
12. 恒温晶核还阻止自燃与被点燃、阻止冰冻、清除已有的冻住/闷烧/燃烧状态（`main/formations/register.lua:104-175`、`effects.lua:174-193`）。
13. 锁魔阵允许骑乘玩家连人带坐骑通过（`main/formations/util.lua:72-74`）。
14. 玄阵枢纽的归还材料为魔晶×1、树枝×2、电子元件×2（`prefabs/formations/lj_supernatural_power_pivot.lua:90`）。

**灵植与资源**

15. 融灵草与彼岸花都可用铲子挖起并重新种植，移植后需施肥才会重新生长（`prefabs/plants/lj_reiki_grass.lua:46-49,93-104,154-159`；`prefabs/plants/lj_red_magic_flower.lua:45-48,93-104,156-161`）。
16. 紫晶塑体花每朵附近最多同时存在 10 朵原版花（`prefabs/plants/lj_purple_magic_flower.lua:81`），月狮死亡后花进入 20 天重生周期（`:138-145`）。
17. 蝴蝶岛每个骨架附带 1 朵彼岸花与 1 份魔核或魔晶（`main/world/butterfly_winter.lua:134-155`）。

**异火与线索**

18. 异火分为「本体 / 分裂（消耗品）」两类，分裂火点燃目标或作为燃料时消耗自身，燃料补充为最大值 50%（`prefabs/alchemy/lj_flame.lua:243-252`）。
19. 异火可放入虚空戒（只收本体，`main/ui/containers.lua:11-15`）、灵虚葫（8 格，只收丹药与异火，`containers.lua:18-39`）；这些容器在白名单里不会被本体火焚毁（`lj_flame.lua:13-20`）。
20. 灵虚葫会自动吸收 16 范围内的异火（`components/lj_reiki_gourd_proxy.lua:158-187`），吸收后每秒扣灵力/生命并点燃主人一次（`components/lj_reiki_gourd.lua:169-198`）。
21. 紫鳞妖焰本体可右键解锁魂幡的炼魂（`main/interactions/actions.lua:132-134`、`components/lj_soul_banner.lua:217`）；魂幡只有 `unlocked` 布尔状态，没有等级。
22. 五个线索物品各有独立的解锁方式：冰霜线索用镐挖 6 下（`prefabs/quests/lj_logs.lua:351`）、焦黑鳞片降温到 ≤5 度（`lj_logs.lua:135-139`）、狂鬃线索斧砍 6 下（`lj_logs.lua:353`）、灵煊线索拾取即开始计时（`lj_logs.lua:220-222`）、紫鳞卷轴烘干或点燃（`lj_logs.lua:169-182`）。
23. 冰霜线索有一条 4 段土堆追踪链，第 4 处生成原版巨鹿（`lj_logs.lua:280-349`、`components/lj_log_quests.lua`）。
24. 阅读日志需境界 `major >= 5`（入微），但线索从开局就投放（`main/config/lj_log_defs.lua:59`、`components/lj_log_quests.lua:350`）。

**生物与 Boss**

25. 炽岩蝎龙有「全局技能空档」4 秒（`prefabs/bosses/lj_chiyan_scorpion_dragon.lua:191`），冲撞会破坏沿途可工作物与 `smashable` 目标（`:344-408`）。
26. 毒蝎幼虫有独立状态图，攻击与跳跃状态带 `no_stun`（`stategraphs/SGlj_little_scorpion.lua:42,75,120`），且会共享目标（`lj_chiyan_scorpion_dragon.lua:646-653`）。
27. 噬魂蛇的中毒会随时间加重伤害并切换 4 级附着特效，持续 240 秒、每 10 秒结算一次（`prefabs/effects/lj_debuffs.lua:725-769`、`prefabs/effects/lj_soul_snake_fx.lua:235-268`）。
28. 月蚀晶翼狮不会自然入睡，反复被催眠会递增抗性（`lj_moon_lion.lua:786-790,1096-1100`）；每枚飞弹落地还会留下一朵原版花（`:202-205`）；有地面冲击波组件（`:1082-1090`）。
29. 月狮由紫晶塑体花召唤且 `persists = false`，不随存档独立保存（`prefabs/plants/lj_purple_magic_flower.lua:169-184`）。
30. 夜蝠巢穴不可被锤毁（`prefabs/creatures/lj_bat_nest.lua` 全文件无 `workable`），白天会强制收回全部在外的妖蝠与暗影血蝠（`:109-168`）。

**世界与系统**

31. 残骸祭坛岛由 `components/lj_remains_island_manager.lua` 在空海上按静态地皮表放置，含独立的局部气候（`:256-293`、`main/world/island_climate.lua`）。
32. 蝴蝶岛是独立于主陆的静态四翼岛群，有管理器、存档锚点与管理控制台命令 `c_ljhd`（`components/lj_butterfly_island_manager.lua`、`main/admin/console.lua:4-27`、`prefabs/world/lj_butterfly_island_anchor.lua`）。
33. 蝴蝶岛二号翼是固定冬季气候（环境温度 -10、降雪、地面积雪、建筑积雪，`map/lj_butterfly_winter_data.lua:4-13`），该翼还生成企鹅冰场、冰矿 5~8 处与 4 处遗骸（`map/lj_butterfly_winter_data.lua:16-20`、`main/world/butterfly_winter.lua:116-155`）。

---

## 代码里找不到对应实现的文档内容

1. **`lj_warcraft_forest` / 魔兽森林预制体**：全仓库 `grep` 无 `warcraft`、无预制体名；「魔兽森林」只出现在 1 条注释里（`components/lj_log_quests.lua:323`）。见下一节。
2. **`lj_reiki_cultivatepool` / 玄灵培育池**：全仓库 `grep` 无 `cultivatepool`、无「培养池」、无「玄灵」，两者在代码中都不存在。
3. **「1~3 级魂幡」**：`components/lj_soul_banner.lua` 只有 `unlocked` 布尔与 `pendingloot` 计数（`:52,159,171,204`），没有等级字段；魂幡也不在制作栏（`main/localization/language_zh.lua:32`）。
4. **「彼岸花种」**：5% 额外产物是 `lj_red_magic_dug_flower`，中文名「彼岸花根」（`main/localization/language_zh.lua:327`）；没有种子物品。
5. **「蝙蝠翅膀」**：`prefabs/creatures/lj_bats.lua:296` 妖蝠只掉 `monstermeat`；全仓库无 `batwing`，也未做任何掉落概率分支。
6. **异火放「背包」超 10 秒焚毁**：只有「容器或玩家物品栏」这一个实现路径（`prefabs/alchemy/lj_flame.lua:114-127`，取 `owner.components.container or owner.components.inventory`），没有区分背包（krampus sack 之类的容器）与物品栏的额外逻辑。
7. **「靠近解锁……」中的等级/科技说明**：8 件物品确实都是祭坛科技（`TECH.ETHEREAL_REALM_ONE`），但代码里没有「靠近时自动解锁」的机制——祭坛是 `prototyper` 科技站，配方标记为 `nounlock = true`，属原版「在科技站旁可制作」的行为（`main/crafting/recipes.lua:102-348`、`prefabs/structures/lj_remains_altar.lua:75-81`）。文档若把它描述成一次性永久解锁，则无对应实现。
8. **「四季调和阵 12×12 需最少 4 阵旗」**：代码最小阵旗数为 8（`main/config/lj_formation_defs.lua:3`），4 面旗在代码里必然报 `TOO_FEW`，不存在「4 面即可」的实现。
9. **蝎龙「沙砾喷发减速 40% + 每秒 10 伤」** 与 **月狮「裂地囚步减速 70%」**：这两个减速数值在代码中不存在（`lj_chiyan_scorpion_dragon.lua:212-225`、`lj_moon_lion.lua:413,514-536` 都只做伤害与陷坑）。

---

## 魔兽森林 vs 蝴蝶岛

**判断：文档的「魔兽森林（冬季板块）」就是代码里的蝴蝶岛二号翼（蝴蝶岛冬季板块）。**依据如下（均为实际读到的代码内容）：

1. **代码注释把二号翼直接叫作「魔兽森林」。**`components/lj_log_quests.lua:323` 写着「紫鳞任务仅使用魔兽森林的既有冻结池塘，缺失时保留日志。」，紧接着 `:325` 的实现是 `FindPositionNearPrefab("lj_butterfly_frozen_pond", 8, 14)`——用蝴蝶岛的冻结池塘来定位噬魂蛇的刷新点。也就是说，注释里的「魔兽森林」= 有 `lj_butterfly_frozen_pond` 的那块地，而冻结池塘只出现在蝴蝶岛模板里（`map/lj_butterfly_island_data.lua:197` 是唯一一处 `lj_butterfly_frozen_pond` 固定实体）。

2. **冬季板块由「二号板块」界定，而二号板块就是蝴蝶岛的四翼之一。**`main/world/butterfly_winter.lua:1` 注释「仅新蝴蝶岛的冬季布景生成与气候恢复」；`:11-18` 按地皮把蝴蝶岛格点分成 4 个 region，其中 `region = 2` 定义为 `MARSH` 或 `CAVE`（鸟粪）地皮，其余裸地按中央水道分给 1/3/4 号翼；`map/lj_butterfly_winter_data.lua:1` 注释直接写「二号板块的固定冬季与随机布景参数」。而 `map/lj_butterfly_island_data.lua:12` 的 `tile_names = { D = "DIRT", M = "MARSH", C = "CAVE" }` 说明这四种地皮都属于同一张蝴蝶岛模板。

3. **「冬季」是二号翼的固定气候，而不是独立世界或独立地块。**`map/lj_butterfly_winter_data.lua:4-13` 定义 `enabled = true, season = "winter", temperature = -10, colourcube/snow_fx/ground_snow/building_snow = true`；`main/world/island_climate.lua:4-5` 同时 require 蝴蝶岛蓝图与这份冬季配置，`main/world/butterfly_winter.lua:178-191` 只在 `climate.GetClimateConfigAtXZ(ex, ez) == CONFIG.climate` 的范围内刷积雪——即气候绑定在蝴蝶岛二号翼的坐标上。

4. **异火线索「紫鳞」任务的场景与文档「魔兽森林」描述吻合。**`lj_log_defs.lua:40-49` 中 `purple` 的 Boss 是 `lj_soul_devouring_snake`，其刷新点由 `lj_log_quests.lua:325` 在冻结池塘附近选取；`main/world/butterfly_winter.lua:211-223` `M.FindPond` 也只在蝴蝶岛冻结池塘中找最近的一个。

5. **名称层面确实没有任何 `lj_warcraft_forest` 预制体**：`scripts/map/lj_butterfly_island_data.lua:13` 的 `topology_id = "StaticLayoutIsland:LJButterflyIsland"` 是这个板块在代码里的唯一身份标识，`map/lj_butterfly_island_worldgen.lua:61` 也用 `LAYOUT_NAME = "LJButterflyIsland"`。文档的「魔兽森林」是**设计名**，代码里对应实现叫蝴蝶岛（冬季）。

**与「融灵草生成地」的交叉验证**：文档说融灵草生成在「魔兽森林夜蝠巢穴附近」，代码里 `main/world/butterfly_winter.lua:119-129` 正是遍历蝴蝶岛模板中的 `lj_bat_nest`（`map/lj_butterfly_island_data.lua:113-116` 共 4 处），在每个巢穴旁生成 1~3 株 `lj_reiki_grass`。这条也把「魔兽森林」指向蝴蝶岛（冬季二号翼），而不是主陆森林。

**需要注意的一处不一致**：文档把融灵草的野外生成地概括为「森林地皮蜘蛛巢 + 魔兽森林夜蝠巢穴」，但代码里两处的**地皮条件不同**——主陆那一批要求蜘蛛巢本身位于 `WORLD_TILES.FOREST`（`map/lj_resource_worldgen.lua:77`），岛上那一批却要求在鸟粪地皮 `GUANO`（即 `CAVE` 地皮）上（`main/world/butterfly_winter.lua:125`）。文档表述会把岛上那批误读成「森林地皮」。

---

## 备注（本次未验证的部分）

以下内容本次没有实际读到或没有读到可下结论的代码，因此上表按「代码中未找到」或「未验证」处理，不做推测：

- 融灵草的「可催熟」：只用到了原版 `pickable` 组件，本次没有追踪催熟（肥料）时原版组件的完整调用链。
- 噬魂蛇鳞片「玩家无法拾取、可用异火烧毁」：只读到「燃烧中/已烧焦的鳞片不可被吞」（`prefabs/bosses/lj_soul_devouring_snake.lua:182-185`），没有逐行读取 `prefabs/materials/lj_soul_snake_skin.lua`。
- 妖蝠「超范围冲刺」的伤害数值：只读到冲刺触发距离 `stategraphs/SGlj_bat.lua:49` `SPRINT_DISTANCE = 12` 与状态链 `SGlj_bat.lua:180-270`，没有读取冲刺各状态的时间轴数值。
- 文档提到的「灵虚葫」本体预制体（`prefabs/equipment/lj_reiki_gourd.lua`）本次只读了组件与代理组件，未逐行读取预制体本体文件。
