import io, re

lines = [l.strip() for l in io.open("aces_all.txt", encoding="utf-8") if l.strip()]
models = [n for n in lines if not n.endswith(("_skeleton","_anim","_animtree","_char","_na","_collision","_dmg"))]

junk_rx = re.compile(r"(drop_tank|tower|hangar|flag_|_flag|chute|ammunition|air_cargo|jato|blu_|decoy|parachute|static|paratrooper|wing_tank|_tank_|prop_|_prop$|engine|pilot|crew|seat|cockpit|runway|ramp|barrier|barrel|crate|container|trailer|tractor|balloon|bomb_cart|base_airfield|bafg|bf109|^aa20$|dummy|empty_mesh|football|fokker|_navale|pd500|fr_100kg|fr_1[0-9]{2}|samp|sneb|matra_t_10|secan|m117|fr_200kg|fr_460l|cone_|halloween|pumpkin|^helper|ice_center|il2serie|_50_kg_gp|ir_fatter|ir_sedjil|ir_yasser|jp_navy|jp_type9|jp_mk82|matra_r5|super_530|^hp_12|jp_type92|jp_type94|menu_cam|objective_|undercarriage|^pl_11|^us_pl_11|^uk_pl_11|^pl_7|^pl_9|python_3|r_darter|ecm_pod|^s_3k|^sc[0-9]|sc1000_c|sc2500|^sd[0-9]|skyfire|spad_|spitfire|ao_25|brab|^su_fab|^su_rs132|^su_rs82|s_25ofm_pod|zab_|zb_360|zb_500|falco|tank_armor_shard|flz_|uk_\d+lb|herfc|herl|2_inch|f53|mc_mk|ap_mk|uk_sraam|uk_hvar|cookie|mk_79|unitaz|an-m|an_m|_cone|_rod|_white|_box_ap|^us_\d+lb_mk|^us_\d+lb_ap|m63|anm\d|an66|m118|m31|anm56|anm64|_in_ar|_in_atar|bazooka|m116|^us_\d+lb_m\d|^us_\d+_in_|tiny_tim|water_|^water)", re.I)
drop_rx = re.compile(r"(torpedo|depth_charge|hedgehog|rbk|mine|tank_bullet|s_13of|incendiary|fire_snake|_inc_|^inc_|_gp_|^gp_|bfa_|ba_fg_|binc_|^de_sc|^de_sd|^de_sb|^de_pc|r4m|^de_210|^de_ld|^de_abc|^de_lt)", re.I)
missile_rx = re.compile(r"(9m\d|9k\d|9p\d|kornet|spike_|hellfire|tow|bastion|refleks|invir|shturm|fagot|metis|milan|malyutka|swingfire|combat_anti_tank|kh_|kab_|agm_|vikhr|maverick|harm|shrike|exocet|harpoon|penguin|as_30|as_20|as20|as30|aspide|kormoran|laser_guided|smart_|guided_bomb|gbu|jdam|pgb|aim_54|su_r_77|su_r_73|pl_12|missile|r_550|magic|mica|fx1400|fritz|hammer|aasm|ruhrstahl|x_4|x4|bgl|spice|hs_293|ki_148|lance|pgm_|rb_05|r_40|upab|paveway|brimstone|skipper|walleye)", re.I)
rocket_rx = re.compile(r"(rocket|s-8|s-13|s-24|s-25|hydra|zuni|ffar|rs-82|rs-132|rp-3|nebel|wgr|srak|psrak|hvar)", re.I)
guided_rx = re.compile(r"(kab_|gbu|jdam|pgb|laser_guided|smart_|guided_bomb|lgb|ls_500|ls_6|gb250|_laser|fx1400|fritz|hammer|aasm|bgl|spice|hs_293|ki_148|pgm_|upab|paveway|brimstone|skipper|walleye)", re.I)
bomb_rx = re.compile(r"(bomb|minb|sb_m\d|\d+kg_|kg_sb|kg_minb|fab_|ofab|betab|bkbr|pbk|an-m|mk_82|mk_83|mk_84|sc-250|sc-500|sd-500)", re.I)
# 残余非弹药：水体材质 / 飞艇等场景物件
FINAL_JUNK = re.compile(r"(winter_|_border_mat|zeppelin|ice_border)", re.I)

# 反坦克导弹（按用户要求整类删除），含 Vikhr / Hellfire / TOW 等
ATGM_DROP = re.compile(r"(9m\d|9k\d|9p\d|kornet|spike_|hellfire|_tow|tow_|bastion|refleks|invir|shturm|fagot|metis|milan|malyutka|swingfire|combat_anti_tank|khrizantema)", re.I)

# 反舰导弹（按用户要求整类删除）
ANTI_SHIP = re.compile(r"(kormoran|exocet|agm_84d|agm_119|penguin|rb_05|yj_83|kh_31a|kh_31ad)", re.I)

AAM_KEEP = {"us_aim_54a","us_aim_54c","pl_12_missile","pl_12a_missile",
            "su_r_77_missile","su_r_77_1_missile","su_r_73","su_r_73l","su_r_40rd","su_r_40td"}
