# SBW Toolkit

配套工具集：第三方模组 jar 的字节码补丁，以及 War Thunder 模型 → 附属包格式的转换。

## 1. PatchAsh.java — mod jar 内摘除指定载具

用 ASM 从 jar 中移除某个载具的三处注册（实体 / 渲染器 / 创造标签页）并删除其资产，
用于在同一载具存在多个来源时只保留一份。

```bash
javac -cp "asm-9.x.jar;asm-tree-9.x.jar" -d out PatchAsh.java
java -cp "out;asm-9.x.jar;asm-tree-9.x.jar" PatchAsh <原jar> <输出jar>
```

要点：
- 实体注册是 `ldc "id" / invokedynamic / invokestatic / putstatic` 四连，整段删除
- 渲染器经 `invokedynamic` 的 BootstrapMethods 间接引用，指令里看不到类名，只能按实体字段锚定

## 2. tools/ — 模型格式转换

| 脚本 | 作用 |
|---|---|
| `obj_to_bedrock.py` | OBJ → bedrock 1.12 `poly_mesh` 几何，支持 `rotate` / `scale` |
| `convert_all.py` | 批量转换 + DDS→PNG |
| `validate_geo.py` | 结构校验：面数守恒、索引范围、UV 范围、包围盒一致性 |
| `gen_vehicle_data.py` | 由几何生成载具数据 json（OBB 自算） |
| `ammo_filter.py` | 弹药清单白/黑名单过滤（导弹优先于火箭弹规则） |

### 单位与轴向（实测结论）

- `poly_mesh` 的 `positions` 单位 = **方块**（非像素）；`normalized_uvs: true` 时 UV ∈ [0,1]
- 包内载具长轴在 **Z**，故转换时按 `(x,y,z) → (-z,y,x)` 旋转 +90°
- 缩放系数由包内同型车标定：载具 `1.1919`，弹药 `1.305`
