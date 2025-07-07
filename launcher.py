import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import minecraft_launcher_lib
import subprocess
import threading
import os
import json
import urllib.request

CONFIG_FILE = "launcher_config.json"

class AccountDialog(tk.Toplevel):
    def __init__(self, parent, title=None, initial=None):
        super().__init__(parent)
        self.result = None
        self.title(title or "Account")

        self.username_var = tk.StringVar(value=initial.get("username") if initial else "")
        self.mode_var = tk.StringVar(value=initial.get("mode") if initial else "offline")
        self.token_var = tk.StringVar(value=initial.get("token") if initial else "")

        ttk.Label(self, text="Username:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(self, textvariable=self.username_var).grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        ttk.Label(self, text="Mode:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        mode_combo = ttk.Combobox(self, textvariable=self.mode_var, values=["offline", "online"], state="readonly")
        mode_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)

        ttk.Label(self, text="Token (online only):").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.token_entry = ttk.Entry(self, textvariable=self.token_var)
        self.token_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

        self.columnconfigure(1, weight=1)

        self.on_mode_change()
        self.grab_set()
        self.wait_window(self)

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
        self.result = {"username": username, "mode": mode, "token": token}
        self.destroy()

class MinecraftLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Offline Minecraft Launcher")
        self.geometry("700x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.minecraft_dir = os.path.abspath(".")
        self.config = self.load_config()
        self.profiles = self.config.get("profiles", {})
        self.accounts = self.config.get("accounts", {})  # new
        self.history = self.config.get("history", [])
        self.dark_mode = self.config.get("dark_mode", False)

        self.create_widgets()
        self.apply_theme()
        self.load_versions()
        self.load_profile(self.config.get("last_profile", None))
        self.refresh_account_list()

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
        self.account_var.set("")

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
        # Determine username & token from selected account or manual input
        account_name = self.account_var.get()
        username = None
        token = None
        mode = "offline"

        if account_name and account_name in self.accounts:
            acc = self.accounts[account_name]
            username = acc.get("username")
            mode = acc.get("mode", "offline")
            token = acc.get("token", None)
        else:
            # fallback to manual username entry
            username = self.username_entry.get().strip()

        if not username:
            messagebox.showerror("Error", "Please enter a username or select an account.")
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

        self.add_to_history(username, version)

        self.append_log(f"Launching Minecraft {version} as '{username}' ({mode})...\n")
        self.launch_button.config(state=tk.DISABLED)
        threading.Thread(target=self._launch_minecraft_thread,
                         args=(username, version, ram_gb, extra_jvm, fullscreen, width, height, mode, token), daemon=True).start()

    def _launch_minecraft_thread(self, username, version, ram_gb, extra_jvm, fullscreen, width, height, mode, token):
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

            if mode == "online" and token:
                options["uuid"] = "online-uuid"  # Optionally set real UUID here if you have it
                options["token"] = token

            launch_command = minecraft_launcher_lib.command.get_minecraft_command(
                version,
                self.minecraft_dir,
                options
            )

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
        self.config['accounts'] = self.accounts
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

def get_versions(minecraft_dir):
    versions_folder = os.path.join(minecraft_dir, "versions")
    if os.path.exists(versions_folder):
        return sorted([v for v in os.listdir(versions_folder) if os.path.isdir(os.path.join(versions_folder, v))])
    return []

if __name__ == "__main__":
    app = MinecraftLauncher()
    app.mainloop()
