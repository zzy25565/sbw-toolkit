"""Deep validation of the generated bedrock geo files (structure, indices, UV, bbox)."""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "converted")

sys.path.insert(0, BASE)
from obj_to_bedrock import parse_obj


def check(geo_path, obj_path=None):
    issues = []
    with io.open(geo_path, encoding="utf-8") as f:
        doc = json.load(f)

    assert doc["format_version"] == "1.12.0", "format_version"
    g = doc["minecraft:geometry"][0]
    desc = g["description"]
    bones = g["bones"]
    names = [b["name"] for b in bones]
    if names[0] != "root" or names[1] != "base":
        issues.append("root/base 结构不对")

    total_faces = 0
    bbox_min = [float("inf")] * 3
    bbox_max = [float("-inf")] * 3
    for b in bones:
        pm = b.get("poly_mesh")
        if not pm:
            continue
        if not pm.get("normalized_uvs"):
            issues.append(f"{b['name']}: normalized_uvs 非 true")
        pos, nor, uv, polys = pm["positions"], pm["normals"], pm["uvs"], pm["polys"]
        if not (len(pos) == len(nor) == len(uv)):
            issues.append(f"{b['name']}: 位置/法线/UV 数量不一致")
        total_faces += len(polys)
        for tri in polys:
            if len(tri) != 3:
                issues.append(f"{b['name']}: 非三角面")
                break
            for idx in tri:
                if len(idx) != 3:
                    issues.append(f"{b['name']}: 索引三元组长度异常")
                    break
                for v in idx:
                    if not (0 <= v < len(pos)):
                        issues.append(f"{b['name']}: 索引越界 {v}")
                        break
        for p in pos:
            for i in range(3):
                bbox_min[i] = min(bbox_min[i], p[i])
                bbox_max[i] = max(bbox_max[i], p[i])
        for t in uv:
            if not (0.0 <= t[0] <= 1.0 and 0.0 <= t[1] <= 1.0):
                issues.append(f"{b['name']}: UV 超出 [0,1]")
                break

    # visible_bounds 与实际几何一致性
    width = max(bbox_max[0] - bbox_min[0], bbox_max[2] - bbox_min[2])
    height = bbox_max[1] - bbox_min[1]
    if abs(width - desc["visible_bounds_width"]) > 0.01:
        issues.append(f"visible_bounds_width 不一致 {width:.3f} vs {desc['visible_bounds_width']}")
    if abs(height - desc["visible_bounds_height"]) > 0.01:
        issues.append(f"visible_bounds_height 不一致 {height:.3f} vs {desc['visible_bounds_height']}")

    # 与源 OBJ 面数比对（如提供）
    if obj_path and os.path.exists(obj_path):
        _, _, _, groups = parse_obj(obj_path)
        src_faces = sum(len(v) for v in groups.values())
        if src_faces != total_faces:
            issues.append(f"面数不一致 源{src_faces} vs geo{total_faces}")

    return total_faces, issues


rows = []
for root, _, files in os.walk(OUT):
    for fn in files:
        if not fn.endswith(".geo.json"):
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, OUT)
        src = None
        if rel.startswith("ammo"):
            src = os.path.join(BASE, "models_fresh/ammo_pack", fn.replace(".geo.json", ".obj"))
        elif rel.startswith("vehicles"):
            veh = os.path.basename(os.path.dirname(p))
            src = os.path.join(BASE, "models_fresh", veh, veh + "_0.obj")
        faces, issues = check(p, src)
        rows.append((rel, faces, issues, round(os.path.getsize(p) / 1048576, 2)))
        print(f"{rel:44s} {faces:>7} 面 {len(issues):>2} 问题 {rows[-1][3]}MB")
        for i in issues:
            print("    ", i)

bad = [r for r in rows if r[2]]
print(f"\n共 {len(rows)} 个模型，{len(bad)} 个有问题" if bad else f"\n共 {len(rows)} 个模型，全部通过校验")
