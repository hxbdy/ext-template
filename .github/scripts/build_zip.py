#!/usr/bin/env python3
"""ブラウザ拡張 (Chrome / Edge / Firefox) のリリース用zipを dist/ に作成する。

どのリポジトリでも .github/ をコピーするだけで使える。

リポジトリの manifest.json は3ブラウザ共通で書く (ローカルでどのブラウザにも直接読み込める)。
ストアは他ブラウザ用のキーで警告/拒否することがあるため、zip ごとに manifest を変換する:
- <repo>-chrome-v<version>.zip  : background.scripts と browser_specific_settings を削除
- <repo>-edge-v<version>.zip    : 同上 (Edge のストアは MV3 で background.scripts があると拒否する)
- <repo>-firefox-v<version>.zip : background.service_worker を削除
  ※ Firefox 版は manifest.json に browser_specific_settings がある場合だけ作る
manifest.json が直下にない場合は、環境変数 EXTENSION_DIR か第1引数でフォルダを指定する。

zip に入れないもの:
- git で追跡されていないファイル
- "." で始まるファイル/フォルダ (.claude, .github, .gitignore など)
- manifest.json が参照しない画像 (参照: icons / action.default_icon など)
- *.md, LICENSE*
- 拡張フォルダ直下の .releaseignore に書いた glob (任意。1行1パターン、# はコメント)

使い方:
  python .github/scripts/build_zip.py            # manifest.json がリポジトリ直下
  python .github/scripts/build_zip.py src        # manifest.json が src/ にある
"""
import fnmatch
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico", ".psd"}
ALWAYS_EXCLUDE = ["*.md", "LICENSE*"]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout


def manifest_images(manifest: dict) -> set[str]:
    refs: list[str] = list((manifest.get("icons") or {}).values())
    for key in ("action", "browser_action", "page_action"):
        icon = (manifest.get(key) or {}).get("default_icon")
        if isinstance(icon, str):
            refs.append(icon)
        elif isinstance(icon, dict):
            refs.extend(icon.values())
    return {str(PurePosixPath(r.lstrip("/"))) for r in refs}


def for_chromium(manifest: dict) -> dict:
    """Chrome / Edge 用。Edge のストアは MV3 で background.scripts があると受け付けない。"""
    m = json.loads(json.dumps(manifest))
    m.pop("browser_specific_settings", None)
    bg = m.get("background")
    if isinstance(bg, dict) and "service_worker" in bg:
        bg.pop("scripts", None)
    return m


def for_firefox(manifest: dict) -> dict:
    """Firefox 用。Firefox は background.service_worker に対応していない。"""
    m = json.loads(json.dumps(manifest))
    bg = m.get("background")
    if isinstance(bg, dict) and "scripts" in bg:
        bg.pop("service_worker", None)
    return m


def main() -> None:
    # Windows のコンソールでも日本語メッセージが文字化けしないようにする
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")

    root =Path(git("rev-parse", "--show-toplevel").strip())
    os.chdir(root)

    ext_dir = PurePosixPath(
        (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("EXTENSION_DIR") or ".").replace("\\", "/").strip("/") or "."
    )
    manifest_path = root / ext_dir / "manifest.json"
    if not manifest_path.exists():
        sys.exit(f"{manifest_path.relative_to(root).as_posix()} が見つかりません (EXTENSION_DIR を確認してください)")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    version = manifest["version"]
    keep_images = manifest_images(manifest)

    patterns = list(ALWAYS_EXCLUDE)
    ignore_file = root / ext_dir / ".releaseignore"
    if ignore_file.exists():
        for line in ignore_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line.rstrip("/") + ("/*" if line.endswith("/") else ""))

    # zip内パス (拡張フォルダからの相対) -> リポジトリ内パス
    files: dict[str, str] = {}
    for f in git("-c", "core.quotepath=false", "ls-files", "-z", "--", str(ext_dir)).split("\0"):
        if not f:
            continue
        arc = PurePosixPath(f).relative_to(ext_dir)
        if any(part.startswith(".") for part in arc.parts):
            continue
        if arc.suffix.lower() in IMAGE_EXTS and str(arc) not in keep_images:
            continue
        if any(fnmatch.fnmatch(str(arc), pat) or fnmatch.fnmatch(arc.name, pat) for pat in patterns):
            continue
        files[str(arc)] = f

    missing = sorted(keep_images - set(files))
    if missing:
        sys.exit(f"manifest.json が参照する画像が git に登録されていません: {missing}")

    # zip名はリポジトリ名から付ける (Actions では owner/repo の repo 部分)
    repo = os.environ.get("GITHUB_REPOSITORY", root.name).split("/")[-1]
    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    # dist/ を各リポジトリの .gitignore に書かなくても git に入らないようにする
    (dist / ".gitignore").write_text("*\n", encoding="utf-8")

    targets = {"chrome": for_chromium(manifest), "edge": for_chromium(manifest)}
    if "browser_specific_settings" in manifest:
        targets["firefox"] = for_firefox(manifest)

    zips = []
    for target, target_manifest in targets.items():
        out = dist / f"{repo}-{target}-v{version}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for arc in sorted(files):
                if arc == "manifest.json":
                    z.writestr(arc, json.dumps(target_manifest, ensure_ascii=False, indent=2) + "\n")
                else:
                    z.write(files[arc], arc)

        rel = out.relative_to(root).as_posix()
        zips.append(rel)
        print(f"Created {rel} ({len(files)} files):")
        for arc in sorted(files):
            print(f"  {arc}")

    if gh_out := os.environ.get("GITHUB_OUTPUT"):
        with open(gh_out, "a", encoding="utf-8") as fh:
            fh.write(f"version={version}\nzips={' '.join(zips)}\n")


if __name__ == "__main__":
    main()
