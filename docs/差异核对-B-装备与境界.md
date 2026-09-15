一句话总结：这份《装备与境界》设计稿的大部分硬数值与代码一致（淬铁灵剑 45/1.5/+10% 移速/100 耐久、灵韵 78/20% 暴击/×1.8/间隔 1.2/射程 10/耐久 200/耐久 0 降为 10、星陨 88/22% 暴击/×2/间隔 1/距离 2/耐久 300/5 次 25% 充能/10 秒清零/+5 增伤/技能 10 灵力 2 秒冷却、甲冠 1500 耐久 80% 防御与魔晶每颗 +1%、血蝠精血修满、以血修甲 5 秒脱战 2 秒扣 1 血回 10 耐久、虚空戒 1 格与 10 点灵力点火补燃料、灵虚葫 8 格与 16 范围自动吸火、魂幡紫鳞妖焰解锁与 1 影怪 1 魔晶），但多处不成立：焚灼/冰蚀并不是「+15」「+30」，而是持续 8 秒、每 0.5 秒 16 点的减益；玄冰灌注没有「眩晕」；淬铁灵剑的魔核碎片 1 个只填 10 点耐久；陨火刺基础伤害是 140（+10 位面合计 150）；跨大境界所需的丹药从辟谷境起就要（不是引气）；灵力枯竭靠原版睡意/昏沉实现，代码里没有「移速降低 90%」这个数值；「灵技」这一系统在代码中完全不存在。

## 逐条对比

