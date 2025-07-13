import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import minecraft_launcher_lib
import subprocess
import threading
import os
import json
import shutil
import urllib.request
import xml.etree.ElementTree as ET

from PIL import ImageTk, Image
from minecraft_launcher_lib import command

CONFIG_FILE = "launcher_config.json"
MOD_LOADERS = ["vanilla", "forge", "fabric"]

class MinecraftLauncher(tk.Tk):
    def on_close(self):
        self.save_config()
        self.destroy()

    def __init__(self):
        super().__init__()
        self.title("Advanced Offline Minecraft Launcher")
        self.geometry("700x700")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.minecraft_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = self.load_config()
        self.profiles = self.config.get("profiles", {})
        self.history = self.config.get("history", [])
        self.dark_mode = self.config.get("dark_mode", False)

        self.create_widgets()
        self.apply_theme()
        self.load_versions()
        self.load_profile(self.config.get("last_profile", None))

    def browse_mods_folder(self):
        folder = filedialog.askdirectory(title="Select Mods Folder")
        if folder:
            self.mods_folder_var.set(folder)

    def create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0
        ttk.Label(frame, text="Username:").grid(row=row, column=0, sticky="w")
        self.username_entry = ttk.Entry(frame)
        self.username_entry.grid(row=row, column=1, sticky="ew")

        row += 1
        ttk.Label(frame, text="Minecraft Version:").grid(row=row, column=0, sticky="w")
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(frame, textvariable=self.version_var, state="readonly")
        self.version_combo.grid(row=row, column=1, sticky="ew")
        self.version_combo.bind("<<ComboboxSelected>>", lambda e: self.load_forge_versions())

        row += 1
        ttk.Label(frame, text="Max RAM (GB):").grid(row=row, column=0, sticky="w")
        self.ram_entry = ttk.Entry(frame)
        self.ram_entry.grid(row=row, column=1, sticky="ew")

        row += 1
        ttk.Label(frame, text="Extra JVM Args:").grid(row=row, column=0, sticky="w")
        self.jvm_args_entry = ttk.Entry(frame)
        self.jvm_args_entry.grid(row=row, column=1, sticky="ew")

        row += 1
        ttk.Label(frame, text="Fullscreen:").grid(row=row, column=0, sticky="w")
        self.fullscreen_var = tk.BooleanVar()
        self.fullscreen_check = ttk.Checkbutton(frame, variable=self.fullscreen_var)
        self.fullscreen_check.grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame, text="Window Width:").grid(row=row, column=0, sticky="w")
        self.width_entry = ttk.Entry(frame)
        self.width_entry.grid(row=row, column=1, sticky="ew")

        row += 1
        ttk.Label(frame, text="Window Height:").grid(row=row, column=0, sticky="w")
        self.height_entry = ttk.Entry(frame)
        self.height_entry.grid(row=row, column=1, sticky="ew")

        row += 1
        ttk.Label(frame, text="Mod Loader:").grid(row=row, column=0, sticky="w")
        self.loader_var = tk.StringVar(value="vanilla")
        self.loader_combo = ttk.Combobox(frame, textvariable=self.loader_var, values=MOD_LOADERS, state="readonly")
        self.loader_combo.grid(row=row, column=1, sticky="ew")
        self.loader_combo.bind("<<ComboboxSelected>>", lambda e: self.on_loader_change())

        row += 1
        ttk.Label(frame, text="Forge Version:").grid(row=row, column=0, sticky="w")
        self.forge_version_var = tk.StringVar()
        self.forge_version_combo = ttk.Combobox(frame, textvariable=self.forge_version_var, state="readonly")
        self.forge_version_combo.grid(row=row, column=1, sticky="ew")
        self.forge_version_combo.config(values=[])

        row += 1
        ttk.Label(frame, text="Mods Folder:").grid(row=row, column=0, sticky="w")
        self.mods_folder_var = tk.StringVar()
        self.mods_entry = ttk.Entry(frame, textvariable=self.mods_folder_var)
        self.mods_entry.grid(row=row, column=1, sticky="ew")
        ttk.Button(frame, text="Browse", command=self.browse_mods_folder).grid(row=row, column=2, sticky="ew")

        row += 1
        self.launch_button = ttk.Button(frame, text="Launch Minecraft", command=self.launch_minecraft)
        self.launch_button.grid(row=row, column=0, columnspan=3, pady=10)

        frame.columnconfigure(1, weight=1)

        self.log_text = tk.Text(self, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Disable Forge version combobox initially
        self.forge_version_combo.config(state=tk.DISABLED)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_config(self):
        self.config["profiles"] = self.profiles
        self.config["history"] = self.history
        self.config["dark_mode"] = self.dark_mode
        self.config["last_profile"] = "default"
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except:
            pass

    def load_versions(self):
        self.versions = fetch_minecraft_versions(self.minecraft_dir)
        version_ids = [v["id"] for v in self.versions]
        self.version_combo['values'] = version_ids
        if version_ids:
            self.version_var.set(version_ids[0])
            self.load_forge_versions()

    def load_profile(self, profile_name):
        pass

    def on_loader_change(self):
        loader = self.loader_var.get()
        if loader == "forge":
            self.forge_version_combo.config(state=tk.NORMAL)
            self.load_forge_versions()
        else:
            self.forge_version_combo.set("")
            self.forge_version_combo.config(state=tk.DISABLED)

    def load_forge_versions(self):
        loader = self.loader_var.get()
        if loader != "forge":
            self.forge_version_combo.config(state=tk.DISABLED)
            self.forge_version_combo.set("")
            return

        mc_version = self.version_var.get()
        if not mc_version:
            self.forge_version_combo.config(state=tk.DISABLED)
            self.forge_version_combo.set("")
            return

        self.log(f"Fetching Forge versions for Minecraft {mc_version}...")

        def fetch_and_update():
            versions = []
            # Try minecraft_launcher_lib method first
            try:
                import minecraft_launcher_lib.forge as forge_mod
                if hasattr(forge_mod, "get_forge_versions"):
                    versions = forge_mod.get_forge_versions(mc_version)
            except Exception as e:
                self.log(f"Failed to get Forge versions via minecraft_launcher_lib: {e}")

            # Fallback to Maven scraping if no versions found
            if not versions:
                versions = fetch_forge_versions_maven(mc_version)

            if versions:
                # Sort versions descending (latest first)
                versions.sort(reverse=True)
                self.forge_version_combo.config(values=versions)
                self.forge_version_var.set(versions[0])
                self.forge_version_combo.config(state=tk.NORMAL)
                self.log(f"Found Forge versions for Minecraft: {', '.join(versions[:10])}...")
            else:
                self.forge_version_combo.config(values=[])
                self.forge_version_var.set("")
                self.forge_version_combo.config(state=tk.DISABLED)
                self.log(f"No Forge versions found for Minecraft {mc_version}")

        threading.Thread(target=fetch_and_update, daemon=True).start()

    def launch_minecraft(self):
        username = self.username_entry.get().strip()
        base_version = self.version_var.get()
        loader = self.loader_var.get()
        mods_folder = self.mods_folder_var.get().strip()
        jvm_extra = self.jvm_args_entry.get().strip()
        forge_version = self.forge_version_var.get()

        try:
            ram = int(self.ram_entry.get())
        except:
            ram = 2

        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
        except:
            width = 854
            height = 480

        java_args = [f"-Xmx{ram}G"]
        if jvm_extra:
            java_args.extend(jvm_extra.split())

        if self.fullscreen_var.get():
            java_args.append("-Dorg.lwjgl.opengl.Window.undecorated=true")
            java_args.append("-Dorg.lwjgl.opengl.Window.fullscreen=true")
        else:
            java_args.append(f"-Dorg.lwjgl.opengl.Window.width={width}")
            java_args.append(f"-Dorg.lwjgl.opengl.Window.height={height}")

        def thread_launch():
            try:
                # Ensure vanilla base version is installed first
                base_version_path = os.path.join(self.minecraft_dir, "versions", base_version)
                if not os.path.exists(base_version_path):
                    self.log(f"Base version {base_version} not found locally. Downloading vanilla first...")
                    minecraft_launcher_lib.install.install_minecraft_version(base_version, self.minecraft_dir)
                    self.log(f"Base version {base_version} installed.")

                version_to_launch = base_version

                # Install mod loader if needed
                if loader == "forge":
                    if not forge_version:
                        self.log("No Forge version selected, cannot launch Forge.")
                        return
                    self.log(f"Installing Forge version {forge_version}...")
                    minecraft_launcher_lib.forge.install_forge_version(forge_version, self.minecraft_dir)
                    version_to_launch = forge_version
                elif loader == "fabric":
                    self.log(f"Installing Fabric for {base_version}...")
                    minecraft_launcher_lib.fabric.install_fabric(base_version, self.minecraft_dir)
                    versions_folder = os.path.join(self.minecraft_dir, "versions")
                    fabric_versions = [v for v in os.listdir(versions_folder) if "fabric" in v.lower()]
                    if fabric_versions:
                        version_to_launch = sorted(fabric_versions)[-1]

                self.log(f"Launching version: {version_to_launch}")

                # Copy mods if loader needs them and mods folder specified
                if loader in ("forge", "fabric") and mods_folder:
                    mods_dir = os.path.join(self.minecraft_dir, "mods")
                    os.makedirs(mods_dir, exist_ok=True)
                    # Don't copy if already present (to avoid 'same file' errors)
                    for file in os.listdir(mods_folder):
                        if file.endswith(".jar"):
                            src = os.path.join(mods_folder, file)
                            dst = os.path.join(mods_dir, file)
                            if not os.path.exists(dst):
                                shutil.copy(src, dst)
                    self.log(f"Copied mods from {mods_folder} to {mods_dir}")

                from uuid import uuid4
                uuid = str(uuid4())
                options = {
                    "minecraft_directory": self.minecraft_dir,
                    "username": username if username else "OfflineUser",
                    "uuid": uuid,
                    "token": "",
                    "launcher_name": "AdvancedLauncher",
                    "launcher_version": "1.0",
                    "java_args": java_args
                }

                cmd = command.get_minecraft_command(version_to_launch, self.minecraft_dir, options)
                self.log("Launching Minecraft...")
                proc = subprocess.Popen(cmd, cwd=self.minecraft_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout:
                    self.log(line.strip())
                proc.wait()
                self.log("Minecraft closed.")
            except Exception as e:
                self.log(f"Launch error: {e}")

        threading.Thread(target=thread_launch, daemon=True).start()

    def log(self, msg):
        def append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.after(0, append)

    def apply_theme(self):
        pass

def fetch_minecraft_versions(minecraft_dir):
    try:
        mirror_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        with urllib.request.urlopen(mirror_url) as response:
            data = response.read()
            manifest = json.loads(data)
            return manifest.get("versions", [])
    except Exception as e:
        print("Failed to load version manifest:", e)
        return []

def fetch_forge_versions_maven(mc_version):
    """Fetch Forge versions for a given Minecraft version by parsing Forge Maven metadata XML."""
    base_url = "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"
    try:
        with urllib.request.urlopen(base_url) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        versions = []
        for version in root.find('versioning').find('versions').findall('version'):
            ver_str = version.text
            # Forge versions start with the MC version like "1.20.1-47.0.0"
            if ver_str.startswith(mc_version):
                versions.append(ver_str)
        return versions
    except Exception as e:
        print(f"Error fetching Forge versions from Maven: {e}")
        return []

if __name__ == "__main__":
    app = MinecraftLauncher()
    app.mainloop()
