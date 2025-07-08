<p align="center">
  <img src="logo.png" alt="Offline Launcher Logo" width="200"/>
</p>

<h1 align="center">Offline_Launcher</h1>

<p align="center"><b>A Custom Minecraft Launcher Written Entirely in Python 3.13</b></p>
<p align="center"><b>Current Version: Beta V0.5</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13%2B-blue" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey" />
</p>

---

## ✨ Features

### 🧠 Core
- 🟢 **Offline Account Support** — Play without Mojang/Microsoft login.
- 🔵 **Online Account Support (Token-Based)** — Use access tokens (under testing).
- 🟡 **Skin System (Beta)** — Link `.png` skins to offline accounts (under testing).

### 🎮 Profile System
- Create and manage multiple **launch profiles**:
  - Minecraft version
  - JVM arguments
  - RAM allocation
  - Fullscreen toggle
  - Custom window size
  - Username
- 🖱️ Profile UI:
  - Add / Edit / Delete / Save profiles
  - Automatically loads selected profile into launch tab

### 👥 Account Manager
- Manage **offline** and **token-based online** accounts  
  *(Online token support coming in Release V0.1)*  
- Per-account skin file support *(in beta)*
- Username autofill
- Dropdown selector in Launch tab

### 📦 Minecraft Version Management
- 📂 Check if selected version is installed
- 🔄 Auto-install versions using `minecraft-launcher-lib`
- 📁 Manual loading of `version_manifest.json` (must be in same folder)

### ⚙️ Advanced Settings
- Custom JVM arguments
- RAM allocation (in GB)
- Fullscreen toggle
- Set window resolution (width & height)

### 🖼️ GUI Features
- Clean **tabbed interface** using `tkinter`:
  - 🚀 Launch tab
  - 🧾 Profiles tab
  - 👤 Accounts tab
  - ⚙️ Settings tab *(placeholder)*
  - 📜 Console Log tab

### 📜 Console Output Viewer
- Real-time Minecraft stdout/stderr log
- Useful for tracking mod crashes and errors

### 🌙 Dark Mode (configurable)
- Enabled via `launcher_config.json`  
- Custom themes coming in future versions

---

## 💾 Persistence & Config
- All settings stored in: `launcher_config.json`
- Saves:
  - Accounts
  - Profiles
  - Last selected Minecraft directory
- Prompts for Minecraft directory on first launch

---

## 🐞 Known Bugs & Issues
- Launcher may fail to open if configuration files are corrupted.  
  *Fix:* Delete `launcher_config.json` or `launcher.json` to reset (will lose saved profiles/accounts).
- Online token login is still experimental; may not work reliably.
- Skin system is in beta and can occasionally fail to load skins.
- Some Minecraft versions may fail to auto-install due to network issues.
- Dark mode may not apply consistently on all UI elements.

---

## 🚧 Things That Need To Be Added
- ✅ Full online login support with Microsoft OAuth flow
- ✅ Automatic skin download from Mojang servers for online accounts
- ✅ Mod support (loading and launching Forge/Fabric mods)
- ✅ Custom resource pack management
- ✅ Profile export/import
- ✅ Configurable launcher themes
- ✅ Better error handling and user-friendly messages
- ✅ Localization / multi-language support
- ✅ Launcher auto-update mechanism
- ✅ Support for additional platforms (macOS, other Linux distros)
- ✅ Integration with popular Minecraft server lists

---

## 🛠️ Requirements

- Python 3.13+
- Dependencies:
  - `minecraft-launcher-lib`
  - `requests`
  - `tkinter` *(usually pre-installed with Python)*

---

## 📥 Installation

1. Clone this repository or download the ZIP and extract it.
2. Install required packages:

```bash
pip install minecraft-launcher-lib requests
