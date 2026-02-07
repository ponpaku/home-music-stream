# app.py

import os
import json
import hashlib
import uuid
import functools
import datetime
import threading
from flask import Flask, send_from_directory, jsonify, url_for, request, session, redirect, render_template, Response
from dotenv import load_dotenv
from mutagen import File as MutagenFile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# .envファイルをロード
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)

# アルバムアートのキャッシュ (メモリ上)
album_art_cache = {}

# スレッドセーフのためのロック
structure_lock = threading.Lock()

# ディレクトリ設定
MUSIC_DIR = os.environ.get('MUSIC_DIR', 'static/music')  # 音楽ファイルが保存されているディレクトリへのパス

# Windowsのパス形式（C:\...）が指定されている場合にLinux形式（/mnt/c/...）に変換を試みる
if os.name == 'posix' and MUSIC_DIR.startswith(('C:\\', 'c:\\')):
    MUSIC_DIR = '/mnt/c/' + MUSIC_DIR[3:].replace('\\', '/')

USERS_DIR = 'users'  # ユーザー情報を保存するディレクトリ
MUSIC_STRUCTURE_FILE = 'music_structure.json'

# ディレクトリが存在しない場合は作成
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# 管理者情報の初期設定
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'pass0000')

# ユーザー管理関数
def init_admin_user():
    """管理者ユーザーの初期設定"""
    admin_file = os.path.join(USERS_DIR, f"{ADMIN_USERNAME}.json")
    
    if not os.path.exists(admin_file):
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha256((ADMIN_PASSWORD + salt).encode()).hexdigest()
        
        admin_data = {
            "username": ADMIN_USERNAME,
            "password_hash": hashed_password,
            "salt": salt,
            "is_admin": True,
            "playlists": {}
        }
        
        with open(admin_file, 'w', encoding='utf-8') as f:
            json.dump(admin_data, f, ensure_ascii=False, indent=2)
        
        print(f"Admin user created: {ADMIN_USERNAME}")

