-- 单独导出「残骸祭坛」修复完成形态（idle_stage2），给百科详情正文当插图用。
--
-- 为什么不用 extract_mod_showcase.py：
--   那个脚本按 data.json 里的条目批量导出**卡片图**，一个条目一个文件；
--   祭坛的卡片图要保留「破碎残骸」（idle_stage1）的样子，完成体只是正文里的一张插图，
--   所以这里单独导一次，输出到 showcase/lj_remains_altar_complete.png。
--
-- 动画包里的动画：idle_stage1（破碎）、stage1_2（修复过程）、idle_stage2（完整）、idle_stage2_1
--
-- 用法（必须走 run_dst_app.ps1，它会强制断网并收尾清进程）：
--   .\tools\run_dst_app.ps1 -LuaFile tools\export_altar_stage2.lua
local ANIMS = [[D:\Users\huan\Documents\GitHub\lj_mod\anim\]]
local OUT   = [[D:\Users\huan\Documents\GitHub\lingjie\images\lingjie\showcase\]]
local paths = { ANIMS .. "lj_remains_altar.zip" }

local imported = doc:import_resources(paths)
print(string.format("IMPORTED builds=%d banks=%d", #imported.builds, #imported.banks))

local ID   = "lj_remains_altar"
local WANT = "idle_stage2"

local bank = doc.banks:find(ID)
if bank == nil then print("MISS bank " .. ID) return end

local names = {}
for i = 1, #bank.animations do names[#names + 1] = bank.animations[i].name end
print("ANIMS " .. table.concat(names, ","))

local anim = bank.animations:find(WANT)
if anim == nil then print("MISS anim " .. WANT) return end

local build = doc.builds:find(ID)
local frame = anim.frames[1]
print(string.format("FRAME anim=%s frames=%d elements=%d build=%s",
    WANT, #anim.frames, #frame.elements, build ~= nil and build.name or "-"))

local opts = { max_dimension = 512 }
if build ~= nil then
    -- 只允许用自己这套图集渲染，避免 dst-app 跨 build 按名字抢符号（会串图）。
    opts.builds = { build }
    local known = {}
    for _, s in ipairs(build.symbols) do known[string.lower(s.name)] = true end
    local hide = {}
    for _, e in ipairs(frame.elements) do
        if not known[string.lower(tostring(e.symbol))] then hide[tostring(e.layer)] = true end
    end
    local list = {}
    for k in pairs(hide) do list[#list + 1] = k end
    table.sort(list)
    if #list > 0 then opts.hide_layers = list end
    print("HIDE " .. table.concat(list, ","))
end

frame:export_png(OUT .. "lj_remains_altar_complete.png", opts)
print("EXPORTED " .. OUT .. "lj_remains_altar_complete.png")
