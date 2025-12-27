import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import Calendar
from datetime import datetime, timedelta
import json, os, threading, time
from playsound import playsound

# ---------------- CONFIG ----------------
BIRTHDAY_FILE = "birthdays.json"
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "reminder_time": "23:58",
    "sound_path": ""
}

alarm_running = False
triggered_today = set()

# ---------------- DATA LAYER ----------------
def load_json(file, default):
    if not os.path.exists(file):
        save_json(file, default)
        return default

    try:
        with open(file, "r") as f:
            data = json.load(f)
        return data if isinstance(data, type(default)) else default
    except:
        return default


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


birthdays = load_json(BIRTHDAY_FILE, [])
settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)

# Ensure settings schema
if not isinstance(settings, dict):
    settings = DEFAULT_SETTINGS
    save_json(SETTINGS_FILE, settings)

# ---------------- ALARM LOGIC ----------------
def play_sound():
    global alarm_running
    if not settings["sound_path"]:
        return

    while alarm_running:
        try:
            playsound(settings["sound_path"])
        except:
            break
        time.sleep(1)


def trigger_alarm(name):
    global alarm_running
    alarm_running = True
    threading.Thread(target=play_sound, daemon=True).start()

    messagebox.showinfo(
        "🎂 Birthday Reminder",
        f"Tomorrow is {name}'s birthday!"
    )

    alarm_running = False


def background_checker():
    global triggered_today

    while True:
        now = datetime.now().replace(second=0, microsecond=0)

        try:
            hour, minute = map(int, settings["reminder_time"].split(":"))
        except:
            time.sleep(30)
            continue

        for b in birthdays:
            bday = datetime.strptime(b["date"], "%Y-%m-%d")
            reminder = bday.replace(year=now.year) - timedelta(days=1)
            reminder = reminder.replace(hour=hour, minute=minute)

            key = f"{b['name']}-{now.date()}"

            if now == reminder and key not in triggered_today:
                triggered_today.add(key)
                trigger_alarm(b["name"])

        time.sleep(30)

# ---------------- UI ACTIONS ----------------
def add_birthday():
    name = name_entry.get().strip()
    date = calendar.get_date()

    if not name:
        messagebox.showerror("Error", "Please enter a name")
        return

    birthdays.append({"name": name, "date": date})
    save_json(BIRTHDAY_FILE, birthdays)
    refresh_list()
    name_entry.delete(0, tk.END)


def delete_birthday():
    if not listbox.curselection():
        messagebox.showwarning("Select", "Select a birthday to delete")
        return

    index = listbox.curselection()[0]
    birthdays.pop(index)
    save_json(BIRTHDAY_FILE, birthdays)
    refresh_list()


def refresh_list():
    listbox.delete(0, tk.END)
    for b in birthdays:
        listbox.insert(tk.END, f" {b['name']} — {b['date']}")


def update_time():
    value = time_entry.get().strip()

    if not value or ":" not in value:
        messagebox.showerror("Invalid Time", "Use HH:MM format")
        return

    settings["reminder_time"] = value
    save_json(SETTINGS_FILE, settings)
    messagebox.showinfo("Saved", "Reminder time updated")


def choose_sound():
    path = filedialog.askopenfilename(
        title="Choose Alarm Sound",
        filetypes=[("Audio Files", "*.mp3 *.wav")]
    )
    if path:
        settings["sound_path"] = path
        save_json(SETTINGS_FILE, settings)
        sound_label.config(text=os.path.basename(path))

# ---------------- UI ----------------
root = tk.Tk()
root.title("Birthday Reminder")
root.geometry("500x730")
root.configure(bg="#121212")
root.resizable(False, False)

def section(title, row):
    tk.Label(
        root, text=title,
        bg="#121212", fg="#3B9CF7",
        font=("Segoe UI", 13, "bold")
    ).grid(row=row, column=0, columnspan=2, pady=(20, 10))

# Title
tk.Label(
    root, text=" Birthday Reminder",
    bg="#121212", fg="white",
    font=("Segoe UI", 20, "bold")
).grid(row=0, column=0, columnspan=2, pady=20)

# Add Birthday
section("Add Birthday", 1)

tk.Label(root, text="Name", bg="#121212", fg="white").grid(row=2, column=0, sticky="w", padx=30)
name_entry = tk.Entry(root, width=30)
name_entry.grid(row=2, column=1, padx=30)

calendar = Calendar(
    root,
    date_pattern="yyyy-mm-dd",
    background="#1e1e1e",
    foreground="white",
    selectbackground="#00ffcc"
)
calendar.grid(row=3, column=0, columnspan=2, pady=10)

tk.Button(
    root, text="Add Birthday",
    bg="#00ffcc", fg="black",
    width=20,
    command=add_birthday
).grid(row=4, column=0, columnspan=2)

# List
section("Saved Birthdays", 5)

listbox = tk.Listbox(root, width=45, height=7)
listbox.grid(row=6, column=0, columnspan=2, pady=5)

tk.Button(
    root, text="Delete Selected",
    bg="#ff4d4d", fg="white",
    command=delete_birthday
).grid(row=7, column=0, columnspan=2, pady=5)

# Settings
section("Reminder Settings", 8)

tk.Label(root, text="Reminder Time (HH:MM)", bg="#121212", fg="white").grid(row=9, column=0, padx=30, sticky="w")
time_entry = tk.Entry(root, width=10)
time_entry.insert(0, settings["reminder_time"])
time_entry.grid(row=9, column=1, sticky="w")

tk.Button(
    root, text="Save Reminder Time",
    command=update_time
).grid(row=10, column=0, columnspan=2, pady=5)

tk.Button(
    root, text="Choose Alarm Sound",
    command=choose_sound
).grid(row=11, column=0, columnspan=2, pady=5)

sound_label = tk.Label(
    root,
    text=os.path.basename(settings["sound_path"]) if settings["sound_path"] else "No sound selected",
    bg="#121212", fg="gray"
)
sound_label.grid(row=12, column=0, columnspan=2, pady=5)

refresh_list()
threading.Thread(target=background_checker, daemon=True).start()
root.mainloop()