| 项目 | 文档说法 | 代码实际（标注文件名与行号） | 结论 |
| --- | --- | --- | --- |
| 灵力初始值 | 50 | `self.current = 50`、`self.max = 50`，lj_spirit_value.lua:9-10 | 一致 |
| 灵力上限 | 120 | `self.max = math.min(120, 50 + self.realm_bonus)`，lj_spirit_value.lua:44；读档时也 clamp 到 50~120，lj_spirit_value.lua:118。上限随境界加成增长，具灵境 spirit=70 → 50+70=120，lj_realm_defs.lua:28 | 一致 |
| 每分钟回复 3.3 点 | 3.3 / 分钟 | `inst:DoPeriodicTask(60, ... self:DoDelta(3.3))`，仅存活玩家结算，lj_spirit_value.lua:21-25 | 一致 |
| 枯竭判定为低于 5 | < 5 | `if self.current < 5 and self.weak_task == nil then self:StartWeakness()`，lj_spirit_value.lua:54-56；复活与读档时同样判定，lj_spirit_value.lua:14-18、28-30 | 一致 |
| 枯竭时移速降低 90% | -90% 移速 | 组件只做 10 秒计时（`duration = math.clamp(tonumber(duration) or 10, 0, 10)`，lj_spirit_value.lua:67），实际效果是原版睡意/昏沉：有 sleeper 时 `AddSleepiness(4, duration)`，否则 `grogginess:AddGrogginess(2, duration)`，两者都没有则 `PushEvent("knockedout")`，lj_spirit_value.lua:84-96。全组件没有任何 -90% 移速数值，也没有 locomotor 乘数 | 不符 |
| 虚弱解除后恢复 10 点灵力 | +10 | 计时结束时 `self.weak_task = nil; self:StopWeakness(); self:DoDelta(10)`，lj_spirit_value.lua:70-74 | 一致 |
| 境界数量与名称 | 共 9 个：凡境/淬体/炼筋/辟谷/引气/入微/超凡/合婴/具灵 | `max_major = 8`（major 取值 0~8，即 9 个境界），lj_realm_defs.lua:3；`REALM_NAMES[0..8]` 与文档逐字一致，language_zh.lua:474-484 | 一致 |
| 每境界 9 阶 | 9 阶 | `max_minor = 9`，lj_realm_defs.lua:4；`MINOR_NAMES` 一~九，language_zh.lua:486-496 | 一致 |
| 击杀生物得经验 | 击杀得经验 | `GetKillExpFromTarget` = 目标基础最大生命 × `TUNING.LJ_REALM_EXP_RATE`（默认 .05，可由配置 `realm_exp_rate` 改动），lj_realm_value.lua:131-137、tuning.lua:6、lj_demonization_defs.lua:23 | 一致 |
| 15 个地皮范围内 | 15 地皮 | `kill_exp_radius = 60`（源码注释「原稿15格地皮，每格4世界单位」），lj_realm_defs.lua:6；判定 `player:GetDistanceSqToInst(inst) <= radius * radius`，realm_combat.lua:49-52 | 一致 |
| 30 秒内参与攻击可获经验 | 30 秒 | `kill_exp_window = 30`，lj_realm_defs.lua:5；每次被攻击记录时间戳并剔除超时项，realm_combat.lua:22-33、47-53 | 一致 |
| 死亡掉一阶 | 掉一阶 | `DropOneMinor()`：minor>1 时 minor-1；minor=1 时降到上一境界第 9 阶；经验重置为该阶起点并 `locked = true`，lj_realm_value.lua:26-29、260-272 | 一致 |
| 需服清心丸才能继续修炼 | 清心丸 | 死亡后 `locked=true`，只有 `UnlockAfterDeath("lj_stillness_pill")` 能解锁（其它道具名直接 return false），lj_realm_value.lua:292-299；吃丹药时调用，lj_pill.lua:50；「清心丸」= lj_stillness_pill，language_zh.lua:262；锁定时提示文本「心神未稳，先服用清心丸才能继续修炼。」，language_zh.lua:145 | 一致 |
| 3→4 阶、6→7 阶、9 阶→下一境界需要打坐 | 同上 | `IsBreakthroughMinor(minor) = minor == 3 or minor == 6 or minor == 9`，lj_realm_value.lua:7-9；配合 `IsAtBottleneck` 与经验封顶，lj_realm_value.lua:48-51、106-108 | 一致 |
| 引气及以上须服特定丹药并打坐 10 秒 | 引气及以上 | `breakthrough_pills` 从 major 3（辟谷）到 major 8（具灵）共 6 种：辟谷丹/引气丹/入微丹/超凡丹/合婴丹/具灵丹，lj_realm_defs.lua:30-37；仅在跨大境界（next_minor == 1）时才要求丹药，且必须是已服下对应 debuff（`self.inst:HasDebuff(required)`），lj_realm_value.lua:140-143。打坐时长 `meditation_duration = 10`，lj_realm_defs.lua:7；判定 `GetTime() - breakthrough_started >= meditation_duration`，lj_realm_value.lua:212-216、223-228 | 不符（丹药要求实际从辟谷境起，不是引气） |
| 淬铁灵剑攻击力 | 45 | `inst.components.weapon:SetDamage(45)`，lj_ordinary_sword.lua:73 | 一致 |
| 淬铁灵剑攻击范围 | 1.5 | `SetRange(1.5)`，lj_ordinary_sword.lua:74 | 一致 |
| 淬铁灵剑手持 +10% 移速 | +10% | `inst.components.equippable.walkspeedmult = 1.1`，lj_ordinary_sword.lua:96 | 一致 |
| 淬铁灵剑耐久 100（可攻击 100 下） | 100 | `finiteuses:SetMaxUses(100)`、`SetUses(100)`，lj_ordinary_sword.lua:79-81；每次命中由基础 weapon 组件扣 1 点（基础游戏 scripts/components/weapon.lua:111-119：`finiteuses:Use(attackwear or 1)`） | 一致 |
| 淬铁灵剑可用魔核碎片填充，1 个填 100 | 碎片 1 个 = 100 | `repairable.repairmaterial = "lj_magic_debris"`，lj_ordinary_sword.lua:85-87；材料侧 `finiteusesrepairvalue = 10`，lj_magic_core.lua:39-42（魔核才是 100，lj_magic_core.lua:43-46）；「魔核碎片」= lj_magic_debris，language_zh.lua:3。修复时按该值 `finiteuses:Repair(...)`，基础游戏 scripts/components/repairable.lua:135-141 | 不符（1 个碎片只回 10 点耐久，10 个才回满 100） |
| 灵韵攻击力 | 78 | 箭弹 `weapon:SetDamage(big_arrow and 300 or 78)`，lj_reiki_bow.lua:348；`GetArrowDamage` 普通箭返回 78，lj_reiki_bow.lua:103、268 | 一致 |
| 灵韵暴击率 | 20% | `projectile._lj_crit = ... math.random() < 0.2`，lj_reiki_bow.lua:119 | 一致 |
| 灵韵暴击伤害 | ×1.8 | `damage = damage * 1.8`，位面伤害同时 ×1.8，lj_reiki_bow.lua:105-108 | 一致 |
| 灵韵冰蚀伤害 | +30 | 冰蚀在代码中是减益 `lj_reiki_bow_ice_debuff`：`duration = 8`、每 0.5 秒 `health:DoDelta(-16, nil, "lj_reiki_bow_ice", ...)`，lj_debuffs.lua:678-695；武器侧只是每次命中挂/刷新该减益，lj_reiki_bow.lua:69-73、83-84。全仓库没有 +30 这一冰蚀数值 | 不符（实际每 0.5 秒 16 点、持续 8 秒） |
| 灵韵 +10 点位面伤害 | +10 位面 | `local planar_damage = 10`，返回 `{ planar = planar_damage }`，lj_reiki_bow.lua:104、110 | 一致 |
| 灵韵攻击间隔 | 1.2 秒 | 装备时 `owner.components.combat:SetAttackPeriod(1.2)`，卸下恢复原值，lj_reiki_bow.lua:207-210、229-232 | 一致 |
| 灵韵射程 | 10 | `weapon:SetRange(10)`，lj_reiki_bow.lua:269（箭弹自身 `projectile:SetRange(16)`、大箭 20，lj_reiki_bow.lua:357，文档未写） | 一致 |
| 灵韵耐久 200 | 200 | `finiteuses:SetMaxUses(200)`、`SetUses(200)`，lj_reiki_bow.lua:273-275 | 一致 |
| 灵韵攻击一次减 1 耐久 | -1 | `inst.components.finiteuses:Use(1)`，lj_reiki_bow.lua:122-124；箭弹设了 `projectile.has_damage_set = true`（lj_reiki_bow.lua:358）且箭弹自身没有 finiteuses 组件，因此一次射击合计只扣 1 点 | 一致 |
| 灵韵可用魔核填充（1 个填 100） | 1 个 = 100 | `repairable.repairmaterial = "lj_magic_core"`，lj_reiki_bow.lua:277-279；lj_magic_core.lua:43-46 `finiteusesrepairvalue = 100` | 一致 |
| 灵韵耐久 0 时伤害降为 10 | 10 | `if inst._lj_depleted then return 10 end`，lj_reiki_bow.lua:95-97；耗尽时也不再挂冰蚀，lj_reiki_bow.lua:79-81 | 一致 |
| 灵韵冰蚀阈值：小型 2 层=2 秒、中型 3 层=1.5 秒、大型 5 层=1 秒 | 2/2、3/1.5、5/1 | `GetFreezeProfile`：`target:HasTag("epic")` → 5 层、1 秒；`health.maxhealth >= 900` → 3 层、1.5 秒；其余 → 2 层、2 秒，lj_reiki_bow.lua:32-42；到阈值时 `AddColdness(math.max(threshold, ResolveResistance()), freeze_time)`，lj_reiki_bow.lua:50-57。分类依据是 epic 标签与最大生命 ≥900，不是体型字段 | 一致 |
| 玄冰灌注：右键主动、消耗 20 灵力、造成 300 伤害、冰冻 3 秒、冷却 12 秒 | 20 灵力、300、3 秒、12 秒 | 灵力门槛 `current >= 20`，lj_reiki_bow.lua:140；释放后 `DoDelta(-20)` 与 `Discharge(12)`，lj_reiki_bow.lua:158-163；`rechargeable:SetChargeTime(12)`，lj_reiki_bow.lua:297-299；大箭伤害 `return 300`，lj_reiki_bow.lua:99-101、348；命中 `FreezeTarget(target, 3)`，lj_reiki_bow.lua:86-88、61-66 | 一致 |
| 玄冰灌注「眩晕」目标 | 眩晕并冰冻 | 命中只做 `freezable:AddColdness(...)` + `freezable:SpawnShatterFX()`，lj_reiki_bow.lua:61-66；全仓库未找到与该技能关联的 grogginess/stun/knockedout 调用 | 代码中未找到 |
| 灵韵击杀任意生物恢复 5 点灵力 | +5 | 装备时监听 owner 的 `killed` → `lj_spirit_value:DoDelta(5)`，lj_reiki_bow.lua:212-219；卸下移除监听，lj_reiki_bow.lua:234-236 | 一致 |
| 星陨攻击力 | 88 | `weapon:SetDamage(88)`，lj_star_sword.lua:417；`GetStarSwordDamage` 普通分支 `88 + _lj_star_bonus`，lj_star_sword.lua:153 | 一致 |
| 星陨暴击率与暴击伤害 | 22%、×2 | `crit = math.random() < 0.22`，lj_star_sword.lua:155；命中时 `base_damage * 2` 且位面伤害同样 ×2，lj_star_sword.lua:161-163 | 一致 |
| 星陨焚灼 +15（命中挂 8 秒燃烧，每次攻击重置） | +15、8 秒、重置 | 焚灼是减益 `lj_star_sword_burn_debuff`：`duration = 8`、`refresh = REFRESH_RESET`（lj_debuffs.lua:663-665）、每 0.5 秒 `health:DoFireDamage(16, ...)`（lj_debuffs.lua:666-675）；武器侧只负责挂/刷新减益，lj_star_sword.lua:96-100、134-137。没有 +15 的平砍加成 | 不符（实际每 0.5 秒 16 点火焰伤害、8 秒共 16 跳） |
| 星陨 +10 点位面伤害 | +10 位面 | `local PLANAR_DAMAGE = 10`，lj_star_sword.lua:140、154；通过 planardamage 组件结算，lj_star_sword.lua:165-168、422-423 | 一致 |
| 星陨攻击间隔 | 1 秒 | 装备时 `combat:SetAttackPeriod(1)`，卸下恢复原值，lj_star_sword.lua:331-334、358-361 | 一致 |
| 星陨攻击距离 | 2 | `weapon:SetRange(2)`，lj_star_sword.lua:418 | 一致 |
| 星陨耐久 300 | 300 | `finiteuses:SetMaxUses(300)`、`SetUses(300)`，lj_star_sword.lua:425-427 | 一致 |
| 星陨可用魔核填充（1 个填 100） | 1 个 = 100 | `repairable.repairmaterial = "lj_magic_core"`，lj_star_sword.lua:430-432；lj_magic_core.lua:43-46 `finiteusesrepairvalue = 100` | 一致 |
| 星陨耐久 0 时伤害降为 10 | 10 | `else base_damage = 10`，lj_star_sword.lua:156-157；不可用时不再挂焚灼、不充能，lj_star_sword.lua:104-107、134-137 | 一致 |
| 每攻击 5 次充能 25%，满 100% 进入星陨状态 | 5 次 25%、100% | `attack_count >= 5` → 计数清零、`charge = math.min(100, charge + 25)`、`charge >= 100` 时 `_lj_star_active = true`，lj_star_sword.lua:109-117 | 一致 |
| 停止攻击 10 秒充能清零 | 10 秒 | 每次普通命中重置 `inst:DoTaskInTime(10, ClearStarState)`，lj_star_sword.lua:77-82；`ClearStarState` 清零充能、计数、激活标记与增伤，lj_star_sword.lua:67-74 | 一致 |
| 星陨状态下每攻击一下 +5 伤害 | +5/次 | `if inst._lj_star_active then self._lj_star_bonus = (bonus or 0) + 5`，lj_star_sword.lua:119-121；该加成计入基础伤害，lj_star_sword.lua:153 | 一致 |
| 陨火刺：消耗 10 灵力、过程免疫伤害、冷却 2 秒 | 10 灵力、免疫、2 秒冷却 | 灵力 `current < 10` 直接拒绝，lj_star_sword.lua:209-210；冲刺结束后 `DoDelta(-10)`，lj_star_sword.lua:273-275；`health:SetInvincible(true)` 持续 0.8 秒并在冲刺结束后 6 帧还原原无敌状态，lj_star_sword.lua:250-257、280-284；`rechargeable:SetChargeTime(2)` 与 `Discharge(2)`，lj_star_sword.lua:460、277 | 一致 |
| 陨火刺「造成 150 伤害」 | 150 | `aoeweapon_lunge:SetDamage(140)`，lj_star_sword.lua:445；冲刺分支 `base_damage = 140` 且 `planar_damage = 10`，lj_star_sword.lua:149-151。基础值 140，加 10 点 位面伤害后合计 150 | 不符（基础 140 + 位面 10） |
| 星陨击杀任意生物恢复 5 点灵力 | +5 | 装备时监听 owner 的 `killed` → `DoDelta(5)`，lj_star_sword.lua:336-343 | 一致 |
| 骸龙甲 / 晶羽冠耐久 1500 | 1500 | `TUNING.ETHEREAL_REALM.ARMOUR_DURABILITY = 1500`，tuning.lua:14；`armor:InitCondition(TUNING.ETHEREAL_REALM.ARMOUR_DURABILITY, 0.8)`，lj_keel_armour.lua:60-61、lj_crystalcrown.lua:68-69 | 一致 |
| 初始防御 80% | 80% | 同上 `InitCondition(1500, 0.8)`；升级组件每次重算 `armor:SetAbsorption((80 + self.level) / 100)`，lj_armour_upgrade.lua:16 | 一致 |
| 给予魔晶 1 个 +1% 防御（最高 90） | 每颗 +1%，上限 90 | `Upgrade` 每次消耗 1 颗 `lj_magic_crystal` 并 `level + 1`，lj_armour_upgrade.lua:34-57；`MAX_LEVEL = 10`，lj_armour_upgrade.lua:1；吸收 = (80+level)/100 → 10 级为 90%，lj_armour_upgrade.lua:16。右键升级动作 actions.lua:379-407 | 一致 |
| 1 点位面防御（最高 10） | 每颗 +1 点，上限 10 | `planardefense:SetBaseDefense(self.level)`，lj_armour_upgrade.lua:19（0~10 级对应 0~10 点位面防御） | 一致 |
| 血蝠精血 1 个恢复满耐久 | 1 个修满 | `RepairWithBlood`：材料必须是 `lj_bat_blood`，消耗 1 个后 `armor:Repair(armor.maxcondition)`，满耐久时拒绝且不消耗，lj_armour_upgrade.lua:60-75；「血蝠精血」language_zh.lua:104；动作 actions.lua:388-407 | 一致 |
| 「以血修甲」仅在脱战（5 秒内未受伤）时触发 | 5 秒脱战 | `ARMOUR_BLOOD_REPAIR_DELAY = 5`，tuning.lua:16；`GetTime() - self.last_damage_time < 5` 直接返回，lj_blood_armour.lua:87-92；`attacked`、`blocked`、`healthdelta` 掉血都会刷新计时，且主动修甲的扣血原因 `lj_armour_blood_repair` 不计入，lj_blood_armour.lua:21-33。额外条件：`not self.inst:IsNearDanger()`（原版危险判定），文档未写，lj_blood_armour.lua:89 | 一致 |
| 血量 >30% 时每 2 秒扣 1 点血恢复 10 点耐久 | 2 秒、-1 血、+10 耐久 | `ARMOUR_BLOOD_REPAIR_INTERVAL = 2`、`COST = 1`、`AMOUNT = 10`，tuning.lua:15-18；`DoPeriodicTask(2, Repair)`，lj_blood_armour.lua:66-77；`health:DoDelta(-1, true, "lj_armour_blood_repair", false, nil, true)` 后 `item.components.armor:Repair(10)`，lj_blood_armour.lua:99-107（扣血绕过护甲吸收、不触发受击动作） | 一致 |
| 血量 <30% 时既不扣血也不回耐久 | <30% 停手 | 判定写作 `health:GetPercent() <= SETTINGS.ARMOUR_BLOOD_REPAIR_MIN_HEALTH`（0.3）即跳过，lj_blood_armour.lua:88、97（每件装备扣血后再检查一次血线，lj_blood_armour.lua:94-98）：恰好 30% 也会停手 | 一致 |
| 耐久为 0 不消失但不提供保护 | 不消失、无保护 | 两件都 `armor:SetKeepOnFinished(true)`，lj_keel_armour.lua:62、lj_crystalcrown.lua:70；破损（condition <= 0）时 `SetAbsorption(0)`、`planardefense:SetBaseDefense(0)`，并清空护甲标签不再参与分摊伤害，修复后按原等级恢复，lj_armour_upgrade.lua:13-21；检视状态返回 BROKEN，lj_keel_armour.lua:52-54、lj_crystalcrown.lua:60-62 | 一致 |
| 两件同时穿戴可免疫镜像混淆 | 免疫 | `HasMirrorConfusionImmunity`：身体槽必须是 `lj_keel_armour`、头槽必须是 `lj_crystalcrown`，且两件 `armor.condition > 0`，demonization.lua:965-978；抽取混淆时排除（demonization.lua:1011-1014），穿齐时立即解除已有混淆（demonization.lua:980-989、1873-1874） | 一致 |
| 虚空戒开局自带 | 开局自带 | `StartingGift:GrantOnce()` 生成 `lj_void_ring` 与 `lj_ordinary_flame`，尝试把火放进戒指容器再把戒指入包，按 userid 记录、读档不补发，lj_starting_gift.lua:13-48 | 一致 |
| 虚空戒一格空间 | 1 格 | `container:WidgetSetup("lj_void_ring")`，lj_void_ring.lua:57-58；布局 `deepcopy(containers.params.slingshot)`，main/ui/containers.lua:11；基础游戏 `containers.params.slingshot` 只有 1 个 slotpos（Steam 安装包 scripts.zip → scripts/containers.lua:1463-1481） | 一致 |
| 虚空戒可放墟火/异火 | 可放墟火/异火 | `itemtestfn = function(container, item, slot) return item:HasTag("lj_flame_source") end`，main/ui/containers.lua:13-15；所有异火本体都带 `lj_flame_source`，lj_flame.lua:278-279；「墟火」= lj_ordinary_flame，language_zh.lua:164 | 一致 |
| 灵煊尘火放入虚空戒可解锁灵技 | 解锁灵技 | 全仓库检索不到「灵技」或等价标识（grep `灵技`、`lj_skill`、`spiritskill` 均无命中）；戒指容器只按 `lj_flame_source` 标签收纳，没有任何解锁逻辑，main/ui/containers.lua:13-15。「灵煊尘火」实为 `lj_dust_flame`，language_zh.lua:201 | 代码中未找到 |
| 可手持使用灵技 | 手持使用灵技 | 戒指只提供容器与点火/补燃料入口，lj_void_ring.lua:57-66、actions.lua:259-323；没有 spellcaster/skill 相关组件 | 代码中未找到 |
| 手持带火的虚空戒右键可点燃物品、添加燃料、焚烧建筑，消耗 10 灵力值 | 10 灵力、点燃/补燃料/焚烧建筑 | 动作注册在 `EQUIPPED` 的 container 上（须装备在手上），目标需带 `canlight` 或 `BURNABLE_fueled`，actions.lua:313-321；须容器内存在 `lj_flame_source`，actions.lua:204-217、265；燃料类 `fueled:DoDelta(maxfuel * 0.5)`、可燃烧类 `burnable:Ignite(nil, ring, doer)`，两种都先校验 `current >= 10` 再扣 10，actions.lua:269-287 | 一致（「焚烧建筑」没有专门实现，只有对带 burnable 的目标点燃） |
| 灵虚葫 8 格空间 | 8 格 | 跟随葫芦容器 `WidgetSetup("lj_reiki_gourd_deployed")`，lj_reiki_gourd.lua:122-123；布局按两列四行共 8 个 slotpos，main/ui/containers.lua:18-35 | 一致 |
| 灵虚葫右键打开/关闭 | 右键开/关 | mod 中跟随葫芦只注册了一个自定义右键动作「回收」（LJ_REIKI_GOURD_RECALL，actions.lua:57-69），未找到右键开关容器的实现 | 代码中未找到 |
| 打开状态不会因开别的箱子而自动关闭 | 不会自动关闭 | 未找到相关实现；容器参数只有 `openlimit = 1`，main/ui/containers.lua:28；`Open` 被重写为仅允许主人打开，lj_reiki_gourd.lua:124-129 | 代码中未找到 |
| 可鼠标拿起放置地面跟随 | 可放置跟随 | 物品带 `usedeploystring` 与 deployable（`keep_in_inventory_on_deploy = true`），lj_reiki_gourd.lua:50、80-84；`Deploy(pt, deployer)` → `SpawnProxy(pt, owner)` 生成跟随实体并绑定物品与主人，lj_reiki_gourd.lua:63-107 | 一致 |
| 跟随状态下 16 码范围内有异火会自动吸收 | 16 码自动吸收 | `TheSim:FindEntities(x, y, z, 16, { "lj_flame" }, { "INLIMBO" })`，每秒执行一次（`DoPeriodicTask(1, CollectFlames)`），容器满则跳过、成功吸 1 个即返回，lj_reiki_gourd_proxy.lua:19-20、93-99、158-187 | 一致（每秒最多 1 个；吸收会触发主人 60 秒灼烧，见下节） |
| 跟随状态下右键回收 | 右键回收 | `ReikiGourdProxy:Recall(doer)`：非主人返回 false，先把内容物搬回本体容器再移除跟随实体，lj_reiki_gourd_proxy.lua:142-154；`ReikiGourd:Recall` 关闭容器并移除代理，lj_reiki_gourd.lua:110-119 | 一致 |
| 跟随状态下左键开关 | 左键开关 | 未找到左键开合葫芦容器的自定义动作或事件 | 代码中未找到 |
| 魂幡给予紫鳞妖焰可解锁技能「炼魂」 | 紫鳞妖焰解锁炼魂 | `LearnSoul` 要求物品 `lj_purplemonster_flame`、魂幡在地上且未解锁，消耗 1 个后 `SetUnlocked(true)` 并去掉 locked 标签，lj_soul_banner.lua:217-230、156-161；动作名「领悟炼魂」，actions.lua:101-142、language_zh.lua:43；「紫鳞妖焰」language_zh.lua:209 | 一致 |
| 插在地上可自动识别影怪类生物吸入魂幡 | 插地自动吸魂 | 条件为已解锁 + 已插地（`lj_soul_banner_deployed`）+ 在地面 + 未休眠，lj_soul_banner.lua:60-62；每 0.3 秒扫描一次（`SOUL_BANNER_INTERVAL`，tuning.lua:11），半径 `SOUL_BANNER_RADIUS = 3 * 4 = 12`（tuning.lua:9），lj_soul_banner.lua:131-144、384-407；逐帧把目标拉向幡心、距离 ≤ 0.35 判定吸入，lj_soul_banner.lua:326-350 | 一致（吸魂半径 12，文档未写） |
| 「影怪类生物」的范围 | 影怪类生物 | 不是按类别标签泛指，而是固定名单 `TARGET_PREFABS = { terrorbeak = true, crawlinghorror = true, nightmarebeak = true, crawlingnightmare = true }`，lj_soul_banner.lua:1-6，并要求目标有 Physics 与 sg，lj_soul_banner.lua:34-36；检索标签必须是 shadowcreature / nightmarecreature / lj_can_be_refined 之一，lj_soul_banner.lua:8、395；另有入魔影体分身（`_lj_is_shadow_clone` 且带 `lj_can_be_refined`）被直接炼化，lj_soul_banner.lua:239-250、397-398 | 不符 |
| 每吸入一个单体影怪转化成 1 个魔晶 | 1 影怪 = 1 魔晶 | 每次吸入 `self.pendingloot = self.pendingloot + 1`，lj_soul_banner.lua:305-323、239-250；收势动画结束后逐个 `SpawnPrefab("lj_magic_crystal")`，lj_soul_banner.lua:20-31、74-92 | 一致 |
| 魔晶直接掉落在摆放位置正下方 | 摆放位置正下方 | 产物坐标即魂幡自身世界坐标：`loot.Transform:SetPosition(inst.Transform:GetWorldPosition())`，lj_soul_banner.lua:20-24；并且要等 `flutter_pst` 播完才生成，lj_soul_banner.lua:73-92 | 一致 |

