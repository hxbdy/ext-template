# ext-template

Chrome / Edge / Firefox 共通で動くブラウザ拡張 (Manifest V3) のひな形です。
`manifest.json` の version を上げて push すると、GitHub Release にストア提出用の zip が自動で添付されます。

## 使い方

1. GitHub の「Use this template」から新しいリポジトリを作る
2. `manifest.json` を書き換える
   - `name` / `description` / `action.default_title`
   - `browser_specific_settings.gecko.id` (Firefox のアドオン ID。AMO に登録すると変更できない)
   - `content_scripts.matches` (対象サイト)
3. `background.js` / `content.js` / `popup.html` / `popup.js` を実装する
4. この README を拡張の説明に書き換える (README は zip に含まれない)

## リリース

- `manifest.json` の `version` を上げて `main` (または `master`) に push する
  → `v<version>` のタグと GitHub Release が作られ、`<リポジトリ名>-v<version>.zip` が添付される
- 同じ version のリリースが既にあれば何もしない
- Actions タブの「Release」→「Run workflow」で手動実行もできる
- ローカルで zip だけ作る: `python .github/scripts/build_zip.py` (出力先は `dist/`)

zip は Chrome ウェブストア、Microsoft Edge アドオン、Firefox Add-ons (AMO) のどれにもそのまま提出できます。

### zip に入らないもの

- git に登録していないファイル
- `.` で始まるファイル/フォルダ (`.github`, `.claude`, `.gitignore` など)
- `manifest.json` が参照していない画像 (`icons` / `action.default_icon` で指定した画像は入る)
- `*.md`, `LICENSE*`
- `.releaseignore` に書いたパターン (任意。`manifest.json` と同じフォルダに置き、1行1パターンで書く)

### manifest.json をサブフォルダに置く場合

`.github/workflows/release.yml` の `EXTENSION_DIR: .` をそのフォルダ名 (例: `src`) に変える。

## 3ブラウザ対応のポイント

- `background` に `service_worker` (Chrome / Edge 用) と `scripts` (Firefox 用) を両方書く
- `browser_specific_settings.gecko` は Firefox だけが使う。Chrome では警告が出ることがあるが動作に影響はない
- API は `chrome.*` を使えば 3 ブラウザとも動く

## 動作確認

- Chrome / Edge: 拡張機能ページでデベロッパーモードを有効にし、「パッケージ化されていない拡張機能を読み込む」でこのフォルダを選ぶ
- Firefox: `about:debugging` →「この Firefox」→「一時的なアドオンを読み込む」で `manifest.json` を選ぶ
