"""Generate sbw_vls vehicle data json from the converted geo (OBB from real geometry)."""
import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "converted")

# 每台车的定位：武器与行走方式（占位，之后可手调）
PROFILE = {
    "iris_slm": {
        "health": 260,
        "engine": "Wheel",
        "weapons": {"Cannon": None, "DriverAAMissile": "superbwarfare:ru_9m336_missile"},
        "seat_weapons": ["DriverAAMissile"],
        "note": "IRIS-T 发射车：导弹暂用 9M336 占位，需替换为 IRIS-T 弹",
    },
    "iris_slm_fcs": {
        "health": 240,
        "engine": "Wheel",
        "weapons": {},
        "seat_weapons": [],
        "note": "IRIS-T 雷达车（FCS）：无武器，仅雷达",
    },
    "t_80u": {
        "health": 380,
        "engine": "Track",
        "weapons": {"Cannon": "superbwarfare:small_cannon_shell"},
        "seat_weapons": ["Cannon"],
        "note": "T-80U：主炮为占位弹种，需替换为 125mm APFSDS",
    },
}

ENGINE_INFO = {
    "Buoyancy": 0.052, "EnergyCostRate": 96, "WheelRotSpeed": 1.25, "WheelDifferential": 0.5,
    "TrackRotSpeed": 1.9, "TrackDifferential": 0.8, "MaxForwardSpeedRate": 0.82,
    "MaxBackwardSpeedRate": 0.35, "Increment": 0.025, "Decrement": 0.015, "SteeringSpeed": 0.1,
}


def bone_bbox(bone):
    pm = bone.get("poly_mesh")
    if not pm or not pm.get("positions"):
        return None
    mn = [min(p[i] for p in pm["positions"]) for i in range(3)]
    mx = [max(p[i] for p in pm["positions"]) for i in range(3)]
    return mn, mx


def build(veh, geo_path):
    geo = json.load(io.open(geo_path, encoding="utf-8"))["minecraft:geometry"][0]
    bones = geo["bones"]
    prof = PROFILE[veh]

    total = None
    turret = None
    for b in bones:
        bb = bone_bbox(b)
        if bb is None:
            continue
        mn, mx = bb
        total = (mn, mx) if total is None else (
            [min(total[0][i], mn[i]) for i in range(3)],
            [max(total[1][i], mx[i]) for i in range(3)],
        )
        if "turret" in b["name"].lower():
            turret = (mn, mx) if turret is None else (
                [min(turret[0][i], mn[i]) for i in range(3)],
                [max(turret[1][i], mx[i]) for i in range(3)],
            )

    def box(b, part=None):
        mn, mx = b
        size = [round(mx[i] - mn[i], 4) for i in range(3)]
        pos = [round((mx[i] + mn[i]) / 2, 4) for i in range(3)]
        o = {"Size": size, "Position": pos}
        if part:
            o["Part"] = part
            o["Transform"] = part
            o["Rotation"] = part
        return o

    obb = [box(total)]
    if turret:
        obb.append(box(turret, "Turret"))

    weapons = {}
    weapon_keys = prof["seat_weapons"]
    if "Cannon" in weapon_keys:
        weapons["Cannon"] = {
            "Icon": "superbwarfare:textures/overlay/vehicle/weapon/icons/cannon.png",
            "DefaultFireMode": "Semi",
            "AvailableFireModes": "Semi",
            "Projectile": prof["weapons"]["Cannon"],
            "RPM": 8,
            "Velocity": 40,
            "Damage": 120,
            "ExplosionDamage": 20,
            "ExplosionRadius": 2,
            "Magazine": 1,
            "EmptyReloadTime": 120,
            "ShootPos": {"Transform": "Turret", "Positions": [[0, 1.5, 0]], "Directions": ["Barrel"]},
        }
    if "DriverAAMissile" in weapon_keys:
        weapons["DriverAAMissile"] = {
            "AmmoType": "superbwarfare:medium_anti_air_missile",
            "Icon": "superbwarfare:textures/overlay/vehicle/weapon/icons/aam.png",
            "DefaultZoom": 4,
            "DefaultFireMode": "Semi",
            "AvailableFireModes": "Semi",
            "Magazine": 8,
            "EmptyReloadTime": 320,
            "Projectile": prof["weapons"]["DriverAAMissile"],
            "Damage": 100,
            "ExplosionDamage": 170,
            "ExplosionRadius": 4,
            "Velocity": 20,
            "SeekWeaponInfo": {"SeekDirection": "Barrel", "SeekRange": 384, "SeekAngle": 20,
                               "SeekTime": 20, "OnlyLockEntity": True},
            "ShootPos": {"Transform": "Turret", "Positions": [[0, 2.2, 0]], "Directions": ["Barrel"]},
        }

    seat = {
        "HidePassenger": True,
        "CameraPos": {"UseFixedCameraPos": True,
                      "Position": [0.5, (total[1][1] * 0.9), 0],
                      "ZoomPosition": [0.5, (total[1][1] * 0.9), 0],
                      "Direction": "Barrel"},
        "Weapons": weapon_keys,
        "Transform": "Turret" if turret else None,
        "Position": [0, 1.6, 0],
        "CanRotateHead": bool(turret),
        "MinPitch": -5,
        "MaxPitch": 70,
        "HasThermalImaging": True,
    }
    if seat["Transform"] is None:
        seat.pop("Transform")

    data = {
        "ID": f"sbw_vls:{veh}",
        "MaxHealth": prof["health"],
        "MaxEnergy": 5000000,
        "OBB": obb,
        "Seats": [seat],
        "Weapons": weapons,
        "EngineType": prof["engine"],
        "EngineInfo": ENGINE_INFO,
        "TurretPos": [0, 0, 0],
    }

    dst_dir = os.path.join(OUT, "vehicles", veh)
    os.makedirs(dst_dir, exist_ok=True)
    for path in [os.path.join(dst_dir, "data.json"),
                 os.path.join(dst_dir, "assets_copy.json")]:
        json.dump(data, io.open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"  {veh}: OBB {len(obb)} 件 / 武器 {list(weapons)} | {prof['note']}")
    return {"id": veh, "obb": obb, "weapons": list(weapons), "note": prof["note"]}


if __name__ == "__main__":
    rows = []
    for veh in PROFILE:
        geo = os.path.join(OUT, "vehicles", veh, veh + ".geo.json")
        if os.path.exists(geo):
            rows.append(build(veh, geo))
    json.dump(rows, io.open(os.path.join(OUT, "data_report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
