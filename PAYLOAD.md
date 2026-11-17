# CoreSetup — AxiomBox bootstrap installer

这是魔改版 TrollStore（AxiomBox）的**独立安装器**。用爱思助手等工具给它
签上你的个人开发者证书、sideload 到 iPhone，打开点 Install，即可用内核漏洞
把 AxiomBox 装进设备，**全程不依赖原版 TrollStore**。

## 前置：拿到 AxiomBox.tar（关键）

安装器内置的是魔改载荷，必须先把 `AxiomBox.tar` 放进来才能编译。这个 tar
由魔改版 TrollStore 项目（`D:\Project\TrollStore`，fork：cduang/TrollStore）
的 GitHub Actions 产出：

1. 打开 `https://github.com/cduang/TrollStore/actions`
2. 进入最新一次成功运行（commit `cdc955d` 或更新的 `mod/stealth-identity`）
3. 在页面底部 **Artifacts** 下载 `AxiomBox-tar`
4. 解压得到 `AxiomBox.tar`，放到本仓库的 `payload/AxiomBox.tar`

或者，编译安装器时用 `workflow_dispatch` 触发，在 `payload_url` 里填这个 tar
的可下载地址，CI 会自动下载。

> tar 内含 `AxiomBox.app`（不是 `TrollStore.app`），以及魔改版
> `axiomboxhelper`、`PersistenceHelper`。安装器代码已经对齐了这些名字和
> `install-axiombox` 命令。

## 编译

`GitHub Actions` 会自动触发（macos-15 + Xcode 16.4）。也可本地 Mac：

```bash
# 放好 payload/AxiomBox.tar 后
python3 apply_axiombox_payload.py   # 装载魔改载荷 + 对齐命令/路径（幂等）
python3 apply_stealth_installer.py  # 去特征（幂等）
chmod +x build.sh && ./build.sh     # 产出 CoreSetup.ipa
```

CI 产物在 Actions 页面的 `CoreSetup-IPA` artifact。

## 安装到设备

1. 用**爱思助手 / Sideloadly / AltStore** 把 `CoreSetup.ipa` 用你的 Apple ID
   签名安装到 iPhone（免费个人证书即可）。
2. 首次打开前：设置 → 通用 → VPN与设备管理 → 信任该证书。
3. iOS 16 需在 设置 → 隐私与安全性 → 开发者模式 → 开启（会重启）。
4. 打开 Core Setup，点 Install。设备为 iPhone 14 Pro / iOS 16.4.1（arm64e），
   会走**直接安装**（kfd + dmaFail）；按提示选一个可移除的系统 App 作为
   持久化助手（如「提示」）。
5. 完成后主屏出现 AxiomBox，respring 后即可用。

## 注意事项

- 安装器是 7 天签名，掉签后 App 打不开，但**已装好的 AxiomBox 不受影响**。
  需要重装安装器时重新签名即可。
- 安装器本身 bundle id 为 `com.axiomdev.coresetup`，显示名 Core Setup，
  无任何 TrollStore/TrollInstallerX 明文标识。
- 自动更新已禁用（魔改载荷内置；避免联网拉回原版）。升级 AxiomBox 请在
  AxiomBox 内安装新版，或重新用新版载荷编译安装器。
- 卸载：装好后安装器就没用了，可直接在设备上删除（不影响 AxiomBox）。

## 两个脚本

- `apply_axiombox_payload.py`：把 AxiomBox.tar 装进 Resources，并对齐
  `install-trollstore` → `install-axiombox`、`TrollStore.app` → `AxiomBox.app`
  等命令/路径。想换载荷放新 tar 重跑即可。
- `apply_stealth_installer.py`：去特征 + 持久化契约对齐（标记文件
  `.AxiomBoxHelper`、备份后缀 `_AXIOMBOX_BACKUP`、roothelper `axiomboxhelper`），
  与魔改版 TrollStore 完全一致。想换身份改脚本顶部变量重跑即可。

两者均幂等，改动已提交进仓库；脚本用于将来重建或换身份。
