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
  → `v<version>` のタグと GitHub Release が作られ、ブラウザ別の zip が3つ添付される
- 同じ version のリリースが既にあれば何もしない
- Actions タブの「Release」→「Run workflow」で手動実行もできる
- ローカルで zip だけ作る: `python .github/scripts/build_zip.py` (出力先は `dist/`)

| zip | 提出先 | zip 内の manifest |
|---|---|---|
| `<リポジトリ名>-chrome-v<version>.zip` | Chrome ウェブストア | `background.scripts` と `browser_specific_settings` を削除 |
| `<リポジトリ名>-edge-v<version>.zip` | Microsoft Edge アドオン | 同上 (Edge は `background.scripts` があると受け付けない) |
| `<リポジトリ名>-firefox-v<version>.zip` | Firefox Add-ons (AMO) | `background.service_worker` を削除 |

リリース前に次の検査を行い、失敗したらリリースしない:

- Chrome / Edge 用 zip に他ブラウザ用のキーが残っていないか
- Firefox 用 zip を `web-ext lint --warnings-as-errors` で検査 (AMO 審査と同じ検査。警告も失敗扱い)

### zip に入らないもの

- git に登録していないファイル
- `.` で始まるファイル/フォルダ (`.github`, `.claude`, `.gitignore` など)
- `manifest.json` が参照していない画像 (`icons` / `action.default_icon` で指定した画像は入る)
- `*.md`, `LICENSE*`
- `.releaseignore` に書いたパターン (任意。`manifest.json` と同じフォルダに置き、1行1パターンで書く)

### manifest.json をサブフォルダに置く場合

`.github/workflows/release.yml` の `EXTENSION_DIR: .` をそのフォルダ名 (例: `src`) に変える。

## 3ブラウザ対応のポイント

- リポジトリの `manifest.json` は3ブラウザ共通で書く。ブラウザ別の変換はリリース時に自動で行う
  - `background` に `service_worker` (Chrome / Edge 用) と `scripts` (Firefox 用) を両方書く
  - `browser_specific_settings` は Firefox 用。`gecko_android.strict_min_version` は `data_collection_permissions` に対応した 142.0 以上にする
  - ローカルで Chrome / Edge に読み込むと `background.scripts` の警告が出るが、リリースされる zip では出ない
- API は `chrome.*` を使えば 3 ブラウザとも動く
- background は service worker として動く書き方にする (DOM / `window` を使わない、状態は `chrome.storage` に保存)
- `innerHTML` に変数を代入すると Firefox の検査で警告になる。`textContent` や DOM API で組み立てる

## 動作確認

- Chrome / Edge: 拡張機能ページでデベロッパーモードを有効にし、「パッケージ化されていない拡張機能を読み込む」でこのフォルダを選ぶ
- Firefox: `about:debugging` →「この Firefox」→「一時的なアドオンを読み込む」で `manifest.json` を選ぶ
