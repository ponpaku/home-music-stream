# 今後の開発タスク (GitHub Issues)

以下の4つの機能を Issue として管理するためのドラフトです。

---

## 1. スマホのロック画面操作対応 (Media Session API)
**タイトル:** feat: Implement Media Session API for better mobile experience

**説明:**
スマホのブラウザで再生している際、ロック画面や通知センターから曲の情報を確認したり、再生・一時停止・スキップ操作ができるようにします。

**技術的ポイント:**
- `window.navigator.mediaSession` を利用。
- `metadata` に曲名、アーティスト名、アルバム名、アルバムアートのURLを設定。
- `setActionHandler` で再生、一時停止、前の曲、次の曲のイベントをハンドル。

---

## 2. フォルダ変更の自動検知 (Watchdog)
**タイトル:** feat: Auto-update music library on file system changes

**説明:**
PCのエクスプローラーで直接音楽ファイルを移動・追加・削除した際に、サーバーがそれを検知して自動的に `music_structure.json` を更新するようにします。現在は手動アップロードまたは再起動が必要です。

**技術的ポイント:**
- Pythonライブラリ `watchdog` を導入。
- `MUSIC_DIR` を監視し、変更があった場合に `save_music_structure_to_json()` を呼び出すバックグラウンドスレッドを作成。

---

## 3. 楽曲メタデータ（タグ）の編集機能
**タイトル:** feat: Allow editing song metadata (ID3 tags) from UI

**説明:**
ブラウザのUI上から曲名、アーティスト名、アルバム名を変更できるようにします。変更内容はサーバー上のファイル（MP3/FLAC等）に直接書き込みます。

**技術的ポイント:**
- `mutagen` ライブラリを使用してファイルのタグ情報を更新。
- フロントエンドに編集用のダイアログを追加。
- 編集完了後、ライブラリの再スキャンを実行。

---

## 4. 歌詞表示機能
**タイトル:** feat: Support for displaying lyrics (Embedded/LRC)

**説明:**
音楽ファイルに埋め込まれている歌詞、または同一フォルダにある `.lrc` ファイルを読み込んで画面に表示します。

**技術的ポイント:**
- `mutagen` で `USLT` (Unsynchronized Lyrics) フレームを読み取るエンドポイントを追加。
- `.lrc` ファイルがある場合は、タイムスタンプに合わせて歌詞をハイライト表示するフロントエンド実装。