AAM_ALL = re.compile(r"(us_aim_54|us_aim_7|us_aim_9|us_aim_120|rb71_aim_7|uk_skyflash|su_r_24|su_r_27|su_r_60|su_r_73|su_r_77|matra_r550|mbda_mica|pl_5|pl_8|pl_12|shafrir|matra_r5|super_530|pl_11|pl_7|pl_9|r_darter|su_r_40|uk_sraam)", re.I)

kept = []
for m in models:
    if junk_rx.search(m): continue
    if drop_rx.search(m): continue
    if AAM_ALL.search(m) and m not in AAM_KEEP: continue
    if ANTI_SHIP.search(m): continue
    if ATGM_DROP.search(m): continue
    if FINAL_JUNK.search(m): continue
    if missile_rx.search(m): kept.append(m); continue
    if rocket_rx.search(m): continue
    if bomb_rx.search(m) and not guided_rx.search(m): continue
    kept.append(m)

aam = sorted(m for m in kept if AAM_ALL.search(m))
uncat = [m for m in kept if not re.search(r"(aim_54|su_r_77|su_r_73|pl_12|kh_|kab_|9m127|vikhr|agm_|maverick|harm|shrike|exocet|harpoon|penguin|as_30|as_20|as20|as30|aspide|kormoran|laser_guided|smart_|guided_bomb|9m\d|9k\d|9p\d|kornet|spike_|hellfire|tow|bastion|refleks|invir|shturm|fagot|metis|milan|malyutka|swingfire|gbu|jdam|pgb|missile|r_550|magic|mica|lgb|ls_500|ls_6|gb250|fx1400|fritz|hammer|aasm|ruhrstahl|x_4|bgl|spice|hs_293|ki_148|lance|pgm_|rb_05|r_40|upab|paveway|brimstone|skipper|walleye)", m, re.I)]
print("final:", len(kept), "| uncat:", len(uncat), uncat[:6])

cats = {
 "空空导弹 AAM": r"(us_aim_54|su_r_77|su_r_73|pl_12|su_r_40)",
 "空地导弹 / 反舰 ASM": r"(kh_|kab_|9m127|vikhr|agm_|maverick|harm|shrike|exocet|harpoon|penguin|as_30|as_20|as20|as30|aspide|kormoran|laser_guided|smart_|guided_bomb|rb_05|brimstone|skipper|walleye)",
 "反坦克导弹 ATGM": r"(9m\d|9k\d|9p\d|kornet|spike_|hellfire|tow|bastion|refleks|invir|shturm|fagot|metis|milan|malyutka|swingfire|combat_anti_tank)",
 "制导炸弹 Guided Bomb": r"(kab_|gbu|jdam|pgb|lgb|ls_500|ls_6|gb250|fx1400|fritz|hammer|aasm|bgl|spice|hs_293|ki_148|pgm_|upab|paveway|brimstone|skipper|walleye)",
 "弹道导弹 / 其他 Ballistic & Other": r"(lance|missile|r_550|mica|magic|ruhrstahl|x_4)",
}
result = {}
for c, pat in cats.items():
    result[c] = sorted({m for m in kept if re.search(pat, m, re.I)})

out = ["# 战争雷霆弹药模型清单（aces.grp · 已过滤）", "",
 "过滤规则：", "- 删除：鱼雷 / 深弹 / 水雷 / 坦克炮弹 / 全部火箭弹与火箭巢 / 燃烧弹 / 二战铁炸弹 / 集束铁炸弹 / FAB 铁炸弹",
 "- 航空炸弹：仅保留制导型（KAB / GBU / JDAM / PGM / 激光 LGB / AASM / BGL / SPICE / FX-1400 / UPAB / Paveway / Walleye / Skipper / Brimstone）",
 "- 删除：副油箱 / 机库 / 塔台 / 旗帜 / 伞具 / 弹药箱 / JATO / 飞机静态件 / 机场建筑 / 任务假目标 / 镜头 / 节日道具 / ECM 吊舱 / 水体",
 "- 空空导弹：AIM-54A/C + PL-12 / R-77 / R-73 + R-40RD/TD（>350 kg）", "",
 "原始 1,391 → 过滤后 %d" % len(kept), "", "## 分类统计", "", "| 分类 | 数量 |", "| --- | --- |"]
for c, v in result.items():
    out.append("| %s | %d |" % (c, len(v)))
if uncat:
    out.append("| 其他（未归类） | %d |" % len(uncat))
out += ["", "## 空空导弹（10 条）", ""] + ["- `%s`" % n for n in aam] + ["", "## 各类明细", ""]
for c, v in result.items():
    out += ["", "### %s（%d）" % (c, len(v)), ""] + ["- `%s`" % n for n in v[:60]]
    if len(v) > 60:
        out.append("- … 另有 %d 条，见 `弹药模型清单_full.txt`" % (len(v) - 60))
io.open("弹药模型清单.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
io.open("弹药模型清单_full.txt", "w", encoding="utf-8").write("\n".join(sorted(kept)) + "\n")
for c, v in result.items():
    print("  %s: %d" % (c, len(v)))
