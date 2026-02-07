# home-music-stream

A lightweight, intuitive **Home Music Stream** server designed to let you access your local music library from any device on your home network.

## Features

- **Intuitive Interface:** Browse your music library by Artist and Album.
- **Instant Playback:** Select and play music instantly.
- **Cross-Device Streaming:** Access your PC's music library directly from your smartphone, tablet, or another PC's browser. No more manual file copying between devices.
- **Playlist Management:** Create and manage playlists directly from the UI.
- **Easy Upload:** Drag and drop songs or folders from your browser to the server.
- **Cross-Device Access:** Host on your PC and listen from any device on your home network.

## Why this project?

Existing solutions often felt bloated or didn't offer a simple way to mirror a local folder structure. This project was born out of a desire to solve two main personal frustrations:

- **End the Copying Hassle:** I was tired of manually copying and syncing music files from my main PC to my phone or other devices every time I wanted to listen to something new.
- **Save Mobile Storage:** With limited storage on my smartphone, I had to constantly choose which songs to keep and which to delete. By streaming from a central PC server, I can "carry" my entire library without using any local storage.

It's all about making it easy to listen to your PC's music in any room, on any device, instantly.

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
