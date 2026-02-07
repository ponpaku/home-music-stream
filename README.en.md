# home-music-stream

A lightweight, intuitive **Home Music Stream** server designed to let you access your local music library from any device on your home network.

## Features

- **Intuitive Interface:** Browse your music library by Artist and Album.
- **Instant Playback:** Select and play music instantly.
- **Playlist Management:** Create and manage playlists directly from the UI.
- **Easy Upload:** Drag and drop songs or folders directly from your browser, or use the upload dialog to add music to the server (automatically organizes the structure).
- **Cross-Device Access:** Host on your PC and listen on your phone or tablet.

## Why this project?

Existing solutions often felt bloated or didn't offer the simple, "select and play" experience I wanted. This project was built to allow:
- Direct access to the PC's music folder structure.
- Quick playlist creation.
- A seamless experience across devices without complex synchronization.

## Configuration

You can customize the port and music directory by creating a `.env` file.

1. Copy `.env.example` to `.env`.
2. Edit the values in `.env` as needed.

Main options:
- `PORT`: Server startup port (default: 5000)
- `MUSIC_DIR`: Directory where music files are stored (default: static/music)
- `SECRET_KEY`: Flask session secret key
- `ADMIN_USERNAME`: Default admin username
- `ADMIN_PASSWORD`: Default admin password

## Setup & Usage

### Prerequisites
- Python 3.x installed.
- Music files (MP3/WAV) placed in `static/music/`.

### Directory Structure
Place your music files in the following structure:
```
static/music/
  ├── Artist Name/
  │   ├── Album Name/
  │   │   ├── Song1.mp3
  │   │   └── Song2.mp3
```

### Running the Server

**Windows:**
Double-click `run.bat`.

**Linux/macOS:**
Run the shell script:
```bash
chmod +x run.sh
./run.sh
```

The script will automatically set up the virtual environment, install dependencies, and start the server.

### Accessing the App
Open your browser and navigate to:
`http://localhost:5000` (or the IP address of the host machine).

### Default Login
- **Username:** `admin`
- **Password:** `pass0000`

*Note: Change the default credentials or secret key in `app.py` for production use.*
