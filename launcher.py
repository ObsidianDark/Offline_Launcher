import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import minecraft_launcher_lib
import subprocess
import threading
import os
import json
import minecraft_launcher_lib.install as m_install
import urllib.request

from PIL import ImageTk, Image
from minecraft_launcher_lib import command

def install_version(version_id, minecraft_dir):
    try:
        print(f"Installing version {version_id}...")
        callback = minecraft_launcher_lib.install.install_minecraft_version(
            version_id, minecraft_dir)
        print("Installation complete.")
        return True
    except Exception as e:
        print(f"Failed to install version {version_id}: {e}")
        return False

def fetch_minecraft_versions(minecraft_dir):
    try:
        mirror_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        print("Requesting version manifest from:", mirror_url)

        with urllib.request.urlopen(mirror_url) as response:
            data = response.read()
            manifest = json.loads(data)
            versions = manifest.get("versions", [])
            print(f"Loaded {len(versions)} versions.")
            return versions
    except Exception as e:
        print("Failed to load version manifest:", e)
        return []



CONFIG_FILE = "launcher_config.json"

class AccountDialog(tk.Toplevel):
    def __init__(self, parent, title=None, initial=None):
        super().__init__(parent)

        try:
            icon_path_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
            self.iconbitmap(icon_path_ico)
        except Exception as e:
            print("iconbitmap error:", e)

        try:
            icon_path_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            img = Image.open(icon_path_png)
            photo = ImageTk.PhotoImage(img)
            self.iconphoto(False, photo)
        except Exception as e:
            print("iconphoto error:", e)

        self.result = None
        self.title(title or "Account")
        self.username_var = tk.StringVar(value=initial.get("username") if initial else "")
        self.mode_var = tk.StringVar(value=initial.get("mode") if initial else "offline")
        self.token_var = tk.StringVar(value=initial.get("token") if initial else "")
        self.skin_var = tk.StringVar(value=initial.get("skin") if initial else "")

        # Username
        ttk.Label(self, text="Username:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(self, textvariable=self.username_var).grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        # Mode
        ttk.Label(self, text="Mode:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        mode_combo = ttk.Combobox(self, textvariable=self.mode_var, values=["offline", "online"], state="readonly")
        mode_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)

        # Token
        ttk.Label(self, text="Token (online only):").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.token_entry = ttk.Entry(self, textvariable=self.token_var)
        self.token_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        # Skin File
        ttk.Label(self, text="Skin System Beta (MAY NOT WORK):").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.skin_entry = ttk.Entry(self, textvariable=self.skin_var)
        self.skin_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        self.skin_browse_btn = ttk.Button(self, text="Browse...", command=self.browse_skin)
        self.skin_browse_btn.grid(row=3, column=2, sticky="ew", pady=5, padx=5)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

        self.columnconfigure(1, weight=1)

        self.on_mode_change()
        self.grab_set()
        self.wait_window(self)

    def browse_skin(self):
        file_path = filedialog.askopenfilename(
            title="Select Skin Image",
            filetypes=[("PNG Images", "*.png")],
        )
        if file_path:
            self.skin_var.set(file_path)

    def on_mode_change(self, event=None):
        if self.mode_var.get() == "offline":
            self.token_entry.config(state="disabled")
            self.token_var.set("")
        else:
            self.token_entry.config(state="normal")

    def on_ok(self):
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return
        mode = self.mode_var.get()
        token = self.token_var.get().strip() if mode == "online" else None
        skin = self.skin_var.get().strip() or None

        self.result = {
            "username": username,
            "mode": mode,
            "token": token,
            "skin": skin
        }
        self.destroy()


class MinecraftLauncher(tk.Tk):
    def __init__(self):
        super().__init__()

        try:
            icon_path_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
            self.iconbitmap(icon_path_ico)
        except Exception as e:
            print("iconbitmap error:", e)

        try:
            icon_path_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            img = Image.open(icon_path_png)
            photo = ImageTk.PhotoImage(img)
            self.iconphoto(False, photo)
        except Exception as e:
            print("iconphoto error:", e)

        self.title("Advanced Offline Minecraft Launcher")
        self.geometry("700x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.minecraft_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = self.load_config()
        self.profiles = self.config.get("profiles", {})
        self.accounts = self.config.get("accounts", {})  # new accounts dictionary
        self.history = self.config.get("history", [])
        self.dark_mode = self.config.get("dark_mode", False)

        self.create_widgets()   # Creates notebook, tabs, and widgets
        self.apply_theme()      # Apply dark or light theme
        self.load_versions()    # Fetch Minecraft versions and populate combo box
        self.load_profile(self.config.get("last_profile", None))  # Load last used profile if exists
        self.refresh_account_list()  # Populate accounts listbox and combo box

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Tabs
        self.launch_frame = ttk.Frame(self.notebook)
        self.profiles_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)
        self.log_frame = ttk.Frame(self.notebook)
        self.accounts_frame = ttk.Frame(self.notebook)  # new

        self.notebook.add(self.launch_frame, text="Launch")
        self.notebook.add(self.profiles_frame, text="Profiles")
        self.notebook.add(self.accounts_frame, text="Accounts")  # new tab
        self.notebook.add(self.settings_frame, text="Settings")
        self.notebook.add(self.log_frame, text="Console Log")

        self.create_launch_tab()
        self.create_profiles_tab()
        self.create_accounts_tab()  # new
        self.create_settings_tab()
        self.create_log_tab()

    # === Launch Tab ===
    def create_launch_tab(self):
        frame = self.launch_frame

        row = 0
        ttk.Label(frame, text="Profile:", font=("Arial", 11)).grid(row=row, column=0, sticky="w", pady=4)
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(frame, textvariable=self.profile_var, state="readonly")
        self.profile_combo.grid(row=row, column=1, sticky="ew", pady=4)
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_select)

        row += 1
        # Account selector dropdown (new)
        ttk.Label(frame, text="Account:", font=("Arial", 11)).grid(row=row, column=0, sticky="w", pady=4)
        self.account_var = tk.StringVar()
        self.account_combo = ttk.Combobox(frame, textvariable=self.account_var, state="readonly")
        self.account_combo.grid(row=row, column=1, sticky="ew", pady=4)
        self.account_combo.bind("<<ComboboxSelected>>", self.on_account_select)

        row += 1
        ttk.Label(frame, text="Username (manual):", font=("Arial", 11)).grid(row=row, column=0, sticky="w", pady=4)
        self.username_entry = ttk.Entry(frame)
        self.username_entry.grid(row=row, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="(Used if no account selected)", font=("Arial", 8)).grid(row=row, column=2, sticky="w", pady=4)

        row += 1
        ttk.Label(frame, text="Minecraft Version:", font=("Arial", 11)).grid(row=row, column=0, sticky="w", pady=4)
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(frame, textvariable=self.version_var, state="readonly")
        self.version_combo.grid(row=row, column=1, sticky="ew", pady=4)

        row += 1
        ttk.Label(frame, text="Max RAM (GB):", font=("Arial", 11)).grid(row=row, column=0, sticky="w", pady=4)
        self.ram_entry = ttk.Entry(frame)
        self.ram_entry.grid(row=row, column=1, sticky="ew", pady=4)

        row += 1
        ttk.Label(frame, text="Extra JVM Args:", font=("Arial", 11)).grid(row=row, column=0, sticky="w", pady=4)
        self.jvm_args_entry = ttk.Entry(frame)
        self.jvm_args_entry.grid(row=row, column=1, sticky="ew", pady=4)

        row += 1
        self.fullscreen_var = tk.BooleanVar()
        self.fullscreen_check = ttk.Checkbutton(frame, text="Fullscreen", variable=self.fullscreen_var)
        self.fullscreen_check.grid(row=row, column=1, sticky="w", pady=4)

        row += 1
        ttk.Label(frame, text="Window Width:", font=("Arial", 11)).grid(row=row, column=0, sticky="w", pady=4)
        self.width_entry = ttk.Entry(frame)
        self.width_entry.grid(row=row, column=1, sticky="ew", pady=4)

        row += 1
        ttk.Label(frame, text="Window Height:", font=("Arial", 11)).grid(row=row, column=0, sticky="w", pady=4)
        self.height_entry = ttk.Entry(frame)
        self.height_entry.grid(row=row, column=1, sticky="ew", pady=4)

        row += 1
        self.launch_button = ttk.Button(frame, text="Launch Minecraft", command=self.launch_minecraft)
        self.launch_button.grid(row=row, column=0, columnspan=2, pady=10)

        for i in range(3):
            frame.columnconfigure(i, weight=1)

    # === Accounts Tab ===
    def create_accounts_tab(self):
        frame = self.accounts_frame

        self.account_listbox = tk.Listbox(frame)
        self.account_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.account_listbox.bind("<<ListboxSelect>>", self.on_account_list_select)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        ttk.Button(btn_frame, text="Add Account", command=self.add_account).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Edit Account", command=self.edit_account).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Delete Account", command=self.delete_account).pack(fill=tk.X, pady=2)

        self.refresh_account_list()

    def refresh_account_list(self):
        self.account_listbox.delete(0, tk.END)
        accounts_sorted = sorted(self.accounts.keys())
        for acc in accounts_sorted:
            mode = self.accounts[acc].get("mode", "offline")
            self.account_listbox.insert(tk.END, f"{acc} [{mode}]")

        # Update launch tab account combo too
        self.account_combo['values'] = accounts_sorted
        if self.account_var.get() not in accounts_sorted:
            self.account_var.set('')

    def add_account(self):
        dialog = AccountDialog(self, title="Add Account")
        if dialog.result:
            uname = dialog.result["username"]
            if uname in self.accounts:
                messagebox.showerror("Error", "Account with that username already exists.")
                return
            self.accounts[uname] = dialog.result
            self.save_config()
            self.refresh_account_list()

    def edit_account(self):
        sel = self.account_listbox.curselection()
        if not sel:
            messagebox.showinfo("Edit Account", "Please select an account to edit.")
            return
        item = self.account_listbox.get(sel[0])
        acc_name = item.split()[0]
        if acc_name not in self.accounts:
            return
        dialog = AccountDialog(self, title="Edit Account", initial=self.accounts[acc_name])
        if dialog.result:
            self.accounts[acc_name] = dialog.result
            self.save_config()
            self.refresh_account_list()

    def delete_account(self):
        sel = self.account_listbox.curselection()
        if not sel:
            messagebox.showinfo("Delete Account", "Please select an account to delete.")
            return
        item = self.account_listbox.get(sel[0])
        acc_name = item.split()[0]
        if messagebox.askyesno("Delete Account", f"Delete account '{acc_name}'?"):
            self.accounts.pop(acc_name, None)
            self.save_config()
            self.refresh_account_list()

    def on_account_list_select(self, event):
        sel = self.account_listbox.curselection()
        if sel:
            item = self.account_listbox.get(sel[0])
            acc_name = item.split()[0]
            self.account_var.set(acc_name)
            # Optional: autofill username entry with this account's username
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, acc_name)

    def on_account_select(self, event):
        # When account selected in launch tab combo, autofill username entry
        acc_name = self.account_var.get()
        if acc_name in self.accounts:
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, acc_name)

    # === Profiles Tab ===
    def create_profiles_tab(self):
        frame = self.profiles_frame

        self.profile_listbox = tk.Listbox(frame)
        self.profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.profile_listbox.bind("<<ListboxSelect>>", self.on_profile_list_select)

        button_frame = ttk.Frame(frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        self.btn_new_profile = ttk.Button(button_frame, text="New Profile", command=self.new_profile)
        self.btn_new_profile.pack(fill=tk.X, pady=2)
        self.btn_edit_profile = ttk.Button(button_frame, text="Edit Profile", command=self.edit_profile)
        self.btn_edit_profile.pack(fill=tk.X, pady=2)
        self.btn_delete_profile = ttk.Button(button_frame, text="Delete Profile", command=self.delete_profile)
        self.btn_delete_profile.pack(fill=tk.X, pady=2)
        self.btn_save_profile = ttk.Button(button_frame, text="Save Profile", command=self.save_current_profile)
        self.btn_save_profile.pack(fill=tk.X, pady=2)

        self.refresh_profile_list()

    # === Settings Tab ===
    def create_settings_tab(self):
        frame = self.settings_frame
        self.theme_var = tk.StringVar(value="Dark" if self.dark_mode else "Light")

        ttk.Label(frame, text="Theme:", font=("Arial", 12)).pack(anchor="w", pady=5, padx=10)
        theme_frame = ttk.Frame(frame)
        theme_frame.pack(anchor="w", padx=10)

        ttk.Radiobutton(theme_frame, text="Light", variable=self.theme_var, value="Light", command=self.on_theme_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(theme_frame, text="Dark", variable=self.theme_var, value="Dark", command=self.on_theme_change).pack(side=tk.LEFT, padx=5)

        ttk.Label(frame, text="Minecraft Directory:", font=("Arial", 12)).pack(anchor="w", pady=10, padx=10)
        dir_frame = ttk.Frame(frame)
        dir_frame.pack(anchor="w", padx=10, fill=tk.X)

        self.mc_dir_var = tk.StringVar(value=self.minecraft_dir)
        self.mc_dir_entry = ttk.Entry(dir_frame, textvariable=self.mc_dir_var)
        self.mc_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_browse = ttk.Button(dir_frame, text="Browse...", command=self.browse_mc_dir)
        self.btn_browse.pack(side=tk.LEFT, padx=5)

        self.btn_refresh_versions = ttk.Button(frame, text="Refresh Versions", command=self.load_versions)
        self.btn_refresh_versions.pack(pady=10)

    # === Console Log Tab ===
    def create_log_tab(self):
        frame = self.log_frame
        self.log_text = tk.Text(frame, state=tk.DISABLED, wrap=tk.NONE)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        xscroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.log_text.xview)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)


    # === Launch Methods ===
    def on_profile_select(self, event):
        profile_name = self.profile_var.get()
        if profile_name in self.profiles:
            self.load_profile(profile_name)

    def refresh_profile_list(self):
        self.profile_listbox.delete(0, tk.END)
        for profile_name in sorted(self.profiles.keys()):
            self.profile_listbox.insert(tk.END, profile_name)

    def on_profile_list_select(self, event):
        sel = self.profile_listbox.curselection()
        if not sel:
            return
        profile_name = self.profile_listbox.get(sel[0])
        self.load_profile(profile_name)
        self.notebook.select(self.launch_frame)
        self.profile_var.set(profile_name)

    def new_profile(self):
        new_name = f"Profile{len(self.profiles)+1}"
        while new_name in self.profiles:
            new_name += "_1"
        self.profiles[new_name] = {
            "username": "",
            "version": self.version_var.get(),
            "ram_gb": 2,
            "extra_jvm_args": "",
            "fullscreen": False,
            "width": 854,
            "height": 480,
        }
        self.refresh_profile_list()
        self.profile_listbox.selection_clear(0, tk.END)
        self.profile_listbox.selection_set(tk.END)
        self.load_profile(new_name)

    def edit_profile(self):
        sel = self.profile_listbox.curselection()
        if not sel:
            messagebox.showinfo("Edit Profile", "Please select a profile to edit.")
            return
        profile_name = self.profile_listbox.get(sel[0])
        self.load_profile(profile_name)
        self.notebook.select(self.launch_frame)
        self.profile_var.set(profile_name)

    def delete_profile(self):
        sel = self.profile_listbox.curselection()
        if not sel:
            messagebox.showinfo("Delete Profile", "Please select a profile to delete.")
            return
        profile_name = self.profile_listbox.get(sel[0])
        if messagebox.askyesno("Delete Profile", f"Are you sure you want to delete profile '{profile_name}'?"):
            self.profiles.pop(profile_name, None)
            self.refresh_profile_list()
            if self.profile_var.get() == profile_name:
                self.profile_var.set("")
                self.clear_launch_fields()

    def clear_launch_fields(self):
        self.username_entry.delete(0, tk.END)
        self.version_var.set("")
        self.ram_entry.delete(0, tk.END)
        self.jvm_args_entry.delete(0, tk.END)
        self.fullscreen_var.set(False)
        self.width_entry.delete(0, tk.END)
        self.height_entry.delete(0, tk.END)

    def load_profile(self, profile_name):
        if not profile_name or profile_name not in self.profiles:
            self.clear_launch_fields()
            return
        profile = self.profiles[profile_name]
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, profile.get("username", ""))
        self.version_var.set(profile.get("version", ""))
        self.ram_entry.delete(0, tk.END)
        self.ram_entry.insert(0, str(profile.get("ram_gb", 2)))
        self.jvm_args_entry.delete(0, tk.END)
        self.jvm_args_entry.insert(0, profile.get("extra_jvm_args", ""))
        self.fullscreen_var.set(profile.get("fullscreen", False))
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(profile.get("width", 854)))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(profile.get("height", 480)))

    def save_current_profile(self):
        profile_name = self.profile_var.get()
        if not profile_name:
            messagebox.showerror("Error", "No profile selected to save.")
            return
        self.profiles[profile_name] = {
            "username": self.username_entry.get().strip(),
            "version": self.version_var.get(),
            "ram_gb": int(self.ram_entry.get() or 2),
            "extra_jvm_args": self.jvm_args_entry.get(),
            "fullscreen": self.fullscreen_var.get(),
            "width": int(self.width_entry.get() or 854),
            "height": int(self.height_entry.get() or 480),
        }
        self.save_config()
        self.refresh_profile_list()
        messagebox.showinfo("Success", f"Profile '{profile_name}' saved.")

    def browse_mc_dir(self):
        selected_dir = filedialog.askdirectory(title="Select Minecraft Directory", initialdir=self.minecraft_dir)
        if selected_dir:
            self.minecraft_dir = selected_dir
            self.mc_dir_var.set(selected_dir)
            self.save_config()
            self.load_versions()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config: {e}")
        return {}

    def save_config(self):
        self.config["profiles"] = self.profiles
        self.config["accounts"] = self.accounts
        self.config["history"] = self.history
        self.config["dark_mode"] = self.dark_mode
        self.config["last_profile"] = self.profile_var.get()
        self.config["minecraft_dir"] = self.minecraft_dir
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def load_versions(self):
        try:
            self.versions = fetch_minecraft_versions(self.minecraft_dir)
            print("Fetched versions:", self.versions)  # Debug output

            versions_list = [v["id"] for v in self.versions]
            print("Available version IDs:", versions_list)  # Debug output

            self.version_combo['values'] = versions_list

            if versions_list:
                self.version_var.set(versions_list[-1])  # Default to latest
            else:
                messagebox.showerror("Error", "No versions found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load versions: {e}")

    def launch_minecraft(self):
        self.log("Launch button pressed.")
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return

        version = self.version_var.get()
        if not version:
            messagebox.showerror("Error", "Please select a Minecraft version.")
            return

        try:
            ram_gb = int(self.ram_entry.get())
        except ValueError:
            ram_gb = 2

        jvm_args = self.jvm_args_entry.get().strip()
        fullscreen = self.fullscreen_var.get()
        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
        except ValueError:
            width, height = 854, 480

        account_name = self.account_var.get()
        account_data = self.accounts.get(account_name, None)

        mode = "offline"
        token = None
        if account_data:
            mode = account_data.get("mode", "offline")
            token = account_data.get("token", None)

        if mode == "online" and not token:
            messagebox.showerror("Error", "Online mode selected but no token found.")
            return

        if mode == "online" and token:
            auth = {
                "username": username,
                "access_token": token,
            }
        else:
            auth = {
                "username": username,
                "access_token": "None",
            }

        java_args = ["-Xmx{}G".format(ram_gb)]
        if jvm_args:
            java_args += jvm_args.split()

        def launch_thread():
            self.log("launch_thread started")

            try:
                version_path = os.path.join(self.minecraft_dir, "versions", version)
                self.log(f"Checking if version path exists: {version_path}")

                if not os.path.exists(version_path):
                    self.log(f"Version {version} not installed. Installing now...")
                    callback = minecraft_launcher_lib.install.install_minecraft_version(version, self.minecraft_dir)

                    if callback is None:
                        self.log(f"Install function returned None, assuming install started or completed instantly.")
                    else:
                        start_time = time.time()
                        while not callback():
                            self.log("Installing... waiting...")
                            time.sleep(0.5)
                            if time.time() - start_time > 300:
                                self.log("Installation timeout after 5 minutes.")
                                messagebox.showerror("Error", "Minecraft version installation timed out.")
                                return

                    self.log(f"Version {version} installed successfully.")
                else:
                    self.log(f"Version {version} already installed.")

                self.log(f"Launching Minecraft {version} as {username} ({mode} mode)...")

                options_dict = {
                    "minecraft_directory": self.minecraft_dir,
                    "username": username,
                    "uuid": "Not-Assigned-Yet",
                    "token": "Not-Assigned-Yet",
                    "launcher_name": "AdvancedLauncher",
                    "launcher_version": "1.0",
                    "java_args": java_args,
                    "fullscreen": fullscreen,
                    "width": width,
                    "height": height,
                }

                command = minecraft_launcher_lib.command.get_minecraft_command(version, self.minecraft_dir, options=options_dict)
                self.log(f"Running command: {' '.join(command)}")

                proc = subprocess.Popen(command, cwd=self.minecraft_dir, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout:
                    self.log(line.strip())

                proc.wait()
                self.log("Minecraft process ended.")

            except Exception as e:
                self.log(f"Failed to launch Minecraft: {e}")

        threading.Thread(target=launch_thread, daemon=True).start()

    def log(self, message):
        def append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        self.after(0, append)

    def on_theme_change(self):
        selected = self.theme_var.get()
        self.dark_mode = selected == "Dark"
        self.apply_theme()
        self.save_config()

    def apply_theme(self):
        if self.dark_mode:
            bg_color = "#2e2e2e"
            fg_color = "#ffffff"
        else:
            bg_color = "#f0f0f0"
            fg_color = "#000000"

        style = ttk.Style()
        style.theme_use('default')

        style.configure('.', background=bg_color, foreground=fg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TFrame', background=bg_color)
        style.configure('TButton', background=bg_color)
        style.configure('TCheckbutton', background=bg_color)
        style.configure('TEntry', fieldbackground="#4d4d4d" if self.dark_mode else "white", foreground=fg_color)
        style.configure('TCombobox', fieldbackground="#4d4d4d" if self.dark_mode else "white", foreground=fg_color)

        self.configure(bg=bg_color)

    def on_close(self):
        self.save_config()
        self.destroy()


if __name__ == "__main__":
    app = MinecraftLauncher()
    app.mainloop()

