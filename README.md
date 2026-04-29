# Infinity Browser

A fast, private, and feature-rich desktop web browser built with Python and PyQt6.
Powered by the Chromium rendering engine via QtWebEngine, Infinity delivers a modern
browsing experience with built-in ad blocking, a secure local password vault, tabbed
browsing, download management, and full keyboard shortcut support — all without
sending any data to external servers.

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Quick Install (all distros)](#quick-install-all-distros)
  - [Fedora / RHEL / CentOS Stream](#fedora--rhel--centos-stream)
  - [Debian / Ubuntu / Linux Mint](#debian--ubuntu--linux-mint)
  - [Arch Linux / Manjaro](#arch-linux--manjaro)
  - [openSUSE](#opensuse)
- [Desktop Integration](#desktop-integration)
- [Usage](#usage)
  - [Navigation](#navigation)
  - [Tabs](#tabs)
  - [Bookmarks](#bookmarks)
  - [History](#history)
  - [Downloads](#downloads)
  - [Password Manager](#password-manager)
  - [Notes](#notes)
  - [Settings](#settings)
  - [Open Local Files](#open-local-files)
  - [Print to PDF](#print-to-pdf)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Privacy](#privacy)
- [Project Structure](#project-structure)
- [License](#license)

---

## About

Infinity is an open-source desktop web browser designed for Linux. It is built as a
single Python application with no cloud dependencies, no telemetry, and no external
accounts required. All user data — history, bookmarks, passwords, notes, and settings —
is stored locally on your machine.

The browser uses the Chromium-based Blink rendering engine (through QtWebEngine), which
means it renders modern websites correctly and supports HTML5, CSS3, JavaScript, WebAssembly,
and native PDF viewing out of the box.

Version: 1.0.0
Developer: Ayush Kumar Maurya

---

## Features

### Browsing
- Chromium/Blink rendering engine via QtWebEngine
- Tabbed browsing with a clean, dark-themed interface
- Smart address bar that accepts both URLs and search queries
- Configurable default search engine (Google, DuckDuckGo, Bing, Ecosia, Brave Search)
- Configurable homepage URL
- Back, Forward, Reload, and Home navigation buttons
- Page load progress indicator

### Privacy and Security
- Built-in ad blocker with a curated domain blocklist covering Google ads,
  Facebook/Meta trackers, analytics services, fingerprinting networks, and
  over 60 known ad and tracker domains
- Do Not Track request header support
- Pop-up window blocking
- JavaScript toggle (enable or disable per session)
- HTTPS-Only mode with a warning for insecure HTTP sites
- Safe Browsing protection
- One-click clearing of history, cache, and cookies individually or all at once

### Password Manager
- Secure local password vault with AES-equivalent encryption
- Keys derived with PBKDF2-HMAC-SHA256 and per-entry random nonces
- HMAC-SHA256 message authentication to detect tampering
- Encryption key stored in a local file with owner-only permissions (chmod 600)
- Passwords are never transmitted to any external service

### Bookmarks
- Add and remove bookmarks from the navigation bar with one click
- Full bookmark manager panel with search filter
- Visual indicator in the address bar showing whether the current page is bookmarked

### History
- Browsing history stored locally in JSON format
- History manager with full-text search capability
- One-click clearing from Settings

### Download Manager
- Live download progress with speed tracking (KB/s or MB/s)
- Two download modes: Ask (Save dialog for every download) or Auto (save to a preset folder)
- Configurable download directory
- Download history panel accessible via Ctrl+J

### Notes
- Built-in notes panel for saving personal notes while browsing
- Notes are stored locally and persist across sessions

### Local File Support
- Open local HTML, PDF, video, audio, image, and text files directly in the browser
- Format-aware file picker via Ctrl+O

### PDF Viewer
- Native PDF rendering via the built-in Chromium PDF plugin
- No external viewer required

### Media Playback
- HTML5 audio and video playback
- Supported formats: MP4, MKV, AVI, MOV, FLV, WMV, MP3, WAV, OGG, FLAC

### Interface
- Frameless dark window with custom title bar
- Minimize, maximize/restore, and close controls
- Double-click title bar to toggle maximize
- Application-level keyboard shortcut handling (shortcuts work even when the web view has focus)

### Settings
- General: Homepage URL, startup behavior, search engine selection, toolbar options
- Appearance: Default font size, default zoom level (25% to 300%)
- Privacy: Ad blocker toggle, Do Not Track, pop-up blocker, JavaScript toggle, data clearing
- Security: HTTPS-Only mode, Safe Browsing
- Downloads: Download mode (ask/auto), save location

---

## Technology Stack

| Component         | Technology                        |
|-------------------|-----------------------------------|
| Rendering Engine  | Chromium / Blink (QtWebEngine)    |
| Media Backend     | FFmpeg 7.x (built-in codecs)      |
| UI Framework      | PyQt6 (Qt 6.7 LTS)                |
| Language          | Python 3.10+                      |
| Platform          | Linux (x86-64)                    |

---

## Requirements

- Python 3.10 or newer
- pip
- PyQt6
- PyQt6-WebEngine

These Python packages are listed in `requirements.txt` and will be installed automatically
by the instructions below.

---

## Installation

### Quick Install (all distros)

If you already have Python 3 and pip installed, you can clone the repo and run
the provided installer script. It handles Python dependencies, the application
icon, and desktop integration in one step:

```bash
git clone https://github.com/dev-hints/infinity-browser.git
cd infinity-browser
chmod +x install.sh
./install.sh
```

After the script finishes, Infinity Browser will appear in your application
launcher with the correct icon. To launch it manually at any time:

```bash
python3 main.py
```

For distros where pip is not yet installed, follow the per-distro steps below
first, then run `install.sh`.

---

### Fedora / RHEL / CentOS Stream

**Install system dependencies:**

```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip git
```

On RHEL 8/9 and CentOS Stream, enable the CodeReady Linux Builder (CRB) repository first
if `python3-pip` is not available:

```bash
sudo dnf install -y epel-release
sudo dnf config-manager --enable crb
sudo dnf install -y python3 python3-pip git
```

**Clone and install:**

```bash
git clone https://github.com/dev-hints/infinity-browser.git
cd infinity-browser
chmod +x install.sh
./install.sh
```

---

### Debian / Ubuntu / Linux Mint

**Install system dependencies:**

```bash
sudo apt update
sudo apt install -y python3 python3-pip git
```

> Note: On Ubuntu 22.04 and newer, or Debian 12 (Bookworm) and newer, pip may refuse
> system-wide installs (PEP 668). The `install.sh` script uses `pip3 install --user`
> which works without a virtual environment. If you prefer a venv:

```bash
sudo apt install -y python3-venv
python3 -m venv .venv
source .venv/bin/activate
```

Then edit the `Exec=` line in the generated `.desktop` file to use `.venv/bin/python`
instead of `python3`.

**Clone and install:**

```bash
git clone https://github.com/dev-hints/infinity-browser.git
cd infinity-browser
chmod +x install.sh
./install.sh
```

---

### Arch Linux / Manjaro

**Install system dependencies:**

```bash
sudo pacman -Syu --noconfirm python python-pip git
```

> Alternatively, PyQt6 and PyQt6-WebEngine are available in the official extra
> repository. You may install them system-wide instead of via pip:
> `sudo pacman -S python-pyqt6 python-pyqt6-webengine`
> In that case, skip the pip step inside `install.sh` (the script will still handle
> icon and desktop entry setup).

**Clone and install:**

```bash
git clone https://github.com/dev-hints/infinity-browser.git
cd infinity-browser
chmod +x install.sh
./install.sh
```

---

### openSUSE

**Applies to: openSUSE Leap 15.x and Tumbleweed**

**Install system dependencies:**

```bash
sudo zypper refresh
sudo zypper install -y python3 python3-pip git
```

**Clone and install:**

```bash
git clone https://github.com/dev-hints/infinity-browser.git
cd infinity-browser
chmod +x install.sh
./install.sh
```

---

## Desktop Integration

Desktop integration is handled automatically by `install.sh`. Running it once is
all that is needed:

```bash
chmod +x install.sh
./install.sh
```

The script performs four steps:

1. Installs Python dependencies via pip.
2. Copies `icons/infinity-browser.png` to `~/.local/share/icons/hicolor/512x512/apps/`
   and refreshes the icon cache.
3. Reads `infinity-browser.desktop.template`, replaces the `__INSTALL_DIR__`
   placeholder with the actual clone path, and writes the result to
   `~/.local/share/applications/infinity-browser.desktop`.
4. Pins the app to the GNOME dock (skipped silently on non-GNOME desktops).

After the script finishes, the browser appears in your application launcher with
the correct icon. The icon is also shown in the taskbar while the app is running.

If you later move the project folder, run `install.sh` again to regenerate the
desktop entry with the updated path.

---

## Usage

### Navigation

Type a URL or a search query in the address bar and press Enter. The browser
automatically detects whether you entered a URL or a search term:

- If the input contains a dot and no spaces, it is treated as a URL.
- Otherwise, it is sent to your configured search engine.
- Absolute file paths (starting with `/`) are opened as local files.

Use the Back, Forward, Reload, and Home buttons in the navigation bar, or use
keyboard shortcuts for faster navigation.

### Tabs

Open a new tab with Ctrl+T. Close the current tab with Ctrl+W. Switch between tabs
by clicking on them. The minimum number of open tabs is one; closing the last tab
will not close the browser.

### Bookmarks

Click the star icon in the navigation bar to bookmark the current page. A filled star
indicates the page is already bookmarked; clicking it again removes the bookmark.

Open the Bookmark Manager with Ctrl+B. The manager shows all saved bookmarks and
includes a search box to filter by title or URL.

### History

Open the History panel with Ctrl+H. All visited pages are listed with their title,
URL, and timestamp. Use the search box to find specific entries. History can be
cleared from Settings under the Privacy tab.

### Downloads

All downloads are tracked in the Download Manager, accessible via Ctrl+J. Each entry
shows the filename, download speed, progress, and final status. Two download modes
are available:

- Ask: a Save As dialog appears for every download.
- Auto: files are saved automatically to the configured download folder.

Download mode and save location are configured under Settings — Downloads.

### Password Manager

Open the Password Manager from the browser menu (the three-dot button). Saved entries
include a website URL, username, and encrypted password. You can add, view, and delete
entries. Passwords are decrypted only in memory when viewed and are never written in
plain text.

### Notes

Open the Notes panel with Ctrl+Shift+N or from the browser menu. Notes are plain text
and are saved automatically. This panel is useful for keeping quick references or
copying text from web pages.

### Settings

Open Settings from the browser menu. Settings are organized into five tabs:

- General: Set your homepage URL, choose a default search engine, and toggle
  the Home button in the toolbar.
- Appearance: Adjust the default font size and default zoom level for all pages.
- Privacy: Toggle the ad blocker, Do Not Track header, pop-up blocker, and
  JavaScript. Clear browsing history, cache, and cookies.
- Security: Enable HTTPS-Only mode and Safe Browsing protection.
- Downloads: Set the download mode (ask or auto) and the default save folder.

Changes take effect immediately for appearance and privacy settings. Some security
settings may require reopening affected tabs.

### Open Local Files

Press Ctrl+O to open a local file. The following formats are supported:

- Web pages: .html, .htm
- Documents: .pdf
- Video: .mp4, .mkv, .avi, .mov, .flv, .wmv
- Audio: .mp3, .wav, .ogg, .flac
- Images: .png, .jpg, .jpeg, .gif, .webp, .svg
- Text: .txt, .md, .json, .xml, .csv

The file opens in a new tab.

### Print to PDF

Press Ctrl+P to save the current page as a PDF file. A Save dialog will appear
to choose the output location. The PDF is rendered by the Chromium engine and
preserves page layout and images.

---

## Keyboard Shortcuts

| Shortcut       | Action                        |
|----------------|-------------------------------|
| Ctrl+T         | Open a new tab                |
| Ctrl+W         | Close the current tab         |
| Ctrl+R         | Reload the current page       |
| Ctrl+L         | Focus the address bar         |
| Ctrl+B         | Open Bookmark Manager         |
| Ctrl+H         | Open History panel            |
| Ctrl+J         | Open Download Manager         |
| Ctrl+O         | Open a local file             |
| Ctrl+P         | Print current page to PDF     |
| Ctrl+Shift+N   | Open Notes panel              |

---

## Privacy

Infinity Browser does not collect, transmit, or sell any personal data. There are no
servers, analytics pipelines, or telemetry systems associated with this application.

All data generated during your browsing session is stored exclusively on your local device:

- Browsing history is stored in `history.json` inside the application directory.
- Bookmarks are stored in `bookmarks.json`.
- Notes are stored in `notes.json`.
- Settings are stored in `settings.json`.
- Passwords are encrypted and stored in `passwords.json`. The encryption key is stored
  in `.vault.key` with owner-only file permissions (mode 600).

Search queries are sent directly to your chosen search engine. Infinity does not
intercept or log these queries.

The built-in ad blocker helps reduce third-party tracking by blocking requests to over
60 known ad networks, analytics services, and fingerprinting domains.

---

## Project Structure

Files marked with [git] are tracked and pushed to GitHub.
Files marked with [local] are generated at install time or contain user data and
are excluded from version control via `.gitignore`.

```
infinity-browser/
│
│  -- Source code (pushed to GitHub) --
├── main.py                            [git]  Entry point; initializes the QApplication
├── browser_window.py                  [git]  Main window, title bar, menu, shortcuts
├── navigation_bar.py                  [git]  Address bar, nav buttons, bookmark toggle
├── tab_manager.py                     [git]  Tab widget and WebEngine view management
├── bookmark_manager.py                [git]  Bookmark storage and manager dialog
├── history_manager.py                 [git]  History recording and manager dialog
├── download_manager.py                [git]  Download tracking, progress, manager dialog
├── password_manager.py                [git]  Encrypted password vault and manager dialog
├── notes_manager.py                   [git]  Notes storage and editor dialog
├── ad_blocker.py                      [git]  URL request interceptor with domain blocklist
├── scheme_handler.py                  [git]  Custom infinity:// URL scheme handler
├── settings_manager.py                [git]  Settings persistence and retrieval
├── settings_dialog.py                 [git]  Settings UI with five tabbed sections
├── media_player.py                    [git]  HTML5 media playback support
├── styles.qss                         [git]  Qt stylesheet for the application theme
├── new_tab.html                       [git]  Custom new tab page
│
│  -- Distribution files (pushed to GitHub) --
├── requirements.txt                   [git]  Python package dependencies
├── install.sh                         [git]  One-step installer for any Linux desktop
├── infinity-browser.desktop.template  [git]  Desktop entry template (__INSTALL_DIR__ placeholder)
├── .gitignore                         [git]  Files excluded from version control
├── README.md                          [git]  This file
│
│  -- Application icon (pushed to GitHub) --
├── icons/
│   ├── infinity-browser.png           [git]  App icon installed to hicolor theme (512x512)
│   ├── close_tab.svg                  [git]  Tab close button icon
│   └── close_tab_hover.svg            [git]  Tab close button hover state icon
│
│  -- Example data files (pushed to GitHub, used on first run) --
├── history.json.example               [git]  Empty history template
├── bookmarks.json.example             [git]  Empty bookmarks template
├── notes.json.example                 [git]  Empty notes template
└── downloads.json.example             [git]  Empty downloads template

  -- Generated at install time (local only, not in GitHub) --
    infinity-browser.desktop           [local] Generated by install.sh with the real path

  -- User data files (local only, never pushed) --
    history.json                       [local] Your browsing history
    bookmarks.json                     [local] Your saved bookmarks
    notes.json                         [local] Your personal notes
    downloads.json                     [local] Your download history
    settings.json                      [local] Your settings
    passwords.json                     [local] Encrypted password store
    .vault.key                         [local] Encryption key (chmod 600, never share)
```

---

## License

Infinity Browser is released under the MIT License.

Third-party components used in this project:

- Qt / PyQt6 — GNU GPL v3 / Commercial (used under GPL)
- Chromium / QtWebEngine — BSD and other open-source licenses
- FFmpeg — LGPL 2.1+ (bundled codec support)

See the respective project websites for full license details.

---

Copyright 2026 StrangeInfinity. All rights reserved.
