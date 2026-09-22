import tkinter as tk
from tkinter import scrolledtext
import json, os, subprocess, threading, time, random

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(APP_DIR, "memory.json")
DEFAULT_MEMORY = {"name":"Mika","sessions":0,"messages":0,"timers":0}

try:
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = {**DEFAULT_MEMORY, **json.load(f)}
except Exception:
    memory = DEFAULT_MEMORY.copy()

memory["sessions"] += 1

def save():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

save()

class Mika:
    def __init__(self, root):
        self.root = root
        root.title("Mika — Desktop Companion")
        root.geometry("390x560")
        root.minsize(350, 500)
        root.attributes("-topmost", True)
        root.configure(bg="#10131c")

        top = tk.Frame(root, bg="#171b28")
        top.pack(fill="x")
        tk.Label(top, text="MIKA", fg="#b9c9ff", bg="#171b28",
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=12, pady=8)
        tk.Button(top, text="×", command=root.destroy, bg="#171b28",
                  fg="white", bd=0, font=("Segoe UI", 14)).pack(side="right", padx=8)

        self.avatar = tk.Label(root, text="◕‿◕", fg="#dce8ff", bg="#202638",
                               font=("Segoe UI", 42, "bold"), width=9, height=2)
        self.avatar.pack(pady=(14, 3))

        self.mood = tk.StringVar(value="HAPPY")
        self.status = tk.StringVar(value="Je suis là. Essaie de me surprendre.")
        tk.Label(root, textvariable=self.mood, fg="#8ea8ff", bg="#10131c",
                 font=("Segoe UI", 9, "bold")).pack()
        tk.Label(root, textvariable=self.status, fg="#aeb5c7", bg="#10131c",
                 wraplength=340, font=("Segoe UI", 9)).pack(pady=(2, 10))

        self.chat = scrolledtext.ScrolledText(
            root, wrap="word", height=13, bg="#171b28", fg="#edf1ff",
            insertbackground="white", relief="flat", font=("Segoe UI", 10)
        )
        self.chat.pack(fill="both", expand=True, padx=12)
        self.chat.insert("end", "Mika: T'es enfin là. 🙄\n\n")
        self.chat.configure(state="disabled")

        bottom = tk.Frame(root, bg="#10131c")
        bottom.pack(fill="x", padx=12, pady=10)
        self.entry = tk.Entry(bottom, bg="#202638", fg="white",
                               insertbackground="white", relief="flat",
                               font=("Segoe UI", 10))
        self.entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.entry.bind("<Return>", lambda e: self.send())

        tk.Button(bottom, text="Envoyer", command=self.send, bg="#718cff",
                  fg="white", bd=0, font=("Segoe UI", 9, "bold"),
                  padx=10).pack(side="right", padx=(7, 0))

        controls = tk.Frame(root, bg="#10131c")
        controls.pack(fill="x", padx=12, pady=(0, 12))
        buttons = [
            ("🎮 Minecraft", lambda: self.game("Minecraft")),
            ("🎯 Valorant", lambda: self.game("Valorant")),
            ("📝 Notes", lambda: subprocess.Popen(["notepad.exe"])),
            ("⏱ 5 min", lambda: self.timer(5)),
            ("📊 Stats", self.stats)
        ]
        for label, cmd in buttons:
            tk.Button(controls, text=label, command=cmd, bg="#202638",
                      fg="#dfe6ff", bd=0, padx=6, pady=6).pack(side="left", padx=2)

    def say(self, who, msg):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}: {msg}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def moodset(self, mood):
        faces = {
            "happy": ("◕‿◕", "HAPPY"),
            "annoyed": ("ಠ_ಠ", "ANNOYED"),
            "surprised": ("⊙_⊙", "SURPRISED"),
            "shy": ("⁄⁄•⁄ω⁄•⁄⁄", "SHY"),
            "sleepy": ("－_－", "SLEEPY"),
            "hype": ("ᕙ(🔥‿🔥)ᕗ", "HYPE")
        }
        face, label = faces.get(mood, faces["happy"])
        self.avatar.config(text=face)
        self.mood.set(label)

    def answer(self, msg):
        m = msg.lower()

        if any(x in m for x in ["salut", "yo", "hey", "bonjour"]):
            self.moodset("happy")
            return random.choice(["Yo 😌", "Enfin. J'attendais.", "Salut toi. 👀"])

        if "minecraft" in m:
            self.moodset("hype")
            return "Minecraft ? Vas-y, montre-moi ton PvP. 😏"

        if "valorant" in m or "valo" in m:
            self.moodset("hype")
            return "Encore du ranked ? Respire avant de spray, champion. 🎯"

        if any(x in m for x in ["merci", "thank"]):
            self.moodset("shy")
            return "Ouais ouais... de rien. 🙄"

        if any(x in m for x in ["fatigue", "fatigué", "fatiguée", "triste"]):
            self.moodset("sleepy")
            return "Pause deux minutes. Même les gamers doivent recharger. 💤"

        if "stats" in m:
            return f"Sessions: {memory['sessions']} | Messages: {memory['messages']} | Timers: {memory['timers']}"

        self.moodset(random.choice(["happy", "happy", "surprised", "shy"]))
        return random.choice([
            "Hmm... intéressant. Continue.",
            "J'écoute. 👀",
            "Tu veux vraiment que je réponde à ça ? 😭",
            "Pas mal. Mais j'ai une meilleure idée."
        ])

    def send(self):
        msg = self.entry.get().strip()
        if not msg:
            return
        self.entry.delete(0, "end")
        memory["messages"] += 1
        save()
        self.say("Toi", msg)
        self.say("Mika", self.answer(msg))
        self.status.set(random.choice([
            "Je te surveille. 👀",
            "T'as besoin de moi ?",
            "Bon... je reste là."
        ]))

    def game(self, name):
        self.moodset("hype")
        self.say("Mika", f"{name} détecté dans mon cerveau. 🎮 Lance-le pour l'instant 😭")

    def timer(self, mins):
        memory["timers"] += 1
        save()
        self.say("Mika", f"Timer de {mins} minutes lancé.")

        def wait():
            time.sleep(mins * 60)
            self.root.after(0, lambda: self.say("Mika", "⏰ Temps écoulé !"))
            self.root.after(0, lambda: self.moodset("surprised"))

        threading.Thread(target=wait, daemon=True).start()

    def stats(self):
        self.say("Mika", f"📊 Sessions: {memory['sessions']} | Messages: {memory['messages']} | Timers: {memory['timers']}")

root = tk.Tk()
Mika(root)
root.mainloop()