## 文档完全没提到、但代码里存在的机制或数值

**灵力与境界**

- 境界属性表 `attrs`（每境界的生命加成、移速倍率、灵力上限加成、伤害倍率）：凡境 `health=0, speed=1.00, spirit=0, damage=1.00`，具灵 `health=100, speed=1.40, spirit=70, damage=3.00`，其余境界为 10/15/25/40/55/70/80 生命、1.05~1.35 移速、5/10/15/20/30/40/50 灵力、1.25~2.75 伤害，lj_realm_defs.lua:19-29；由 `RealmValue:ApplyRealmAttrs` 施加到 health/locomotor/combat/lj_spirit_value，lj_realm_value.lua:67-95。
- 每阶经验门槛表（凡境一阶 50 … 具灵九阶 124500），lj_realm_defs.lua:8-18；瓶颈阶的门槛为「下一阶起点 - 1」，lj_realm_defs.lua:54-59。
- 击杀经验 = 目标基础最大生命 × 0.05（`realm_exp_rate` 可配置），lj_realm_value.lua:131-133、tuning.lua:6。
- 不给经验的对象：玩家、companion、wall、影分身，以及被玩家跟随的生物，realm_combat.lua:10-18；死亡事件会从 `data.afflicter` 补记最后一击，realm_combat.lua:36-41；同一目标只结算一次（`_lj_exp_rewarded`），realm_combat.lua:37-44。
- 打坐收益：每 3 秒 +1 精神、+1 灵力；每 10 秒 +1 经验，lj_realm_value.lua:194-211；打坐期间饥饿消耗置 0（`hunger.burnratemodifiers:SetModifier(inst, 0, "lj_meditation")`），lj_realm_value.lua:175-177、254-256。
- 打坐的客观校验：必须坐在悟道台（`sittable:IsOccupiedBy`）、状态机处于 `lj_meditate`、且 `GetDistanceSqToInst(chair) <= 9`，否则结算中断，lj_realm_value.lua:154-160、194-198。
- 大境界突破时经验重置为下一阶起点、并消耗（`RemoveDebuff`）所服丹药，lj_realm_value.lua:229-238。
- `DropOneMajor`：连续掉满 9 小阶（一次掉一个大境界），用于残骸祭坛修复的代价，lj_realm_value.lua:275-290、lj_remains_altar.lua:24。
- 达到最高境界（major 8 minor 9）后经验封顶，`GetNextRealm` 无后继，lj_realm_defs.lua:46-52、lj_realm_value.lua:100-105。
- 灵力枯竭时若在骑乘，坐骑也会收到 `ridersleep`；被冻结/定身/石化时只计时不施加昏睡，lj_spirit_value.lua:76-96。
- 死亡清除枯竭计时、复活时若灵力 < 5 重新施加，lj_spirit_value.lua:13-18。
- 复灵丹：持续 1 天、每 2 秒 +1 灵力，lj_debuffs.lua:643-661。
- 灵力上限随境界从 50 涨到 120（文档只写了 120 这个天花板），lj_spirit_value.lua:42-47、lj_realm_defs.lua:19-29。