# 認証デコレータ
def login_required(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized", "redirect": "/login"}), 401
        return func(*args, **kwargs)
    return decorated_function

def admin_required(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized", "redirect": "/login"}), 401
        
        user_file = os.path.join(USERS_DIR, f"{session['user_id']}.json")
        if not os.path.exists(user_file):
            return jsonify({"error": "User not found"}), 404
        
        with open(user_file, 'r', encoding='utf-8') as file_handle:  # 変数名を変更
            user_data = json.load(file_handle)
        
        if not user_data.get('is_admin', False):
            return jsonify({"error": "Forbidden", "message": "Admin access required"}), 403
        
        return func(*args, **kwargs)
    return decorated_function

@app.route('/api/auth/status')
def auth_status():
    if 'user_id' not in session:
        return jsonify({"isAuthenticated": False})
    
    user_file = os.path.join(USERS_DIR, f"{session['user_id']}.json")
    is_admin = False
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            is_admin = user_data.get('is_admin', False)
            
    return jsonify({
        "isAuthenticated": True,
        "username": session['user_id'],
        "isAdmin": is_admin
    })

# 認証ルート
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form.to_dict()
        username = data.get('username')
        password = data.get('password')
        
        user_file = os.path.join(USERS_DIR, f"{username}.json")
        
        if not os.path.exists(user_file):
            return jsonify({"error": "Invalid credentials"}), 401
        
        with open(user_file, 'r', encoding='utf-8') as file_handle:  # 変数名を変更
            user_data = json.load(file_handle)
        
        salt = user_data.get('salt', '')
        hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
        
        if user_data.get('password_hash') == hashed_password:
            session['user_id'] = username
            session.permanent = True
            return jsonify({"success": True, "redirect": "/"})
        
        return jsonify({"error": "Invalid credentials"}), 401
    
    # GETリクエストの場合はSPAのエントリーポイントを表示
    return send_from_directory('frontend', 'index.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

# 管理者ルート
@app.route('/admin')
def admin_panel():
    return send_from_directory('frontend', 'index.html')

@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    users = []
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            username = os.path.splitext(filename)[0]
            with open(os.path.join(USERS_DIR, filename), 'r', encoding='utf-8') as file_handle:
                user_data = json.load(file_handle)
                users.append({
                    "username": username,
                    "is_admin": user_data.get('is_admin', False)
                })
    
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    user_file = os.path.join(USERS_DIR, f"{username}.json")
    
    if os.path.exists(user_file):
        return jsonify({"error": "User already exists"}), 409
    
    salt = uuid.uuid4().hex
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    
    user_data = {
        "username": username,
        "password_hash": hashed_password,
        "salt": salt,
        "is_admin": is_admin,
        "playlists": {}
    }
    
    with open(user_file, 'w', encoding='utf-8') as file_handle:
        json.dump(user_data, file_handle, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "username": username})

# 音楽構造をJSONファイルに保存する関数
def save_music_structure_to_json(directory):
    with structure_lock:
        music_structure = {}
        supported_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(supported_extensions):
                    # 相対パスを取得し、バックスラッシュをスラッシュに統一してから分割
                    rel_path = os.path.relpath(root, start=directory)
                    artist_album = rel_path.replace('\\', '/').split('/')
                    
                    if len(artist_album) == 1:  # アーティスト直下に曲がある場合
                        artist = artist_album[0]
                        album = "アルバム不明"
                        if artist not in music_structure:
                            music_structure[artist] = {}
                        if album not in music_structure[artist]:
                            music_structure[artist][album] = []
                        music_structure[artist][album].append(file)
                    elif len(artist_album) == 2:  # アーティスト/アルバムの構造を想定
                        artist, album = artist_album
                        if artist not in music_structure:
                            music_structure[artist] = {}
                        if album not in music_structure[artist]:
                            music_structure[artist][album] = []
                        music_structure[artist][album].append(file)
        
        with open(MUSIC_STRUCTURE_FILE, 'w', encoding='utf-8') as outfile:
            json.dump(music_structure, outfile, ensure_ascii=False)

# フォルダ変更を監視するクラス
class MusicDirHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            # ディレクトリの変更（作成・削除・移動）も構造に影響するため更新
            save_music_structure_to_json(MUSIC_DIR)
            return
        
        # 音楽ファイルの拡張子をチェック
        supported_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')
        if event.src_path.lower().endswith(supported_extensions):
            save_music_structure_to_json(MUSIC_DIR)

def start_watchdog():
    event_handler = MusicDirHandler()
    observer = Observer()
    observer.schedule(event_handler, MUSIC_DIR, recursive=True)
    observer.start()
    print(f"Watching for changes in {MUSIC_DIR}...")

# JSONファイルから楽曲データをロードする関数
def load_music_structure():
    try:
        with open(MUSIC_STRUCTURE_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading music structure: {e}")
        return {}

# 音楽関連のAPI (認証必須)
@app.route('/music_structure')
@login_required
def get_music_structure():
    with open(MUSIC_STRUCTURE_FILE, 'r', encoding='utf-8') as infile:
        music_structure = json.load(infile)
    return jsonify(music_structure)

@app.route('/music/<path:path>')
@login_required
def stream_music(path):
    return send_from_directory(MUSIC_DIR, path)

@app.route('/api/album-art/<path:path>')
@login_required
def get_album_art(path):
    # キャッシュキーとしてパスを使用
    if path in album_art_cache:
        cached_data = album_art_cache[path]
        if cached_data:
            return Response(cached_data['data'], mimetype=cached_data['mime'])
        return jsonify({"error": "No artwork found"}), 404

    full_path = os.path.join(MUSIC_DIR, path)
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found"}), 404

    try:
        audio = MutagenFile(full_path)
        if audio is None:
            album_art_cache[path] = None
            return jsonify({"error": "Unsupported file format"}), 404

        # MP3 (ID3)
        if 'APIC:' in audio:
            artwork = audio['APIC:'].data
            mime = audio['APIC:'].mime
        # FLAC / OGG (Vorbis Comment)
        elif hasattr(audio, 'pictures') and audio.pictures:
            artwork = audio.pictures[0].data
            mime = audio.pictures[0].mime
        # MP4 (iTunes style)
        elif 'covr' in audio:
            artwork = audio['covr'][0]
            # covrはMIMEタイプを保持していない場合があるため推測
            mime = 'image/jpeg' if artwork.startswith(b'\xff\xd8') else 'image/png'
        else:
            album_art_cache[path] = None
            return jsonify({"error": "No artwork found"}), 404

        album_art_cache[path] = {'data': artwork, 'mime': mime}
        return Response(artwork, mimetype=mime)

    except Exception as e:
        print(f"Error extracting album art: {e}")
        return jsonify({"error": "Error extracting artwork"}), 500

@app.route('/get-song-data/<string:song_name>')
@login_required
def get_song_data(song_name):
    music_structure = load_music_structure()  # 楽曲データのロード

    # 楽曲データを検索する処理
    for artist, albums in music_structure.items():
        for album, songs in albums.items():
            if song_name in songs:
                # 曲が見つかった場合の処理
                # 音楽ストリーミング用のパスを生成
                song_path = url_for('stream_music', path=f"{artist}/{album}/{song_name}")
                return jsonify({"artist": artist, "album": album, "songName": song_name, "path": song_path})
    
    return jsonify({"error": "Song not found"}), 404

# プレイリスト関連のAPI (ユーザー別)
@app.route('/save_playlist', methods=['POST'])
@login_required
def save_playlist():
    data = request.json
    playlist_name = data.get('name')
    playlist_items = data.get('items')
    
    if not playlist_name or not playlist_items:
        return jsonify({"error": "Name and items are required"}), 400
    
    user_file = os.path.join(USERS_DIR, f"{session['user_id']}.json")
    
    if not os.path.exists(user_file):
        return jsonify({"error": "User not found"}), 404
    
    with open(user_file, 'r', encoding='utf-8') as file_handle:
        user_data = json.load(file_handle)
    
    if 'playlists' not in user_data:
        user_data['playlists'] = {}
    
    # Safe name generation
    safe_name = "".join([c for c in playlist_name if c.isalpha() or c.isdigit() or c==' ' or c=='_']).rstrip()
    
    user_data['playlists'][safe_name] = {
        "name": playlist_name,
        "items": playlist_items,
        "created_at": datetime.datetime.now().isoformat()
    }
    
    with open(user_file, 'w', encoding='utf-8') as file_handle:
        json.dump(user_data, file_handle, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "name": playlist_name})

@app.route('/playlists')
@login_required
def get_playlists():
    user_file = os.path.join(USERS_DIR, f"{session['user_id']}.json")
    
    if not os.path.exists(user_file):
        return jsonify({"error": "User not found"}), 404
    
    with open(user_file, 'r', encoding='utf-8') as file_handle:
        user_data = json.load(file_handle)
    
    playlists = []
    for playlist_id, playlist in user_data.get('playlists', {}).items():
        playlists.append({
            "id": playlist_id,
            "name": playlist["name"],
            "created_at": playlist.get("created_at", ""),
            "count": len(playlist["items"])
        })
    
    return jsonify(playlists)

@app.route('/playlist/<string:playlist_id>')
@login_required
def get_playlist(playlist_id):
    user_file = os.path.join(USERS_DIR, f"{session['user_id']}.json")
    
    if not os.path.exists(user_file):
        return jsonify({"error": "User not found"}), 404
    
    with open(user_file, 'r', encoding='utf-8') as file_handle:
        user_data = json.load(file_handle)
    
    playlist = user_data.get('playlists', {}).get(playlist_id)
    
    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404
    
    return jsonify(playlist["items"])

@app.route('/delete_playlist/<string:playlist_id>', methods=['DELETE'])
@login_required
def delete_playlist(playlist_id):
    user_file = os.path.join(USERS_DIR, f"{session['user_id']}.json")
    
    if not os.path.exists(user_file):
        return jsonify({"error": "User not found"}), 404
    
    with open(user_file, 'r', encoding='utf-8') as file_handle:
        user_data = json.load(file_handle)
    
    if playlist_id not in user_data.get('playlists', {}):
        return jsonify({"error": "Playlist not found"}), 404
    
    del user_data['playlists'][playlist_id]
    
    with open(user_file, 'w', encoding='utf-8') as file_handle:
        json.dump(user_data, file_handle, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True})

@app.route('/api/edit-metadata', methods=['POST'])
@login_required
@admin_required
def edit_metadata():
    data = request.json
    artist = data.get('artist')
    album = data.get('album')
    song = data.get('song')
    
    new_artist = data.get('newArtist')
    new_album = data.get('newAlbum')
    new_title = data.get('newTitle')
    
    if not all([artist, album, song, new_artist, new_album, new_title]):
        return jsonify({"error": "Missing required fields"}), 400
    
    old_path = os.path.join(MUSIC_DIR, artist, album, song)
    if not os.path.exists(old_path):
        # Try fallback for "アルバム不明" or other edge cases
        # In current save_music_structure_to_json, it might be just Artist/Song or Artist/Album/Song
        if album == "アルバム不明":
             old_path = os.path.join(MUSIC_DIR, artist, song)
        
        if not os.path.exists(old_path):
            return jsonify({"error": f"File not found: {old_path}"}), 404
    
    # Sanitize inputs for path usage
    def sanitize_path_part(part):
        return "".join([c for c in part if c not in '<>:"/\\|?*']).strip()
    
    s_artist = sanitize_path_part(new_artist) or "Unknown Artist"
    s_album = sanitize_path_part(new_album) or "Unknown Album"
    s_title = sanitize_path_part(new_title) or "Unknown Title"
    
    try:
        # 1. Update tags using mutagen
        audio = MutagenFile(old_path)
        if audio is not None:
            # Check for ID3 tags (MP3)
            from mutagen.id3 import ID3, TIT2, TPE1, TALB
            
            if audio.tags is None:
                audio.add_tags()
            
            if isinstance(audio.tags, ID3):
                audio.tags.add(TIT2(encoding=3, text=[new_title]))
                audio.tags.add(TPE1(encoding=3, text=[new_artist]))
                audio.tags.add(TALB(encoding=3, text=[new_album]))
            else:
                # FLAC, Ogg, m4a, etc. usually support dict-like access
                audio['title'] = [new_title]
                audio['artist'] = [new_artist]
                audio['album'] = [new_album]
            
            audio.save()
        
        # 2. Rename/Move file to match new metadata if changed
        # We follow the structure: MUSIC_DIR / Artist / Album / Song
        # Keep original extension
        ext = os.path.splitext(song)[1]
        new_filename = s_title + ext
        
        new_dir = os.path.join(MUSIC_DIR, s_artist, s_album)
        os.makedirs(new_dir, exist_ok=True)
        
        new_path = os.path.join(new_dir, new_filename)
        
        # If the path is actually different, move it
        if os.path.abspath(old_path) != os.path.abspath(new_path):
            # Check if destination already exists
            if os.path.exists(new_path):
                # If only case changed on case-insensitive FS, it might be the same file
                if os.path.abspath(old_path).lower() != os.path.abspath(new_path).lower():
                    return jsonify({"error": "Destination file already exists"}), 409
            
            os.rename(old_path, new_path)
            
            # Clean up old empty directories
            old_album_dir = os.path.dirname(old_path)
            old_artist_dir = os.path.dirname(old_album_dir)
            
            try:
                if not os.listdir(old_album_dir):
                    os.rmdir(old_album_dir)
                if not os.listdir(old_artist_dir):
                    os.rmdir(old_artist_dir)
            except OSError:
                pass # Directory not empty or other error
        
        # 3. Rescan library
        save_music_structure_to_json(MUSIC_DIR)
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"Error editing metadata: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
@login_required
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files part"}), 400
    
    files = request.files.getlist('files')
    uploaded_count = 0
    
    for file in files:
        if file.filename == '':
            continue
        
        # Sanitize and normalize path separators
        filename = file.filename.replace('\\', '/')
        parts = filename.split('/')
        
        # Filter out empty parts and '..'
        parts = [p for p in parts if p and p != '..']
        
        if not parts:
            continue

        # Determine destination path based on depth
        if len(parts) == 1:
            save_path = os.path.join(MUSIC_DIR, "Unknown Artist", "Unknown Album", parts[0])
        elif len(parts) == 2:
            save_path = os.path.join(MUSIC_DIR, "Unknown Artist", parts[0], parts[1])
        elif len(parts) >= 3:
            # Use the last 3 parts to ensure Artist/Album/Song structure
            relevant_parts = parts[-3:]
            save_path = os.path.join(MUSIC_DIR, *relevant_parts)
        else:
             continue
        
        # Ensure the file is an audio file
        if not save_path.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.flac')):
             continue

        # Create directories
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save file
        file.save(save_path)
        uploaded_count += 1
        
    # Update music structure
    save_music_structure_to_json(MUSIC_DIR)
    
    return jsonify({"success": True, "count": uploaded_count})

# メインルート (ログイン必須)
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return send_from_directory('frontend', 'index.html')

if __name__ == '__main__':

    # 初期設定

    save_music_structure_to_json(MUSIC_DIR)

    init_admin_user()

    # フォルダ監視を開始（デバッグモードのリローダーによる二重起動を防止）
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        start_watchdog()

    port = int(os.environ.get('PORT', 5000))

    app.run(host="0.0.0.0", port=port, debug=True)
