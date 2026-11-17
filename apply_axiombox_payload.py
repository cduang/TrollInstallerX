#!/usr/bin/env python3
"""TrollInstallerX -> AxiomBox 安装器：载荷 + 命令 + 路径对齐。

把安装器内置的 TrollStore.tar / trollstorehelper / install-trollstore 命令
全部切换到魔改版 AxiomBox 对应物。功能层改动，先于去特征脚本运行。

命令行:
  python apply_axiombox_payload.py --check   # 只检查，不修改
  python apply_axiombox_payload.py           # 应用

前置条件:
  魔改版 AxiomBox.tar 需放在 payload/AxiomBox.tar（由 TrollStore 项目 CI 产出）。
  脚本会把它复制为 TrollInstallerX/Resources/TrollStore.tar —— 保留原文件名
  是为了不动 pbxproj 的资源引用（Bundle.main.url(forResource:"TrollStore")），
  但内容已经是 AxiomBox.app。路径/命令名由下面的映射负责对齐。
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CHECK = "--check" in sys.argv

# 文件名不变（TrollStore.tar / TrollStore.app 目录名保留在 tar 内部），
# 但代码里所有指向内置载荷的“路径片段 / 命令名”要切到魔改版。
# 注意：魔改版 tar 内部是 AxiomBox.app（由 TrollStore 的 assemble_axiombox 产出），
# 因此解压后的 .app 目录名与 helper 名都要改成 AxiomBox 版本。
MAPPING = [
    # --- 命令名：魔改版 roothelper 只认 install-axiombox ---
    ('@"install-trollstore"', '@"install-axiombox"'),

    # --- 解压后的 app 目录名（tar 内是 AxiomBox.app）---
    ('/TrollStore.app/trollstorehelper', '/AxiomBox.app/axiomboxhelper'),
    ('TrollStore.app").appendingPathComponent("trollstorehelper"',
     'AxiomBox.app").appendingPathComponent("axiomboxhelper"'),
    ('TrollStore.app").appendingPathComponent("PersistenceHelper"',
     'AxiomBox.app").appendingPathComponent("PersistenceHelper"'),
    ('/private/preboot/tmp/TrollStore/TrollStore.app/PersistenceHelper',
     '/private/preboot/tmp/AxiomBox/AxiomBox.app/PersistenceHelper'),

    # --- 临时目录里的 helper 名 ---
    ('/private/preboot/tmp/trollstorehelper', '/private/preboot/tmp/axiomboxhelper'),
    ('docs.appendingPathComponent("trollstorehelper")',
     'docs.appendingPathComponent("axiomboxhelper")'),

    # --- 解压根目录（与魔改版 installAxiomBox 内部路径无关，仅安装器自用）---
    ('/private/preboot/tmp/TrollStore"', '/private/preboot/tmp/AxiomBox"'),
]

# 文本目标文件（只改功能逻辑，UI/标识留给去特征脚本）
TARGETS = [
    "TrollInstallerX/Installer/install.m",
    "TrollInstallerX/Installer/Extract.swift",
    "TrollInstallerX/Installer/Installation.swift",
]

PAYLOAD_SRC = os.path.join(ROOT, "payload", "AxiomBox.tar")
PAYLOAD_DST = os.path.join(ROOT, "TrollInstallerX", "Resources", "TrollStore.tar")


def apply_file(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return 0, f"skip (missing): {rel}"
    with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
        text = f.read()
    new = text
    n = 0
    for old, repl in MAPPING:
        c = new.count(old)
        if c:
            if not CHECK:
                new = new.replace(old, repl)
            n += c
    if n and not CHECK:
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(new)
    return n, rel


def main():
    print("=== [1/2] 代码层：命令 / 路径对齐 ===")
    total = 0
    for rel in TARGETS:
        n, label = apply_file(rel)
        total += n
        print(f"  {n:3d}  {label}")
    print(f"  合计 {total} 处替换{'（check 模式，未写入）' if CHECK else ''}")

    print("\n=== [2/2] 载荷：AxiomBox.tar -> Resources/TrollStore.tar ===")
    if os.path.exists(PAYLOAD_SRC):
        size = os.path.getsize(PAYLOAD_SRC)
        if CHECK:
            print(f"  发现魔改载荷 payload/AxiomBox.tar ({size} bytes)，check 模式未复制")
        else:
            with open(PAYLOAD_SRC, "rb") as src, open(PAYLOAD_DST, "wb") as dst:
                dst.write(src.read())
            print(f"  已复制 payload/AxiomBox.tar ({size} bytes) -> Resources/TrollStore.tar")
    else:
        print("  !! 未找到 payload/AxiomBox.tar")
        print("     TrollInstallerX 目前仍内置原版 TrollStore.tar，装上会是原版巨魔。")
        print("     需先从 TrollStore 项目 CI 下载 AxiomBox.tar 放到 payload/ 后重跑。")


if __name__ == "__main__":
    main()
