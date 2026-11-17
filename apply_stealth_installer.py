#!/usr/bin/env python3
"""TrollInstallerX -> 中性安装器 (代号 CoreSetup) 深度去特征。

在 apply_axiombox_payload.py 之后运行。分两类改动：
  1) 运行时可见标识：bundle id、显示名、UI 文本、日志域、偏好域、URL
  2) 持久化助手契约：标记文件/备份后缀/roothelper 名 —— 必须与魔改版
     TrollStore 完全一致，否则间接安装后持久化助手无法被识别（功能性，不是 cosmetic）

刻意保留：Xcode target / scheme / 源文件名 / 目录名 (TrollInstallerX)。
这些只在编译期出现，不进 IPA 运行时特征；改它们会牵连 pbxproj 大量
UUID 引用与 scheme，风险远大于收益。build.sh 会产出中性 IPA 文件名。

命令行:
  python apply_stealth_installer.py --check
  python apply_stealth_installer.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CHECK = "--check" in sys.argv

# 新身份
BUNDLE = "com.axiomdev.coresetup"          # 运行时 bundle id
DISPLAY = "Core Setup"                      # 显示名
DOMAIN = "com.axiomdev.coresetup"           # NSError domain / 偏好域

# 映射按 key 长度降序执行，避免子串互相覆盖。
# 注意：目录名 "TrollInstallerX/" 出现在 pbxproj 的路径里，不能全局替换
# （会破坏 HEADER_SEARCH_PATHS / BRIDGING_HEADER 等真实路径），故 pbxproj 单独精确处理。
MAPPING = {
    # --- 持久化助手契约（与魔改版 TrollStore 对齐，功能性）---
    ".TrollStorePersistenceHelper": ".AxiomBoxHelper",
    "TROLLSTORE_BACKUP":            "AXIOMBOX_BACKUP",
    "TROLLTROLL":                   "AXIOMBOX",
    '@"trollstorehelper"':          '@"axiomboxhelper"',
    "Documents/trollstorehelper":   "Documents/axiomboxhelper",
    "Documents/.TrollStorePersistenceHelper": "Documents/.AxiomBoxHelper",

    # --- 标识 / 域 / 偏好 ---
    "com.Alfie.TrollInstallerX": DOMAIN,
    "TROLLTROLL.com.Alfie.TrollInstallerX": "AXIOM" + DOMAIN,

    # --- 下载源（指向无效地址，防止装回原版；魔改载荷已内置）---
    "https://github.com/opa334/TrollStore/releases/latest/download/TrollStore.tar":
        "https://invalid.local/axiombox/no-auto-update.tar",
    # 注释里的 API 地址
    "https://api.github.com/repos/opa334/TrollStore/releases/latest":
        "https://api.github.com/repos/axiomdev/axiombox/releases/latest",
    # 自动更新检查的仓库定位符：指向不存在的仓库 -> 永远判定“无新版本”，
    # 从而禁用联网更新（魔改载荷内置，无需更新；避免拉到原版或报错）。
    'github_fetchLatestVersion("opa334/TrollStore"':
        'github_fetchLatestVersion("axiomdev/axiombox-nonexistent"',
    # 残留注释
    "and trollstorehelper": "and axiomboxhelper",
    'Credit(name: "opa334", link: URL(string: "https://x.com/opa334dev")!),\n    ':
        "",

    # --- UI 可见文本 / 日志 ---
    'Text("TrollInstallerX")':                 f'Text("{DISPLAY}")',
    "TrollInstallerX uses the 100% reliable": f"{DISPLAY} uses the 100% reliable",
    # install_trollstore 函数名是 C 符号（跨文件调用），但仅在 installer 内部，
    # strip 后不构成运行时明文特征；改名需同步 .h/.m/.swift，收益低，保留。
}

# 精确处理 pbxproj：只改两个运行时键，不动 target/scheme/路径
PBXJ_EXACT = {
    "INFOPLIST_KEY_CFBundleDisplayName = TrollInstallerX;":
        f'INFOPLIST_KEY_CFBundleDisplayName = "{DISPLAY}";',
    "PRODUCT_BUNDLE_IDENTIFIER = com.Alfie.TrollInstallerX;":
        f"PRODUCT_BUNDLE_IDENTIFIER = {BUNDLE};",
}

EXT_TARGETS = (".swift", ".m", ".h", ".plist", ".sh", ".pbxproj", ".xcscheme")
SKIP_PREFIXES = (".git/", "DerivedData/", "payload/")


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT).replace("\\", "/")
        dirnames[:] = [d for d in dirnames
                       if not rel_dir.startswith(("DerivedData", "payload"))
                       and d not in (".git", "DerivedData", "payload")]
        for fn in filenames:
            if not fn.endswith(EXT_TARGETS):
                continue
            rel = (rel_dir + "/" + fn) if rel_dir != "." else fn
            if rel.startswith(SKIP_PREFIXES):
                continue
            yield rel


def replace_sorted(text, mapping):
    n = 0
    for old in sorted(mapping, key=len, reverse=True):
        c = text.count(old)
        if c:
            text = text.replace(old, mapping[old])
            n += c
    return text, n


def apply_file(rel):
    path = os.path.join(ROOT, rel)
    with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
        text = f.read()
    new, n = replace_sorted(text, MAPPING)
    # pbxproj 精确替换（覆盖上面的全局结果里的路径保护）
    if rel.endswith("project.pbxproj"):
        for old, repl in PBXJ_EXACT.items():
            c = new.count(old)
            new = new.replace(old, repl)
            n += c
    if n and not CHECK:
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(new)
    return n


def main():
    print("=== 深度去特征：运行时标识 + 持久化契约 ===")
    total = 0
    hits = []
    for rel in iter_files():
        n = apply_file(rel)
        if n:
            hits.append((n, rel))
            total += n
    for n, rel in sorted(hits, reverse=True):
        print(f"  {n:3d}  {rel}")
    print(f"  合计 {total} 处{'（check 未写入）' if CHECK else ''}")
    print("\n=== 保留项说明 ===")
    print("  - target/scheme/源目录名 TrollInstallerX：编译期符号，不进运行时特征")
    print("  - build.sh：改中性 IPA 文件名，但 -scheme 仍用原 target 名（编译必需）")


if __name__ == "__main__":
    main()
