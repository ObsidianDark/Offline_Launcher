# Offline_Launcher

A Custom Minecraft Launcher Written Entirely in Python 3.13  
**Current Version:** Beta V0.4

---

## ✨ Features

### 🧠 Core Features
- **Offline Account Support**: Play without needing Mojang/Microsoft login.
- **Online Account Support (Token-Based)**: Enter access tokens to authenticate (e.g. from EasyMC).
- **Skin System (Beta)**: Allows linking `.png` skins to accounts for offline use.

---

### 🎮 Profile System
- Create multiple **profiles** with separate settings:
  - Minecraft version
  - JVM arguments
  - Max RAM allocation
  - Fullscreen mode toggle
  - Custom resolution (window width & height)
  - Username
- **Profile Manager UI**:
  - Add, edit, delete, save profiles
  - Automatically loads selected profile into launch tab

---

### 👥 Account Manager
- Create, edit, and delete Minecraft accounts
- Supports both **offline** and **token-based online** accounts (Though token based accounts are going to be added in the Rel-V0.1)
- Per-account skin file support (Still In Testing)
- Username autofill from selected account
- Integrated into launch tab for easy selection

---

### 🗃️ Minecraft Version Management
- Detects whether selected version is installed
- **Automatic Version Installation** using `minecraft-launcher-lib`
- Manual loading of version manifest JSON if needed (Witch is needed and is found in the same folder)

---

### ⚙️ Advanced Launcher Settings
- Set custom JVM arguments
- Allocate RAM (in GB)
- Toggle fullscreen
- Set window resolution

---

### 🪟 GUI Features
- **Tabbed Interface** with:
  - Launch tab
  - Profile tab
  - Account tab
  - Settings tab (placeholder/future features)
  - Console Log tab

---

### 🧾 Console Log Viewer
- Live output of Minecraft's stdout/stderr
- Useful for debugging modpacks or crashes

---

### 🌒 Optional Dark Mode Support (config entry)
- Stored in `launcher_config.json`
- More theme customizations coming soon

---

## 📂 Configuration and Persistence
- All data (accounts, profiles, settings) stored in `launcher_config.json`
- Minecraft directory is persistent across restarts
- First launch will prompt to select Minecraft folder

---

## 🛠️ Requirements
- Python 3.13+
- Dependencies:
  - `minecraft-launcher-lib`
  - `tkinter` (usually included)
  - `requests`

Install dependencies with:

```bash
pip install minecraft-launcher-lib requests