**武器**

- 灵韵箭弹参数：速度 25（大箭 30）、`projectile:SetRange(16)`（大箭 20）、`SetHitDist(1.5)`、`SetLaunchOffset(Vector3(1.5,1.5,1.5))`，lj_reiki_bow.lua:352-357；普通箭暴击时位面伤害同样 ×1.8，lj_reiki_bow.lua:105-108；大箭固定 300 伤害、不吃暴击、不附带位面伤害（`GetArrowDamage` 大箭分支直接 return 300），lj_reiki_bow.lua:99-101；大箭命中额外直接冻结 3 秒，lj_reiki_bow.lua:86-88；冰蚀减益结束时会清空未触发冻结的层数，lj_debuffs.lua:691-694。
- 灵韵装备时另设 `inst.controller_use_attack_distance = 10` 与手柄锁定目标的开关，lj_reiki_bow.lua:258-259。
- 星陨暴击时位面伤害也 ×2，lj_star_sword.lua:161-162；充能手持有 4 段动画（`sword_charge1`~`4`，按 charge/25 取档），lj_star_sword.lua:51-64、548-550。
- 星陨耐久耗尽时只执行 `ClearStarState`（清空充能与增伤，物品保留），lj_star_sword.lua:425-428、67-74。
- 陨火刺：冲刺距离固定 6.5，lj_star_sword.lua:173-190；侧向范围 1，lj_star_sword.lua:446；冲刺命中的目标同样会被挂上焚灼，lj_star_sword.lua:286-289；冲刺后 6 帧才交还原有免疫状态，lj_star_sword.lua:280-284。
- 淬铁灵剑耐久归零时物品直接消失（`finiteuses:SetOnFinished(inst.Remove)`），lj_ordinary_sword.lua:83；命中时只播放特效，没有额外伤害机制，lj_ordinary_sword.lua:13-22。
- 三把武器的修复动作依赖原版 `finiteusesrepairable` 标签，而该标签由基础游戏在 `current < total` 时自动加回（基础 `scripts/components/finiteuses.lua:1-8`）；mod 里 prefab 调的 `SetFiniteUsesRepairable(false)` 只是清一次标签（基础 `scripts/components/repairable.lua:26-32、71-73`）。

