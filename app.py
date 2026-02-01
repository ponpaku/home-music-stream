# app.py

from flask import Flask, send_from_directory, jsonify, url_for, request, session, redirect, render_template
import os
import json
import hashlib
import uuid
import functools
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)

# ディレクトリ設定
MUSIC_DIR = 'static/music'  # 音楽ファイルが保存されているディレクトリへのパス
USERS_DIR = 'users'  # ユーザー情報を保存するディレクトリ
MUSIC_STRUCTURE_FILE = 'music_structure.json'

# ディレクトリが存在しない場合は作成
os.makedirs(USERS_DIR, exist_ok=True)

# 管理者情報の初期設定
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "pass0000"

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
    music_structure = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.mp3', '.wav')):
                artist_album = os.path.relpath(root, start=directory).split(os.sep)
                if len(artist_album) == 2:  # アーティスト/アルバムの構造を想定
                    artist, album = artist_album
                    if artist not in music_structure:
                        music_structure[artist] = {}
                    if album not in music_structure[artist]:
                        music_structure[artist][album] = []
                    music_structure[artist][album].append(file)
    
    with open(MUSIC_STRUCTURE_FILE, 'w', encoding='utf-8') as outfile:
        json.dump(music_structure, outfile, ensure_ascii=False)

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

@app.route('/get-song-data/<string:song_name>')
@login_required
def get_song_data(song_name):
    music_structure = load_music_structure()  # 楽曲データのロード

    # 楽曲データを検索する処理
    for artist, albums in music_structure.items():
        for album, songs in albums.items():
            if song_name in songs:
                # 曲が見つかった場合の処理
                # 静的ファイルへのパスを生成
                song_path = url_for('static', filename=f'music/{artist}/{album}/{song_name}')
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
    
    app.run(host="0.0.0.0", debug=True)