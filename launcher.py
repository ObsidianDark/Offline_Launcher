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
import re
import random
import string

from minecraft_launcher_lib import command
from uuid import uuid4, uuid3, NAMESPACE_DNS

CONFIG_FILE = "launcher_config.json"
MOD_LOADERS = ["vanilla", "forge", "fabric"]

# Your secret token - only players with this token in username can join
LAUNCHER_SECRET_TOKEN = "¨"

# Sample 16-word list for name generation (expand as needed)
WORD_LIST_16 = [
    "apple", "banana", "cherry", "date",
    "elder", "fig", "grape", "hazel",
    "iris", "juniper", "kiwi", "lemon",
    "mango", "nectar", "olive", "pear",
]

def generate_secret_token(length=8):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(random.choice(chars) for _ in range(length))

def offline_uuid(username):
    return str(uuid3(NAMESPACE_DNS, f"OfflinePlayer:{username}"))

def grant_op(minecraft_dir, username):
    ops_path = os.path.join(minecraft_dir, "ops.json")
    uuid = offline_uuid(username)
    entry = {
        "uuid": uuid,
        "name": username,
        "level": 4,
        "bypassesPlayerLimit": True
    }

    try:
        if os.path.exists(ops_path):
            with open(ops_path, "r", encoding="utf-8") as f:
                ops = json.load(f)
        else:
            ops = []

        if not any(op.get("uuid") == uuid for op in ops):
            ops.append(entry)
            with open(ops_path, "w", encoding="utf-8") as f:
                json.dump(ops, f, indent=4)
    except Exception as e:
        print(f"Error updating ops.json: {e}")

def get_latest_server_jar_url():
    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    try:
        with urllib.request.urlopen(manifest_url) as response:
            data = json.loads(response.read())
        latest_version = data["latest"]["release"]
        version_info_url = None
        for v in data["versions"]:
            if v["id"] == latest_version:
                version_info_url = v["url"]
                break
        if not version_info_url:
            print("Could not find latest version info URL")
            return None
        with urllib.request.urlopen(version_info_url) as response:
            version_data = json.loads(response.read())
        server_url = version_data["downloads"]["server"]["url"]
        return server_url
    except Exception as e:
        print(f"Failed to fetch latest server.jar URL: {e}")
        return None

def token_to_name(token):
    """
    Convert the token string into a deterministic 16-word name
    using the WORD_LIST_16.
    """
    # Convert token to bytes
    token_bytes = token.encode('utf-8')
    words = []
    for i in range(16):
        # Use bytes cyclically for index calculation
        b = token_bytes[i % len(token_bytes)]
        idx = b % len(WORD_LIST_16)
        words.append(WORD_LIST_16[idx])
    return "_".join(words)