**甲冠**

- 破损（耐久 0）时除了防御归零，还会清空护甲标签 `armor:SetTags({})` 使护甲不再分摊伤害，lj_armour_upgrade.lua:13-21；修复后按原淬炼等级恢复，等级随物品存档（`OnSave/OnLoad`），lj_armour_upgrade.lua:77-88。
- 破损/受损标签：`lj_armour_damaged`、`lj_armour_broken`、以及未满级时的 `lj_armour_upgradeable`，lj_armour_upgrade.lua:20-22。
- 以血修甲是按装备件分别支付血量：每修一件扣 1 点血、修完一件重新检查血线，背包与地上的甲冠不生效，lj_blood_armour.lua:5-11、94-108；脱战剩余时间会存档（读档按相对时间恢复，不会立刻跳过等待），lj_blood_armour.lua:113-125。
- 狂鬃焰赋能防具：分裂火 = 1 级（最大与当前耐久都翻倍），本体 = 2 级（不再翻倍，追加受到普通伤害 ×0.85 即 -15%），满级后拒绝再次赋能，lj_flame_item.lua:7-33、lj_mighty_armour.lua:1、62-66、89-107。

**虚空戒与异火**

- 虚空戒装备时自动打开自己的容器、卸下时关闭（免去手动开合），lj_void_ring.lua:18-20、31-33。
- 异火本体在物品栏中可右键「分裂」出一个消耗品，消耗 10 点灵力，actions.lua:220-255。
- 用虚空戒补燃料一次补 `maxfuel * 0.5`（50% 燃料），actions.lua:274；分裂火作为燃料被消耗时同样补 50%，lj_flame.lua:247-252。
- 异火本体放在普通容器或玩家物品栏中时，每 10 秒随机焚毁其中 1 个可焚物品（叠堆只烧 1 个），lj_flame.lua:96-176；虚空戒、灵虚葫（本体与跟随）、炼丹炉、灵虚光盏属于安全容器，不放火，lj_flame.lua:13-20、113-127。
- 异火本体落地时点亮半径 20 的光源（`inst.Light:SetRadius(20)`、`BODY_LIGHT_RADIUS = 20`），并带 `heater.heat = 80`、发热半径截止 20 的发热组件；同时每秒熄灭 20 范围内的普通火焰与焖烧，lj_flame.lua:186-201、254、272-276、306-308。

