#!/usr/bin/env bash
# Build CoreSetup IPA (rebranded TrollInstallerX bootstrap installer).
# 产物可供爱思助手等工具用个人开发者证书重签后 sideload。
set -e

SCHEME="TrollInstallerX"          # 内部 target 名，编译期符号，保持不变
DERIVED="DerivedData/$SCHEME"
APP_NAME="TrollInstallerX"        # .app 产物名由 target 决定
OUT_IPA="CoreSetup.ipa"           # 中性 IPA 文件名

xcodebuild -quiet \
  -configuration Release \
  -derivedDataPath "$DERIVED" \
  -destination 'generic/platform=iOS' \
  -scheme "$SCHEME" \
  CODE_SIGNING_ALLOWED="NO" CODE_SIGNING_REQUIRED="NO" CODE_SIGN_IDENTITY=""

cp Resources/ents.plist "$DERIVED/Build/Products/Release-iphoneos/"
pushd "$DERIVED/Build/Products/Release-iphoneos" >/dev/null
rm -rf Payload "$OUT_IPA"
mkdir Payload
cp -r "$APP_NAME.app" Payload/
# fakesign with ldid; 爱思等工具重签时会覆盖此签名
ldid -Sents.plist "Payload/$APP_NAME.app"
zip -qry "$OUT_IPA" Payload
popd >/dev/null
cp "$DERIVED/Build/Products/Release-iphoneos/$OUT_IPA" .
rm -rf "$DERIVED/Build/Products/Release-iphoneos/Payload"

echo "Built: $OUT_IPA"
# 本地构建时在 Finder 中显示；CI 环境无 GUI，跳过
if command -v open >/dev/null 2>&1 && [ -z "${CI:-}" ]; then
  open -R "$OUT_IPA" || true
fi
