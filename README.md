<p align="center">
  <img src="logo.png" alt="Offline Launcher Logo" width="200"/>
</p>

<h1 align="center">Offline_Launcher</h1>

<p align="center"><b>A Custom Minecraft Launcher Written Entirely in Python 3.13</b></p>
<p align="center"><b>Current Version: Beta V0.4</b></p>

---

## ✨ Features

### 🧠 Core
- 🟢 **Offline Account Support** — Play without Mojang/Microsoft login.
- 🔵 **Online Account Support (Token-Based)** — Use access tokens (e.g. from EasyMC).
- 🟡 **Skin System (Beta)** — Link `.png` skins to offline accounts (under testing).

---

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

---

### 👥 Account Manager
- Manage **offline** and **token-based online** accounts  
  *(Online token support coming in Release V0.1)*  
- Per-account skin file support *(in beta)*
- Username autofill
- Dropdown selector in Launch tab

---

### 📦 Minecraft Version Management
- 📂 Check if selected version is installed
- 🔄 Auto-install versions using `minecraft-launcher-lib`
- 📁 Manual loading of `version_manifest.json` (must be in same folder)

---

### ⚙️ Advanced Settings
- Custom JVM arguments
- RAM allocation (in GB)
- Fullscreen toggle
- Set window resolution (width & height)

---

### 🖼️ GUI Features
- Clean **tabbed interface** using `tkinter`:
  - 🚀 Launch tab
  - 🧾 Profiles tab
  - 👤 Accounts tab
  - ⚙️ Settings tab *(placeholder)*
  - 📜 Console Log tab

---

### 📜 Console Output Viewer
- Real-time Minecraft stdout/stderr log
- Useful for tracking mod crashes and errors

---

### 🌙 Dark Mode (configurable)
- Enabled via `launcher_config.json`  
- Custom themes in future versions

---

## 💾 Persistence & Config
- All settings stored in: `launcher_config.json`
- Saves:
  - Accounts
  - Profiles
  - Last selected Minecraft directory
- Prompts for Minecraft directory on first launch

---

## 🛠️ Requirements

- Python 3.13+
- Dependencies:
  - `minecraft-launcher-lib`
  - `requests`
  - `tkinter` *(usually pre-installed)*

### 📥 Install Dependencies

```bash
pip install minecraft-launcher-lib requests