**灵虚葫**

- 8 格只收 `lj_pill` 或 `lj_flame`（丹药也能放），main/ui/containers.lua:37-39。
- 每吸收 1 枚异火，会给主人挂 60 秒灼烧：首先点燃主人一次，随后每秒扣 1 点灵力和 2 点生命（`StartFlameBurn(60)` → `BurnTick`），lj_reiki_gourd_proxy.lua:177-183、lj_reiki_gourd.lua:144-198。
- 葫芦本体容器 `canbeopened = false`，只能通过跟随实体打开，且打开被限制为只有主人可用，lj_reiki_gourd.lua:64-66、124-129；跟随实体的 `Open` 与回收都由 `IsOwner` 判定，lj_reiki_gourd_proxy.lua:125-139。
- 回收或掉地时先把 8 格内容物搬回本体容器，装不下就落地；部署状态与剩余燃烧时间会存档并在入包/读档后恢复，lj_reiki_gourd.lua:110-141、201-229。
- 跟随实体有独立移动速度（走 4 / 跑 6）、跟随组件、自定义 brain 与状态机，lj_reiki_gourd.lua:132-142。

**魂幡**

- 吸魂半径 12、每 0.3 秒扫描一次，且一轮扫描可同时接管多只影怪（扫描频率不限制数量），lj_soul_banner.lua:383-407、409-418。
- 魔晶是在「收势」动画 `flutter_pst` 播完后才生成，未结算数量会随魂幡一起存档；回收时先转移待结算数量再删除旧实体，lj_soul_banner.lua:73-105、164-175、426-445。
- 入魔影体分身（`_lj_is_shadow_clone` + `lj_can_be_refined`）不需要拉取过程，直接炼化并同样 +1 魔晶，lj_soul_banner.lua:238-250、397-398。
- 未解锁的魂幡带 `lj_soul_banner_locked` 标签，且只有在地上的魂幡能接受异火解锁（背包/容器内 `IsOnGround` 为假），lj_soul_banner.lua:52-57、217-225。
- 鼠标悬停时会按吸魂半径缩放原版虚线圆显示作用范围，lj_soul_banner.lua（prefab）:28-67、123-125。

