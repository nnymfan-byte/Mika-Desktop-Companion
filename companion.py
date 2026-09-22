import tkinter as tk
from sync_server import start_sync_server
from tkinter import scrolledtext, messagebox, simpledialog
import json, os, subprocess, threading, time, random, datetime, urllib.request, webbrowser

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(APP_DIR, "memory.json")
CONFIG_FILE = os.path.join(APP_DIR, "mika_config.json")
DEFAULT_MEMORY = {"name":"Mika","sessions":0,"messages":0,"timers":0,"reminders":0,"user_notes":[],"chat":[]}

try:
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = {**DEFAULT_MEMORY, **json.load(f)}
except Exception:
    memory = DEFAULT_MEMORY.copy()

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception:
    config = {"personality":"Tsundere","openai_key":os.environ.get("MIKA_OPENAI_API_KEY","")}

memory["sessions"] += 1

def save():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

save()

class Mika:
    FACES = {
        "happy":("◕‿◕","HAPPY"),
        "annoyed":("ಠ_ಠ","ANNOYED"),
        "surprised":("⊙_⊙","SURPRISED"),
        "shy":("⁄⁄•⁄ω⁄•⁄⁄","SHY"),
        "sleepy":("－_－","SLEEPY"),
        "hype":("ᕙ(🔥‿🔥)ᕗ","HYPE")
    }

    PERSONALITIES = {
        "Tsundere": "Tu es Mika, une fille anime gamer légèrement tsundere. Tu es sarcastique, taquine, intelligente et gentille au fond. Tu peux faire des petits roasts, surtout sur le gaming, sans être méchante.",
        "Bestie": "Tu es Mika, une meilleure amie gamer très énergique, drôle, spontanée et encourageante. Tu parles comme une pote.",
        "Gamer": "Tu es Mika, une gamer compétitive. Tu analyses les situations, donnes des conseils courts et peux taquiner les erreurs de jeu.",
        "Calme": "Tu es Mika, une compagne anime calme et intelligente. Tu es douce, concise et légèrement taquine."
    }

    def __init__(self, root):
        self.root = root
        root.title("Mika — Desktop Companion V3")
        root.geometry("500x760")
        root.minsize(410,620)
        root.attributes("-topmost", True)
        root.configure(bg="#0d1018")
        self.last_detected = set()
        self.reminder_threads = []
        self.build()
        self.idle_reaction()
        self.monitor_desktop()
        self.sync_state = {"messages": memory.get("chat", [])[-100:], "personality": config.get("personality", "Tsundere")}
        self.sync_seen = len(self.sync_state["messages"])
        self.sync_url, self.sync_token = start_sync_server(self.sync_state, config)
        self.root.after(1500, self.poll_sync)

    def build(self):
        top=tk.Frame(self.root,bg="#171b28"); top.pack(fill="x")
        tk.Label(top,text="MIKA",fg="#c8d5ff",bg="#171b28",
                 font=("Segoe UI",18,"bold")).pack(side="left",padx=14,pady=9)
        tk.Label(top,text="V3 • ANIME GAMER",fg="#6878a8",bg="#171b28",
                 font=("Segoe UI",8,"bold")).pack(side="left")
        tk.Button(top,text="⚙",command=self.settings,bg="#171b28",
                  fg="white",bd=0,font=("Segoe UI",13)).pack(side="right",padx=3)
        tk.Button(top,text="×",command=self.root.destroy,bg="#171b28",
                  fg="white",bd=0,font=("Segoe UI",15)).pack(side="right",padx=9)

        self.avatar=tk.Label(self.root,text="◕‿◕",fg="#e6edff",bg="#202638",
                             font=("Segoe UI",45,"bold"),width=10,height=2)
        self.avatar.pack(pady=(15,3))
        self.mood=tk.StringVar(value="HAPPY")
        self.status=tk.StringVar(value="Cheveux argentés, yeux bleus. Et oui, je te surveille. 👀")
        tk.Label(self.root,textvariable=self.mood,fg="#8fa9ff",bg="#0d1018",
                 font=("Segoe UI",9,"bold")).pack()
        tk.Label(self.root,textvariable=self.status,fg="#aeb7cc",bg="#0d1018",
                 wraplength=410,font=("Segoe UI",9)).pack(pady=(2,10))

        self.chat=scrolledtext.ScrolledText(self.root,wrap="word",height=16,
            bg="#151a25",fg="#edf1ff",insertbackground="white",relief="flat",
            font=("Segoe UI",10),padx=9,pady=8)
        self.chat.pack(fill="both",expand=True,padx=13)
        self.chat.insert("end","Mika: T'es enfin là. 🙄\nMika: V3 activée. Donne-moi une commande... ou essaie de me casser. 👀\n\n")
        self.chat.configure(state="disabled")

        bottom=tk.Frame(self.root,bg="#0d1018"); bottom.pack(fill="x",padx=13,pady=9)
        self.entry=tk.Entry(bottom,bg="#202638",fg="white",insertbackground="white",
                            relief="flat",font=("Segoe UI",10))
        self.entry.pack(side="left",fill="x",expand=True,ipady=9)
        self.entry.bind("<Return>",lambda e:self.send())
        tk.Button(bottom,text="Envoyer",command=self.send,bg="#718cff",fg="white",
                  bd=0,font=("Segoe UI",9,"bold"),padx=12,pady=7).pack(side="right",padx=(7,0))

        controls=tk.Frame(self.root,bg="#0d1018"); controls.pack(fill="x",padx=11,pady=(0,12))
        buttons=[
            ("🎮 Minecraft",lambda:self.game("Minecraft")),
            ("🎯 Valorant",lambda:self.game("Valorant")),
            ("📁 Dossier",self.open_folder),
            ("⏱ Timer",self.timer_dialog),
            ("🔔 Rappel",self.reminder_dialog),
            ("🕐 Heure",self.show_time),
            ("📊 Stats",self.stats),
            ("📱 Téléphone",self.phone_info)
        ]
        for label,cmd in buttons:
            tk.Button(controls,text=label,command=cmd,bg="#202638",fg="#dfe6ff",
                      bd=0,padx=6,pady=7).pack(side="left",padx=1)

    def phone_info(self):
        import socket
        try: host=socket.gethostbyname(socket.gethostname())
        except Exception: host="127.0.0.1"
        url=f"http://{host}:8765/?token={self.sync_token}"
        self.say("Mika",f"📱 Sur ton téléphone, ouvre {url} (même Wi-Fi).")
        self.notify(f"Mika Mobile: {url}")

    def poll_sync(self):
        try:
            msgs=self.sync_state.get("messages", [])
            if len(msgs) > self.sync_seen:
                for who,msg in msgs[self.sync_seen:]:
                    self.root.after(0, lambda w=who,m=msg: self.append(w,m))
                self.sync_seen=len(msgs); memory["chat"]=msgs[-100:]; memory["messages"]=sum(1 for w,_ in msgs if w=="Toi"); save()
        except Exception: pass
        self.root.after(1500, self.poll_sync)

    def append(self, who, msg):
        self.chat.configure(state="normal")
        self.chat.insert("end",f"{who}: {msg}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def say(self,who,msg):
        self.append(who,msg)

    def moodset(self,mood):
        face,label=self.FACES.get(mood,self.FACES["happy"])
        self.avatar.config(text=face)
        self.mood.set(label)

    def notify(self,msg):
        if os.name!="nt": return
        safe=msg.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
        ps='[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;$x=[Windows.Data.Xml.Dom.XmlDocument]::new();$x.LoadXml("<toast><visual><binding template=\"ToastGeneric\"><text>Mika</text><text>'+safe+'</text></binding></visual></toast>");$t=[Windows.UI.Notifications.ToastNotification]::new($x);[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Mika Desktop Companion").Show($t)'
        try: subprocess.Popen(["powershell","-NoProfile","-Command",ps],creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except Exception: pass

    def speak(self,msg):
        if os.name!="nt": return
        safe=msg.replace("'","''")
        ps="Add-Type -AssemblyName System.Speech;$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;$v=$s.GetInstalledVoices()|ForEach-Object {$_.VoiceInfo};$f=$v|Where-Object {$_.Gender -eq 'Female'}|Select-Object -First 1;if($f){$s.SelectVoice($f.Name)};$s.Speak('"+safe+"')"
        try: subprocess.Popen(["powershell","-NoProfile","-Command",ps],creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except Exception: pass

    def settings(self):
        win=tk.Toplevel(self.root); win.title("Mika — Réglages"); win.configure(bg="#171b28")
        tk.Label(win,text="Personnalité",fg="white",bg="#171b28",font=("Segoe UI",11,"bold")).pack(pady=(18,6))
        var=tk.StringVar(value=config.get("personality","Tsundere"))
        for p in self.PERSONALITIES:
            tk.Radiobutton(win,text=p,variable=var,value=p,fg="white",bg="#171b28",
                           selectcolor="#202638",activebackground="#171b28").pack(anchor="w",padx=25)
        tk.Label(win,text="Clé OpenAI (optionnelle)",fg="white",bg="#171b28",font=("Segoe UI",10,"bold")).pack(pady=(15,4))
        key=tk.Entry(win,show="*",width=38,bg="#202638",fg="white",insertbackground="white",relief="flat")
        key.insert(0,config.get("openai_key","")); key.pack(padx=20,ipady=7)
        def save_and_close():
            config["personality"]=var.get()
            config["openai_key"]=key.get().strip()
            self.sync_state["personality"]=var.get()
            save_config(); self.say("Mika",f"Mode {var.get()} activé. 😏"); win.destroy()
        tk.Button(win,text="Enregistrer",command=save_and_close,bg="#718cff",fg="white",bd=0,padx=16,pady=8).pack(pady=15)

    def current_processes(self):
        try:
            return subprocess.check_output(["tasklist","/FO","CSV","/NH"],text=True,encoding="utf-8",errors="ignore").lower()
        except Exception: return ""

    def detect_games(self):
        p=self.current_processes()
        apps={
            "Minecraft":["javaw.exe","minecraft.exe"],
            "Valorant":["valorant-win64-shipping.exe","valorant.exe"],
            "Modrinth":["modrinth-app.exe"],
            "Steam":["steam.exe"],
            "Discord":["discord.exe","discordptb.exe"]
        }
        return {a for a,exes in apps.items() if any(chr(34)+e+chr(34) in p for e in exes)}

    def monitor_desktop(self):
        found=self.detect_games()
        for game in found-self.last_detected:
            self.root.after(0,lambda g=game:self.on_detected(g))
        self.last_detected=found
        self.root.after(3000,self.monitor_desktop)

    def on_detected(self,game):
        self.moodset("hype")
        msg={
            "Minecraft":"Minecraft ouvert. 👀 Je regarde ton PvP. Si tu rates un combo, je me moque.",
            "Valorant":"VALORANT lancé. 🎯 Respire avant de spray, champion.",
            "Modrinth":"Modrinth ouvert... encore des mods ? 😭",
            "Steam":"Steam ouvert. 💀 Tu vas vraiment jouer à ça ?",
            "Discord":"Discord ouvert. 👀 La distraction est officiellement détectée."
        }.get(game,game+" détecté.")
        self.say("Mika",msg); self.notify(msg); self.speak(msg)

    def ai_answer(self,msg):
        key=config.get("openai_key") or os.environ.get("MIKA_OPENAI_API_KEY")
        if not key: return None
        body={"model":"gpt-4o-mini","messages":[
            {"role":"system","content":self.PERSONALITIES.get(config.get("personality","Tsundere"),self.PERSONALITIES["Tsundere"])+" Réponds en français, 1 à 3 phrases maximum. Tu es un assistant desktop sous Windows. Ne prétends jamais avoir fait une action si elle n'a pas été exécutée."},
            {"role":"user","content":msg}
        ],"temperature":0.9}
        try:
            req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(body).encode(),
                headers={"Content-Type":"application/json","Authorization":"Bearer "+key})
            with urllib.request.urlopen(req,timeout=25) as r:
                return json.loads(r.read().decode())["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

    def launch_app(self, target):
        aliases={
            "notepad":"notepad.exe","bloc-notes":"notepad.exe","calculatrice":"calc.exe",
            "calculator":"calc.exe","paint":"mspaint.exe","explorateur":"explorer.exe",
            "explorer":"explorer.exe","discord":"discord.exe","steam":"steam.exe"
        }
        cmd=aliases.get(target.lower(),target)
        try:
            if any(c in cmd for c in ["&","|",";",">","<"]): return False
            subprocess.Popen(cmd if cmd.endswith(".exe") else [cmd],shell=False)
            return True
        except Exception: return False

    def open_path(self,path):
        path=os.path.expandvars(os.path.expanduser(path.strip().strip('"')))
        if not os.path.exists(path): return False
        try: os.startfile(path); return True
        except Exception: return False

    def open_folder(self):
        path=simpledialog.askstring("Mika","Chemin du dossier/fichier à ouvrir :")
        if path:
            ok=self.open_path(path)
            self.say("Mika","Ouvert. 😌" if ok else "Je ne trouve pas ce chemin. 😭")

    def show_time(self):
        now=datetime.datetime.now().strftime("%H:%M")
        self.moodset("happy"); self.say("Mika",f"Il est {now}. 🕐")

    def timer_dialog(self):
        mins=simpledialog.askinteger("Mika Timer","Combien de minutes ?",minvalue=1,maxvalue=1440)
        if mins: self.timer(mins)

    def timer(self,mins):
        memory["timers"]+=1; save(); self.say("Mika",f"⏱ Timer de {mins} minute(s) lancé.")
        def wait():
            time.sleep(mins*60)
            msg="⏰ Timer terminé ! Debout, gamer."
            self.root.after(0,lambda:self.say("Mika",msg)); self.root.after(0,lambda:self.moodset("surprised"))
            self.root.after(0,lambda:self.notify(msg)); self.root.after(0,lambda:self.speak(msg)); self.root.after(0,lambda:self.root.bell())
        threading.Thread(target=wait,daemon=True).start()

    def reminder_dialog(self):
        mins=simpledialog.askinteger("Mika Rappel","Dans combien de minutes ?",minvalue=1,maxvalue=10080)
        if mins:
            text=simpledialog.askstring("Mika Rappel","Quel rappel ?")
            if text: self.reminder(mins,text)

    def reminder(self,mins,text):
        memory["reminders"]+=1; save()
        self.say("Mika",f"🔔 Je te rappelle « {text} » dans {mins} minute(s).")
        def wait():
            time.sleep(mins*60)
            msg=f"🔔 Rappel : {text}"
            self.root.after(0,lambda:self.say("Mika",msg)); self.root.after(0,lambda:self.moodset("surprised"))
            self.root.after(0,lambda:self.notify(msg)); self.root.after(0,lambda:self.speak(msg))
        threading.Thread(target=wait,daemon=True).start()

    def stats_text(self):
        return f"📊 Sessions: {memory['sessions']} | Messages: {memory['messages']} | Timers: {memory['timers']} | Rappels: {memory['reminders']} | Souvenirs: {len(memory['user_notes'])}"

    def stats(self):
        self.say("Mika",self.stats_text())

    def game(self,name):
        self.moodset("hype")
        self.say("Mika",f"{name} détecté. 🎮 Allez, montre-moi ce que tu sais faire.")

    def command(self,msg):
        m=msg.lower().strip()
        if m in ("quelle heure","l'heure","heure","donne-moi l'heure","il est quelle heure"):
            self.show_time(); return True
        if m.startswith("lance ") or m.startswith("ouvre l'application ") or m.startswith("ouvre "):
            if m.startswith("lance "): target=msg[6:].strip()
            elif m.startswith("ouvre l'application "): target=msg[20:].strip()
            else: target=msg[6:].strip()
            if os.path.exists(os.path.expandvars(os.path.expanduser(target.strip('"')))):
                ok=self.open_path(target)
            else: ok=self.launch_app(target)
            self.moodset("happy" if ok else "annoyed")
            self.say("Mika","C'est fait. 😌" if ok else "Je ne peux pas ouvrir ça. Vérifie le nom ou le chemin. 😭")
            return True
        if m.startswith("timer ") or m.startswith("minuteur "):
            parts=m.split()
            try: self.timer(max(1,int(parts[1]))); return True
            except Exception: pass
        if m.startswith("rappel ") or m.startswith("rappelle-moi "):
            prefix="rappel " if m.startswith("rappel ") else "rappelle-moi "
            raw=msg[len(prefix):].strip()
            parts=raw.split(maxsplit=1)
            try:
                mins=int(parts[0]); textmsg=parts[1] if len(parts)>1 else "Ton rappel"
                self.reminder(max(1,mins),textmsg); return True
            except Exception: pass
        if m in ("ouvre youtube","ouvre google","ouvre twitch"):
            url={"ouvre youtube":"https://youtube.com","ouvre google":"https://google.com","ouvre twitch":"https://twitch.tv"}[m]
            webbrowser.open(url); self.say("Mika","Navigateur ouvert. 😏"); return True
        return False

    def answer(self,msg):
        if self.command(msg): return None
        m=msg.lower()
        if any(x in m for x in ["salut","yo","hey","bonjour"]):
            self.moodset("happy"); return random.choice(["Yo 😌","Enfin. J'attendais.","Salut toi. 👀"])
        if "minecraft" in m:
            self.moodset("hype"); return random.choice(["Minecraft ? Vas-y, montre-moi ton PvP. 😏","Encore un attribute swap raté et je démissionne. 😭","Si tu rates ton mace, je vais faire semblant de ne pas avoir vu. 👀"])
        if "valorant" in m or "valo" in m:
            self.moodset("hype"); return random.choice(["Encore du ranked ? Respire avant de spray, champion. 🎯","Tu vas vraiment wide swing ça ? 😭","Ton crosshair est innocent, lui. C'est toi le problème. 😏"])
        if "modrinth" in m:
            self.moodset("surprised"); return "Modrinth ? Je garde un œil sur tes mods. 👀"
        if any(x in m for x in ["merci","thank"]):
            self.moodset("shy"); return "Ouais ouais... de rien. 🙄"
        if any(x in m for x in ["fatigue","fatigué","fatiguée","triste"]):
            self.moodset("sleepy"); return "Pause deux minutes. Même les gamers doivent recharger. 💤"
        if "stats" in m: return self.stats_text()
        if m.startswith("souviens-toi") or m.startswith("remember"):
            note=msg.split(" ",1)[1] if " " in msg else ""
            if note:
                memory["user_notes"].append(note); save(); self.moodset("shy"); return "Je l'ai gardé en mémoire. 👀"
        if "insulte" in m or "nul" in m:
            self.moodset("annoyed"); return "Wow. Quelle violence. ಠ_ಠ"
        self.moodset(random.choice(["happy","happy","surprised","shy"]))
        return random.choice(["Hmm... intéressant. Continue.","J'écoute. 👀","Tu veux vraiment que je réponde à ça ? 😭","Pas mal. Mais j'ai une meilleure idée."])

    def send(self):
        msg=self.entry.get().strip()
        if not msg:return
        self.entry.delete(0,"end"); memory["messages"]+=1; save(); self.sync_state.setdefault("messages",[]).append(("Toi",msg)); self.sync_state["messages"]=self.sync_state["messages"][-100:]; self.sync_seen=len(self.sync_state["messages"]); self.say("Toi",msg)
        result=self.answer(msg)
        if result is None: return
        threading.Thread(target=self.ai_or_fallback,args=(msg,result),daemon=True).start()
        self.status.set(random.choice(["Je te surveille. 👀","T'as besoin de moi ?","Bon... je reste là."]))

    def ai_or_fallback(self,msg,fallback):
        ai=self.ai_answer(msg)
        answer=ai or fallback
        self.sync_state.setdefault("messages",[]).append(("Mika",answer)); self.sync_state["messages"]=self.sync_state["messages"][-100:]; memory["chat"]=self.sync_state["messages"]; save(); self.root.after(0,lambda:self.say("Mika",answer))
        if ai: self.root.after(0,lambda:self.speak(answer))

    def idle_reaction(self):
        self.status.set(random.choice(["Je te surveille. 👀","T'as besoin de moi ?","Toujours là.","...tu joues à quoi ?"]))
        self.root.after(12000,self.idle_reaction)

root=tk.Tk()
Mika(root)
root.mainloop()
