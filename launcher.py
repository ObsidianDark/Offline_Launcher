import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import minecraft_launcher_lib
import subprocess
import threading
import os
import json
import urllib.request

CONFIG_FILE = "launcher_config.json"

class MinecraftLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Offline Minecraft Launcher")
        self.geometry("700x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.minecraft_dir = os.path.abspath(".")
        self.config = self.load_config()
        self.profiles = self.config.get("profiles", {})
        self.history = self.config.get("history", [])
        self.dark_mode = self.config.get("dark_mode", False)

        self.create_widgets()
        self.apply_theme()
        self.load_versions()
        self.load_profile(self.config.get("last_profile", None))

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Tabs
        self.launch_frame = ttk.Frame(self.notebook)
        self.profiles_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)
        self.log_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.launch_frame, text="Launch")
        self.notebook.add(self.profiles_frame, text="Profiles")
        self.notebook.add(self.settings_frame, text="Settings")
        self.notebook.add(self.log_frame, text="Console Log")

        self.create_launch_tab()
        self.create_profiles_tab()
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
        ttk.Label(frame, text="Username:", font=("Arial", 11)).grid(row=row, column=0, sticky="w", pady=4)
        self.username_entry = ttk.Entry(frame)
        self.username_entry.grid(row=row, column=1, sticky="ew", pady=4)

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

        for i in range(2):
            frame.columnconfigure(i, weight=1)

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

    def save_current_profile(self):
        profile_name = self.profile_var.get()
        if not profile_name:
            messagebox.showerror("Error", "No profile selected.")
            return

        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return

        try:
            ram_gb = int(self.ram_entry.get().strip())
            if ram_gb <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Max RAM must be a positive integer.")
            return

        try:
            width = int(self.width_entry.get().strip())
            height = int(self.height_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Width and Height must be integers.")
            return

        self.profiles[profile_name] = {
            "username": username,
            "version": self.version_var.get(),
            "ram_gb": ram_gb,
            "extra_jvm_args": self.jvm_args_entry.get().strip(),
            "fullscreen": self.fullscreen_var.get(),
            "width": width,
            "height": height,
        }
        self.refresh_profile_list()
        messagebox.showinfo("Saved", f"Profile '{profile_name}' saved.")
        self.save_config()

    def load_profile(self, profile_name):
        profile = self.profiles.get(profile_name)
        if not profile:
            return
        self.profile_var.set(profile_name)
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

    def launch_minecraft(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter a username.")
            return

        version = self.version_var.get()
        try:
            ram_gb = int(self.ram_entry.get().strip())
            if ram_gb <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Max RAM must be a positive integer.")
            return

        extra_jvm = self.jvm_args_entry.get().strip()
        fullscreen = self.fullscreen_var.get()
        try:
            width = int(self.width_entry.get().strip())
            height = int(self.height_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Width and Height must be integers.")
            return

        # Save last used profile data in history
        self.add_to_history(username, version)

        self.append_log(f"Launching Minecraft {version} as '{username}'...\n")
        self.launch_button.config(state=tk.DISABLED)
        threading.Thread(target=self._launch_minecraft_thread,
                         args=(username, version, ram_gb, extra_jvm, fullscreen, width, height), daemon=True).start()

    def _launch_minecraft_thread(self, username, version, ram_gb, extra_jvm, fullscreen, width, height):
        try:
            version_path = os.path.join(self.minecraft_dir, "versions", version)
            if not os.path.exists(version_path):
                self.append_log(f"Version folder missing: {version_path}\n")
                messagebox.showerror("Error", f"Version {version} not found!")
                return

            jvm_args = [f"-Xmx{ram_gb}G"]
            if extra_jvm:
                jvm_args.extend(extra_jvm.split())

            options = {
                "username": username,
                "uuid": "offline-uuid",
                "token": "0",
                "jvm_args": jvm_args,
                "launcher_name": "AdvancedOfflineLauncher",
                "fullscreen": fullscreen,
                "width": width,
                "height": height,
            }

            launch_command = minecraft_launcher_lib.command.get_minecraft_command(
                version,
                self.minecraft_dir,
                options
            )

            # Run the process capturing output
            proc = subprocess.Popen(launch_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

            for line in proc.stdout:
                self.append_log(line)

            proc.wait()
            self.append_log(f"Minecraft exited with code {proc.returncode}\n")

            if proc.returncode == 0:
                messagebox.showinfo("Success", f"Minecraft exited successfully.")
            else:
                messagebox.showerror("Error", f"Minecraft exited with code {proc.returncode}")

        except Exception as e:
            self.append_log(f"Error launching Minecraft: {e}\n")
            messagebox.showerror("Error", f"Failed to launch Minecraft:\n{e}")

        finally:
            self.launch_button.config(state=tk.NORMAL)

    def append_log(self, text):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def add_to_history(self, username, version):
        entry = {"username": username, "version": version}
        if entry in self.history:
            self.history.remove(entry)
        self.history.insert(0, entry)
        if len(self.history) > 20:
            self.history.pop()
        self.config["history"] = self.history
        self.save_config()

    # === Settings methods ===
    def apply_theme(self):
        style = ttk.Style(self)
        if self.theme_var.get() == "Dark":
            self.dark_mode = True
            self.configure(bg="#2E2E2E")
            style.theme_use('clam')
            style.configure('.', background="#2E2E2E", foreground="white", fieldbackground="#454545")
            style.map("TButton", background=[('active', '#5A5A5A')])
        else:
            self.dark_mode = False
            self.configure(bg="#F0F0F0")
            style.theme_use('default')
            style.configure('.', background="#F0F0F0", foreground="black")

    def on_theme_change(self):
        self.apply_theme()
        self.config['dark_mode'] = self.dark_mode
        self.save_config()

    def browse_mc_dir(self):
        selected_dir = filedialog.askdirectory(initialdir=self.minecraft_dir, title="Select Minecraft Directory")
        if selected_dir:
            self.minecraft_dir = selected_dir
            self.mc_dir_var.set(selected_dir)
            self.load_versions()
            self.config['minecraft_dir'] = selected_dir
            self.save_config()

    def load_versions(self):
        versions = get_versions(self.minecraft_dir)
        if not versions:
            messagebox.showerror("Error", f"No Minecraft versions found in '{self.minecraft_dir}/versions'!")
            self.version_combo['values'] = []
            self.version_var.set('')
            return
        self.version_combo['values'] = versions
        if self.version_var.get() not in versions:
            self.version_var.set(versions[0])

    def save_config(self):
        self.config['profiles'] = self.profiles
        self.config['last_profile'] = self.profile_var.get()
        self.config['minecraft_dir'] = self.minecraft_dir
        self.config['dark_mode'] = self.dark_mode
        self.config['history'] = self.history
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def on_close(self):
        self.save_config()
        self.destroy()

    # === Server ===
    def select_manifest(self):
        file_path = filedialog.askopenfilename(
            title="Select Server Manifest JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.server_manifest_path = file_path
            self.append_server_log(f"Selected manifest file: {file_path}\n")

    def create_new_server(self):
        version = self.server_version_var.get().strip()
        manifest = None
        if self.server_manifest_path:
            try:
                with open(self.server_manifest_path, "r") as f:
                    manifest = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load manifest JSON:\n{e}")
                return

        self.append_server_log(f"Creating server version {version}...\n")
        self.create_server_btn.config(state=tk.DISABLED)

        threading.Thread(target=self._create_and_run_server_thread, args=(version, manifest), daemon=True).start()

    def _create_and_run_server_thread(self, version, manifest):
        import server  # Import your server.py module (must be in same folder)

        try:
            # Create server folder
            server_dir = os.path.join(self.minecraft_dir, "servers", f"server_{version.replace('.', '_')}")
            os.makedirs(server_dir, exist_ok=True)

            # Use server.py functionality to setup the server
            s = server.MinecraftServer(version=version, directory=server_dir, manifest=manifest)
            s.setup_server()

            self.append_server_log(f"Server setup complete in: {server_dir}\n")
            self.append_server_log("Starting server...\n")

            # Run the server jar and print output live
            proc = s.run_server_process()

            for line in proc.stdout:
                self.append_server_log(line)

            proc.wait()
            self.append_server_log(f"Server exited with code {proc.returncode}\n")

        except Exception as e:
            self.append_server_log(f"Error running server: {e}\n")

        finally:
            self.create_server_btn.config(state=tk.NORMAL)

    def append_server_log(self, text):
        self.server_log_text.config(state=tk.NORMAL)
        self.server_log_text.insert(tk.END, text)
        self.server_log_text.see(tk.END)
        self.server_log_text.config(state=tk.DISABLED)

def get_versions(minecraft_dir):
    versions_folder = os.path.join(minecraft_dir, "versions")
    if os.path.exists(versions_folder):
        return sorted([v for v in os.listdir(versions_folder) if os.path.isdir(os.path.join(versions_folder, v))])
    return []

if __name__ == "__main__":
    app = MinecraftLauncher()
    app.mainloop()