## 代码里找不到对应实现的文档内容

1. **「灵技」系统**：文档称「可手持使用灵技」「灵煊尘火放入可解锁灵技」。全仓库检索不到「灵技」以及任何等价标识（`lj_skill`、`spiritskill`、skill 解锁逻辑），虚空戒只有容器 + 点火/补燃料两个功能，main/ui/containers.lua:10-15、actions.lua:259-323。
2. **玄冰灌注的「眩晕」**：只有冻结（`freezable:AddColdness` + 碎裂特效），没有任何 stun / grogginess / 眩晕状态的施加，lj_reiki_bow.lua:61-66、86-88。
3. **灵力枯竭「移速降低 90%」**：代码里不存在这个数值或任何移速乘数，实际是原版睡意 4 / 昏沉 2 加 10 秒 KO 效果，lj_spirit_value.lua:62-97。
4. **「1 个魔核碎片填充 100」**：碎片（lj_magic_debris）的 `finiteusesrepairvalue` 是 10，100 是魔核（lj_magic_core）的值，lj_magic_core.lua:39-46。
5. **焚灼「+15」与冰蚀「+30」这两个固定加成数值**：实际都是持续 8 秒、每 0.5 秒结算 16 点的减益，lj_debuffs.lua:663-695。
6. **陨火刺「造成 150 伤害」的基础值**：代码基础值 140（另有 10 点位面伤害），lj_star_sword.lua:149-151、445。
7. **「引气及以上须服特定丹药」**：丹药要求从辟谷境（major 3）就开始了，共 6 种丹药对应 6 个大境界，lj_realm_defs.lua:30-37。
8. **灵虚葫「右键打开/关闭」与「打开状态不会因开别的箱子而自动关闭」**：mod 中跟随葫芦只注册了右键「回收」，没有开合动作，也没有防自动关闭的处理，actions.lua:57-69、main/ui/containers.lua:18-29。
9. **虚空戒「焚烧建筑」的独立实现**：只有对带 `burnable` 组件的目标调用 `Ignite`（判定标签是 `canlight` / `BURNABLE_fueled`），没有针对建筑的专门分支，actions.lua:279-287、313-321。
10. **「小型 / 中型 / 大型」的体型分类**：冰蚀阈值的实际分层依据是 `epic` 标签与 `maxhealth >= 900`，代码里没有按体型判定的字段，lj_reiki_bow.lua:32-42。
11. **「影怪类生物」的类别泛指**：实际只认 4 个固定 prefab（terrorbeak / crawlinghorror / nightmarebeak / crawlingnightmare）加影体分身，lj_soul_banner.lua:1-8、232-236、239-250。
