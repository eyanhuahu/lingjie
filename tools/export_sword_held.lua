-- 导出「淬铁灵剑」的手持外观，给网站鼠标光标用（图再经 tools/make_sword_cursor.py 处理）。
--
-- 为什么是 BUILD 这个动画：
--   这个包的 bank/build 都是 lj_ordinary_sword，里面有两个符号——
--     lj_ordinary_sword_1  → idle 动画用的，是物品栏/地面上那一版（剑柄朝上、剑刃朝下）
--     lj_ordinary_sword    → BUILD / BUILD_000 动画用的，就是装备后握在手上的那一版（剑尖朝上）
--   装备时游戏执行的是 OverrideSymbol("swap_object", "lj_ordinary_sword", "lj_ordinary_sword")
--   （见 lj_mod/scripts/prefabs/equipment/lj_ordinary_sword.lua:30），所以「手持图」= BUILD 帧。
--
-- 用法（必须走 run_dst_app.ps1，它会强制断网并收尾清进程）：
--   .\tools\run_dst_app.ps1 -LuaFile tools\export_sword_held.lua
--   python tools\make_sword_cursor.py
local ANIMS = [[D:\Users\huan\Documents\GitHub\lj_mod\anim\]]
local OUT   = [[D:\Users\huan\Documents\GitHub\lingjie\.work\]]
local paths = { ANIMS .. "lj_ordinary_sword.zip" }

local imported = doc:import_resources(paths)
print(string.format("IMPORTED builds=%d banks=%d", #imported.builds, #imported.banks))

local bank = doc.banks:find("lj_ordinary_sword")
local build = doc.builds:find("lj_ordinary_sword")
if bank == nil or build == nil then print("MISS bank/build lj_ordinary_sword") return end

local anim = bank.animations:find("BUILD")
if anim == nil then print("MISS anim BUILD") return end

for _, e in ipairs(anim.frames[1].elements) do
    print(string.format("frame1 elem sym=%s layer=%s", tostring(e.symbol), tostring(e.layer)))
end

local opts = { max_dimension = 512, builds = { build } }
anim.frames[1]:export_png(OUT .. "sword_build.png", opts)
print("EXPORTED " .. OUT .. "sword_build.png")
