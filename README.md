# Offline_Launcher

A Custom Minecraft Launcher Written Entirely in Python 3.13  
**Current Version:** Beta V0.4

---

## ✨ Features

### 🧠 Core Features
- **Offline Account Support**: Play without needing Mojang/Microsoft login.
- **Online Account Support (Token-Based)**: Enter access tokens to authenticate (e.g. from EasyMC).
- **Skin System (Beta)**: Allows linking `.png` skins to accounts for offline use *(still in testing)*.

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
  - Automatically loads selected profile into the launch tab

---

### 👥 Account Manager
- Create, edit, and delete Minecraft accounts
- Supports both **offline** and **token-based online** accounts  
  *(Online/token support coming fully in Release V0.1)*
- Per-account skin file support *(still being tested)*
- Username autofill from selected account
- Integrated into launch tab for easy selection

---

### 🗃️ Minecraft Version Management
- Detects whether the selected version is installed
- **Automatic Version Installation** using `minecraft-launcher-lib`
- Requires a local **version manifest JSON** (must be in the same folder as the launcher)

---

### ⚙️ Advanced Launcher Settings
- Set custom JVM arguments
- Allocate RAM (in GB)
- Toggle fullscreen
- Set custom window resolution

---

### 🪟 GUI Features
- Clean **Tabbed Interface**:
  - Launch tab
  - Profile tab
  - Account tab
  - Settings tab *(placeholder for future features)*
  - Console Log tab

---

### 🧾 Console Log Viewer
- Live output from Minecraft’s stdout/stderr
- Helpful for debugging, modpacks, crashes, etc.

---

### 🌒 Dark Mode Support *(Early)*
- Controlled via `launcher_config.json`
- Full theming support planned

---

## 📂 Configuration and Persistence
- All user data (accounts, profiles, settings) saved in `launcher_config.json`
- Minecraft directory is saved and reused between sessions
- First launch will ask for Minecraft folder if not already set

---

## 🛠️ Requirements
- Python 3.13+
- Dependencies:
  - `minecraft-launcher-lib`
  - `tkinter` (usually bundled with Python)
  - `requests`

### 📦 Install Dependencies
```bash
pip install minecraft-launcher-lib requests
