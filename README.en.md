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
