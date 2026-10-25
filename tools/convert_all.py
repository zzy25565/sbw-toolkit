"""Batch: OBJ -> bedrock geo for all 21 ammo + 3 vehicles, DDS -> PNG, review report."""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obj_to_bedrock import convert, parse_obj
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
FRESH = os.path.join(BASE, "models_fresh")
OUT = os.path.join(BASE, "converted")

report = []


def dds_to_png(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    Image.open(src).save(dst)


def bbox_of(obj_path):
    verts, _, _, _ = parse_obj(obj_path)
    xs = [v[0] for v in verts] or [0]
    ys = [v[1] for v in verts] or [0]
    zs = [v[2] for v in verts] or [0]
    return {
        "min": [min(xs), min(ys), min(zs)],
        "max": [max(xs), max(ys), max(zs)],
        "center": [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2],
        "size": [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)],
    }


# ---------- ammo ----------
ammo_dir = os.path.join(FRESH, "ammo_pack")
for fn in sorted(os.listdir(ammo_dir)):
    if not fn.endswith(".obj"):
        continue
    name = fn[:-4]
    obj = os.path.join(ammo_dir, fn)
    geo = os.path.join(OUT, "ammo", name + ".geo.json")
    faces = convert(obj, geo, "geometry.sbw_vls." + name, rotate=False, scale=1.305)
    report.append({"type": "ammo", "id": name, "faces": faces, "geo": geo, "png": "无（弹药未导贴图）"})

# ---------- vehicles ----------
for veh in ["iris_slm", "iris_slm_fcs", "t_80u"]:
    d = os.path.join(FRESH, veh)
    obj = os.path.join(d, veh + "_0.obj")
    if not os.path.exists(obj):
        continue
    geo = os.path.join(OUT, "vehicles", veh, veh + ".geo.json")
    faces = convert(obj, geo, "geometry.sbw_vls." + veh, rotate=True, scale=1.1919)
    bb = bbox_of(obj)
    report.append({"type": "vehicle", "id": veh, "faces": faces, "geo": geo, "bbox": bb})

    # textures
    tex_dir = os.path.join(d, "textures")
    pngs = []
    if os.path.isdir(tex_dir):
        for fn in sorted(os.listdir(tex_dir)):
            if fn.endswith("_c.dds"):
                src = os.path.join(tex_dir, fn)
                dst = os.path.join(OUT, "vehicles", veh, "textures", fn[:-4] + ".png")
                try:
                    dds_to_png(src, dst)
                    pngs.append(os.path.basename(dst))
                except Exception as ex:
                    print("  PNG 转换失败:", fn, ex)
    report[-1]["png"] = pngs

# ---------- review ----------
lines = ["# 转换审查报告", "",
         "| 模型 | 类型 | 面数（=poly 数） | 部件 | 贴图 |",
         "| --- | --- | --- | --- | --- |"]
for r in report:
    tex = r.get("png")
    tex_txt = f"{len(tex)} 张 PNG" if isinstance(tex, list) else str(tex)
    lines.append(f"| {r['id']} | {r['type']} | {r['faces']} | - | {tex_txt} |")
io.open(os.path.join(OUT, "REVIEW.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
json.dump(report, io.open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n完成，报告见 converted/REVIEW.md")