class MinecraftLauncher(tk.Tk):

    def on_close(self):
        self.save_config()
        self.stop_server_process()
        self.destroy()

    def __init__(self):
        super().__init__()
        self.title("Advanced Offline Minecraft Launcher")
        self.geometry("700x820")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.minecraft_dir = os.path.dirname(os.path.abspath(__file__))
        self.server_dir = os.path.join(self.minecraft_dir, "server")
        os.makedirs(self.server_dir, exist_ok=True)

        self.config = self.load_config()
        self.profiles = self.config.get("profiles", {})
        self.history = self.config.get("history", [])
        self.dark_mode = self.config.get("dark_mode", False)

        self.server_process = None
        self.server_thread = None

        self.create_widgets()
        self.apply_theme()
        self.load_versions()
        self.load_profile(self.config.get("last_profile", None))

    def browse_mods_folder(self):
        folder = filedialog.askdirectory(title="Select Mods Folder")
        if folder:
            self.mods_folder_var.set(folder)

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # --- Launcher Tab ---
        launcher_frame = ttk.Frame(notebook)
        notebook.add(launcher_frame, text="Launcher")

        frame = ttk.Frame(launcher_frame)
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

        row += 1
        self.reset_token_button = ttk.Button(frame, text="Reset Secret Token", command=self.reset_secret_token)
        self.reset_token_button.grid(row=row, column=0, columnspan=3, pady=(0,10))

        row += 1
        # --- New toggle for token-as-name ---
        self.use_token_name_var = tk.BooleanVar(value=False)
        self.token_name_check = ttk.Checkbutton(frame, text="Use token as name (16 words)", variable=self.use_token_name_var)
        self.token_name_check.grid(row=row, column=0, columnspan=3, sticky="w")

        frame.columnconfigure(1, weight=1)

        self.log_text = tk.Text(launcher_frame, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Disable Forge version combobox initially
        self.forge_version_combo.config(state=tk.DISABLED)

        # --- Server Tab ---
        server_frame = ttk.Frame(notebook)
        notebook.add(server_frame, text="Server")

        server_controls = ttk.Frame(server_frame)
        server_controls.pack(fill=tk.X, padx=10, pady=10)

        self.download_button = ttk.Button(server_controls, text="Download Server.jar", command=self.download_server_jar)
        self.download_button.pack(side=tk.LEFT, padx=5)

        self.start_server_button = ttk.Button(server_controls, text="Start Server", command=self.start_server)
        self.start_server_button.pack(side=tk.LEFT, padx=5)

        self.stop_server_button = ttk.Button(server_controls, text="Stop Server", command=self.stop_server_process, state=tk.DISABLED)
        self.stop_server_button.pack(side=tk.LEFT, padx=5)

        self.server_log_text = tk.Text(server_frame, height=20, state=tk.DISABLED)
        self.server_log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def reset_secret_token(self):
        global LAUNCHER_SECRET_TOKEN
        LAUNCHER_SECRET_TOKEN = generate_secret_token()
        messagebox.showinfo("Secret Token Reset",
                            f"The secret token has been reset to:\n\n{LAUNCHER_SECRET_TOKEN}\n\n"
                            "Make sure to share this new token with your players.")
        self.log(f"Secret token reset: {LAUNCHER_SECRET_TOKEN}")

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
            try:
                import minecraft_launcher_lib.forge as forge_mod
                if hasattr(forge_mod, "get_forge_versions"):
                    versions = forge_mod.get_forge_versions(mc_version)
            except Exception as e:
                self.log(f"Failed to get Forge versions via minecraft_launcher_lib: {e}")

            if not versions:
                versions = fetch_forge_versions_maven(mc_version)

            if versions:
                versions.sort(reverse=True)
                self.forge_version_combo.config(values=versions)
                self.forge_version_var.set(versions[0])
                self.forge_version_combo.config(state=tk.NORMAL)
                self.log(f"Found Forge versions: {', '.join(versions[:10])}...")
            else:
                self.forge_version_combo.config(values=[])
                self.forge_version_var.set("")
                self.forge_version_combo.config(state=tk.DISABLED)
                self.log(f"No Forge versions found for Minecraft {mc_version}")

        threading.Thread(target=fetch_and_update, daemon=True).start()

    def launch_minecraft(self):
        username = self.username_entry.get().strip()
        if not username:
            username = "OfflineUser"

        # --- Use token as entire name if checkbox enabled ---
        if self.use_token_name_var.get():
            username_with_token = token_to_name(LAUNCHER_SECRET_TOKEN)
        else:
            username_with_token = username + LAUNCHER_SECRET_TOKEN

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
                base_version_path = os.path.join(self.minecraft_dir, "versions", base_version)
                if not os.path.exists(base_version_path):
                    self.log(f"Base version {base_version} not found locally. Downloading vanilla first...")
                    minecraft_launcher_lib.install.install_minecraft_version(base_version, self.minecraft_dir)
                    self.log(f"Base version {base_version} installed.")

                version_to_launch = base_version

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

                if loader in ("forge", "fabric") and mods_folder:
                    mods_dir = os.path.join(self.minecraft_dir, "mods")
                    os.makedirs(mods_dir, exist_ok=True)
                    for file in os.listdir(mods_folder):
                        if file.endswith(".jar"):
                            src = os.path.join(mods_folder, file)
                            dst = os.path.join(mods_dir, file)
                            if not os.path.exists(dst):
                                shutil.copy(src, dst)
                    self.log(f"Copied mods from {mods_folder} to {mods_dir}")

                # Grant OP with original username (without token or phrase)
                grant_op(self.minecraft_dir, username)
                self.log(f"Granted OP to {username} (offline UUID: {offline_uuid(username)}).")

                options = {
                    "minecraft_directory": self.minecraft_dir,
                    "username": username_with_token,
                    "uuid": str(uuid4()),
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

    def download_server_jar(self):
        jar_path = os.path.join(self.server_dir, "server.jar")
        if os.path.exists(jar_path):
            messagebox.showinfo("Info", "server.jar already exists.")
            return

        def download():
            try:
                self.log_server("Fetching latest server.jar URL...")
                url = get_latest_server_jar_url()
                if not url:
                    self.log_server("Failed to get server.jar URL.")
                    return

                self.log_server(f"Downloading server.jar from {url}...")
                with urllib.request.urlopen(url) as response, open(jar_path, "wb") as out_file:
                    shutil.copyfileobj(response, out_file)

                self.log_server("Download complete.")
            except Exception as e:
                self.log_server(f"Download error: {e}")

        threading.Thread(target=download, daemon=True).start()

    def start_server(self):
        if self.server_process:
            self.log_server("Server already running.")
            return

        jar_path = os.path.join(self.server_dir, "server.jar")
        if not os.path.exists(jar_path):
            messagebox.showwarning("Warning", "server.jar not found. Download it first.")
            return

        def run_server():
            self.enable_server_buttons(True)
            try:
                self.server_process = subprocess.Popen(
                    ["java", "-jar", "server.jar", "nogui"],
                    cwd=self.server_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                self.log_server("Server started.")

                player_join_pattern = re.compile(r'\[Server thread/INFO\]: (.+?) joined the game')

                for line in self.server_process.stdout:
                    self.log_server(line.strip())
                    match = player_join_pattern.search(line)
                    if match:
                        player = match.group(1)
                        grant_op(self.server_dir, player)
                        self.log_server(f"Granted OP to player {player}")

                self.log_server("Server process ended.")
            except Exception as e:
                self.log_server(f"Server error: {e}")
            finally:
                self.server_process = None
                self.enable_server_buttons(False)

        threading.Thread(target=run_server, daemon=True).start()

    def stop_server_process(self):
        if self.server_process:
            try:
                self.server_process.stdin.write("stop\n")
                self.server_process.stdin.flush()
                self.log_server("Sent stop command to server.")
            except Exception as e:
                self.log_server(f"Error stopping server: {e}")

    def enable_server_buttons(self, started):
        self.start_server_button.config(state=tk.DISABLED if started else tk.NORMAL)
        self.stop_server_button.config(state=tk.NORMAL if started else tk.DISABLED)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def log_server(self, message):
        self.server_log_text.config(state=tk.NORMAL)
        self.server_log_text.insert(tk.END, message + "\n")
        self.server_log_text.see(tk.END)
        self.server_log_text.config(state=tk.DISABLED)

    def apply_theme(self):
        pass

def fetch_minecraft_versions(minecraft_dir):
    """Fetch available Minecraft versions from Mojang manifest."""
    try:
        manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        with urllib.request.urlopen(manifest_url) as resp:
            data = json.loads(resp.read())
        return data.get("versions", [])
    except Exception as e:
        print(f"Failed to fetch Minecraft versions: {e}")
        return []


if __name__ == "__main__":
    if LAUNCHER_SECRET_TOKEN == "¨":
        LAUNCHER_SECRET_TOKEN = generate_secret_token()
    app = MinecraftLauncher()
    app.mainloop()
