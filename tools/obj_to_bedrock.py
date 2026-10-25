"""OBJ (War Thunder export) -> bedrock 1.12 geo.json for the sbw_vls pack.

Mirrors the pack's buk_visual_missile:
  geometry.description {identifier, texture_width/height, visible_bounds_*}
  bones: root -> base -> <group>_mat0
  poly_mesh: normalized_uvs=true, per-corner positions/normals/uvs, polys of index triplets

No decimation: one OBJ triangle -> exactly one poly, so the face count is provable.
"""
import io
import json
import math
import os
import sys


def parse_obj(path):
    verts, uvs, norms = [], [], []
    groups = {}
    cur = "root"
    with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("vt "):
                p = line.split()
                uvs.append((float(p[1]), float(p[2])))
            elif line.startswith("vn "):
                p = line.split()
                norms.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("g "):
                cur = line[2:].strip() or "root"
                groups.setdefault(cur, [])
            elif line.startswith("f "):
                face = []
                for tok in line.split()[1:]:
                    a = tok.split("/")
                    vi = int(a[0])
                    ti = int(a[1]) if len(a) > 1 and a[1] else 0
                    ni = int(a[2]) if len(a) > 2 and a[2] else 0
                    face.append((vi - 1, ti - 1, ni - 1))
                if len(face) == 3:
                    groups.setdefault(cur, []).append(face)
    return verts, uvs, norms, groups


def wrap01(x):
    x = x % 1.0
    if abs(x) < 1e-7:
        x = 0.0
    return round(x, 6)


def rot_y(x, y, z):
    """+90 deg about Y: length moves from +X to +Z (pack convention)."""
    return (-z, y, x)


def convert(obj_path, out_path, identifier, rotate=True, scale=1.0):
    verts, uvs, norms, groups = parse_obj(obj_path)
    all_faces = sum(len(v) for v in groups.values())

    tv = [rot_y(*v) if rotate else v for v in verts]
    tv = [(v[0] * scale, v[1] * scale, v[2] * scale) for v in tv]
    xs = [v[0] for v in tv] or [0]
    ys = [v[1] for v in tv] or [0]
    zs = [v[2] for v in tv] or [0]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    cz = (min(zs) + max(zs)) / 2.0
    width = max(max(xs) - min(xs), max(zs) - min(zs))
    height = max(ys) - min(ys)

    bones = [
        {"name": "root", "pivot": [0, 0, 0]},
        {"name": "base", "parent": "root", "pivot": [0, 0, 0]},
    ]

    for gname, faces in groups.items():
        if not faces:
            continue
        positions, normals, uvs_out, polys = [], [], [], []
        for face in faces:
            tri = []
            for vi, ti, ni in face:
                idx = len(positions)
                p = verts[vi] if 0 <= vi < len(verts) else (0.0, 0.0, 0.0)
                if rotate:
                    p = rot_y(p[0], p[1], p[2])
                positions.append([round(p[0] * scale, 5), round(p[1] * scale, 5), round(p[2] * scale, 5)])
                n = norms[ni] if 0 <= ni < len(norms) else (0.0, 1.0, 0.0)
                if rotate:
                    n = rot_y(n[0], n[1], n[2])
                ln = math.sqrt(sum(c * c for c in n)) or 1.0
                normals.append([round(n[0] / ln, 5), round(n[1] / ln, 5), round(n[2] / ln, 5)])
                t = uvs[ti] if 0 <= ti < len(uvs) else (0.0, 0.0)
                uvs_out.append([wrap01(t[0]), wrap01(t[1])])
                tri.append([idx, idx, idx])
            polys.append(tri)
        bones.append({
            "name": f"{gname}_mat0",
            "parent": "base",
            "pivot": [0, 0, 0],
            "poly_mesh": {
                "normalized_uvs": True,
                "positions": positions,
                "normals": normals,
                "uvs": uvs_out,
                "polys": polys,
            },
        })

    doc = {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": identifier,
                "texture_width": 1,
                "texture_height": 1,
                "visible_bounds_width": round(width, 4),
                "visible_bounds_height": round(height, 4),
                "visible_bounds_offset": [round(cx, 4), round(cy, 4), round(cz, 4)],
            },
            "bones": bones,
        }],
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8") as w:
        json.dump(doc, w, ensure_ascii=False, separators=(",", ":"))

    # 自校验：面数必须一一对应
    assert sum(len(b.get("poly_mesh", {}).get("polys", [])) for b in bones) == all_faces, "face count mismatch"
    print(f"  {os.path.basename(out_path)}: {all_faces} 面 / {len(bones) - 2} 部件 / {round(os.path.getsize(out_path) / 1048576, 2)} MB")
    return all_faces


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2], sys.argv[3])
