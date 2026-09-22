import tkinter as tk
from tkinter import scrolledtext, messagebox
import json, os, subprocess, threading, time, random, datetime, urllib.request

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(APP_DIR, "memory.json")
DEFAULT_MEMORY = {"name":"Mika","sessions":0,"messages":0,"timers":0,"user_notes":[]}

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
    FACES = {
        "happy":("◕‿◕","HAPPY"), "annoyed":("ಠ_ಠ","ANNOYED"),
        "surprised":("⊙_⊙","SURPRISED"), "shy":("⁄⁄•⁄ω⁄•⁄⁄","SHY"),
        "sleepy":("－_－","SLEEPY"), "hype":("ᕙ(🔥‿🔥)ᕗ","HYPE")
    }

    def __init__(self, root):
        self.root=root
        root.title("Mika — Desktop Companion V3")
        root.geometry("470x720")
        root.minsize(390,580)
        root.attributes("-topmost", True)
        root.configure(bg="#0d1018")
        self.build()
        self.idle_reaction()\n        self.last_detected=set()\n        self.monitor_desktop()

    def build(self):
        top=tk.Frame(self.root,bg="#171b28"); top.pack(fill="x")
        tk.Label(top,text="MIKA",fg="#c8d5ff",bg="#171b28",
                 font=("Segoe UI",17,"bold")).pack(side="left",padx=14,pady=9)
        tk.Label(top,text="V2 • DESKTOP COMPANION",fg="#6878a8",bg="#171b28",
                 font=("Segoe UI",8,"bold")).pack(side="left")
        tk.Button(top,text="×",command=self.root.destroy,bg="#171b28",
                  fg="white",bd=0,font=("Segoe UI",15)).pack(side="right",padx=9)

        self.avatar=tk.Label(self.root,text="◕‿◕",fg="#e6edff",bg="#202638",
                             font=("Segoe UI",45,"bold"),width=10,height=2)
        self.avatar.pack(pady=(15,3))
        self.mood=tk.StringVar(value="HAPPY")
        self.status=tk.StringVar(value="Je suis là. Essaie de me surprendre.")
        tk.Label(self.root,textvariable=self.mood,fg="#8fa9ff",bg="#0d1018",
                 font=("Segoe UI",9,"bold")).pack()
        tk.Label(self.root,textvariable=self.status,fg="#aeb7cc",bg="#0d1018",
                 wraplength=380,font=("Segoe UI",9)).pack(pady=(2,10))

        self.chat=scrolledtext.ScrolledText(self.root,wrap="word",height=15,
            bg="#151a25",fg="#edf1ff",insertbackground="white",relief="flat",
            font=("Segoe UI",10),padx=9,pady=8)
        self.chat.pack(fill="both",expand=True,padx=13)
        self.chat.insert("end","Mika: T'es enfin là. 🙄\nMika: V2 est lancée. Essaie de me casser. 👀\n\n")
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
            ("📝 Notes",lambda:subprocess.Popen(["notepad.exe"])),
            ("⏱ Timer",self.timer_dialog),
            ("📊 Stats",self.stats)
        ]
        for label,cmd in buttons:
            tk.Button(controls,text=label,command=cmd,bg="#202638",fg="#dfe6ff",
                      bd=0,padx=7,pady=7).pack(side="left",padx=2)

    def show_games(self):
        games=", ".join(sorted(self.detect_games())) or "Aucun jeu suivi"
        self.say("Mika","🖥️ Ouvert : "+games)

    def current_processes(self):
        try:
            return subprocess.check_output(["tasklist","/FO","CSV","/NH"],text=True,encoding="utf-8",errors="ignore").lower()
        except Exception:
            return ""

    def detect_games(self):
        p=self.current_processes()
        apps={"Minecraft":["javaw.exe","minecraft.exe"],"Valorant":["valorant-win64-shipping.exe","valorant.exe"],"Modrinth":["modrinth-app.exe"],"Steam":["steam.exe"],"Discord":["discord.exe","discordptb.exe"]}
        return {a for a,exes in apps.items() if any(chr(34)+e+chr(34) in p for e in exes)}

    def monitor_desktop(self):
        found=self.detect_games()
        for game in found-self.last_detected:
            self.root.after(0,lambda g=game:self.on_detected(g))
        self.last_detected=found
        self.root.after(3000,self.monitor_desktop)

    def on_detected(self,game):
        self.moodset("hype")
        msg={"Minecraft":"Minecraft ouvert. 👀 Je regarde ton PvP.","Valorant":"VALORANT lancé. Respire avant le premier duel. 🎯","Modrinth":"Modrinth ouvert... encore des mods ? 😭","Steam":"Steam ouvert. 💀","Discord":"Discord ouvert. 👀"}.get(game,game+" détecté.")
        self.say("Mika",msg)
        self.notify(msg)
        self.speak(msg)

    def notify(self,msg):
        if os.name!="nt": return
        safe=msg.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        ps='[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;$x=[Windows.Data.Xml.Dom.XmlDocument]::new();$x.LoadXml("<toast><visual><binding template=\"ToastGeneric\"><text>Mika</text><text>'+safe+'</text></binding></visual></toast>");$t=[Windows.UI.Notifications.ToastNotification]::new($x);[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Mika Desktop Companion").Show($t)'
        try: subprocess.Popen(["powershell","-NoProfile","-Command",ps],creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except Exception: pass

    def speak(self,msg):
        if os.name!="nt": return
        safe=msg.replace("'","''")
        ps="Add-Type -AssemblyName System.Speech;$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;$v=$s.GetInstalledVoices()|ForEach-Object {$_.VoiceInfo};$f=$v|Where-Object {$_.Gender -eq 'Female'}|Select-Object -First 1;if($f){$s.SelectVoice($f.Name)};$s.Speak('"+safe+"')"
        try: subprocess.Popen(["powershell","-NoProfile","-Command",ps],creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except Exception: pass

    def speak_last(self):
        self.speak("Salut, c'est Mika. Je suis là. 👀")
        self.say("Mika","🔊 Voix Windows lancée.")

    def ai_answer(self,msg):
        key=os.environ.get("MIKA_OPENAI_API_KEY")
        if not key: return None
        body={"model":"gpt-4o-mini","messages":[{"role":"system","content":"Tu es Mika, une compagne desktop anime gamer. Tu parles français, tu es drôle, taquine mais gentille. Réponses courtes."},{"role":"user","content":msg}],"temperature":0.9}
        try:
            req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+key})
            with urllib.request.urlopen(req,timeout=25) as r: return json.loads(r.read().decode())["choices"][0]["message"]["content"].strip()
        except Exception: return None

    def say(self,who,msg):
        self.chat.configure(state="normal")
        self.chat.insert("end",f"{who}: {msg}\n\n")
        self.chat.see("end"); self.chat.configure(state="disabled")

    def moodset(self,mood):
        face,label=self.FACES.get(mood,self.FACES["happy"])
        self.avatar.config(text=face); self.mood.set(label)

    def answer(self,msg):
        m=msg.lower()
        if any(x in m for x in ["salut","yo","hey","bonjour"]):
            self.moodset("happy"); return random.choice(["Yo 😌","Enfin. J'attendais.","Salut toi. 👀"])
        if "minecraft" in m:
            self.moodset("hype"); return "Minecraft ? Vas-y, montre-moi ton PvP. 😏"
        if "valorant" in m or "valo" in m:
            self.moodset("hype"); return "Encore du ranked ? Respire avant de spray, champion. 🎯"
        if "modrinth" in m:
            self.moodset("surprised"); return "Modrinth ? Je garde un œil sur tes mods. 👀"
        if any(x in m for x in ["merci","thank"]):
            self.moodset("shy"); return "Ouais ouais... de rien. 🙄"
        if any(x in m for x in ["fatigue","fatigué","fatiguée","triste"]):
            self.moodset("sleepy"); return "Pause deux minutes. Même les gamers doivent recharger. 💤"
        if "stats" in m:
            return self.stats_text()
        if m.startswith("souviens-toi") or m.startswith("remember"):
            note=msg.split(" ",1)[1] if " " in msg else ""
            if note:
                memory["user_notes"].append(note); save()
                self.moodset("shy"); return "Je l'ai gardé en mémoire. 👀"
        if "insulte" in m or "nul" in m:
            self.moodset("annoyed"); return "Wow. Quelle violence. Je note ça. ಠ_ಠ"
        self.moodset(random.choice(["happy","happy","surprised","shy"]))
        return random.choice(["Hmm... intéressant. Continue.","J'écoute. 👀","Tu veux vraiment que je réponde à ça ? 😭","Pas mal. Mais j'ai une meilleure idée."])

    def send(self):
        msg=self.entry.get().strip()
        if not msg:return
        self.entry.delete(0,"end"); memory["messages"]+=1; save()
        self.say("Toi",msg); self.say("Mika",self.answer(msg))
        self.status.set(random.choice(["Je te surveille. 👀","T'as besoin de moi ?","Bon... je reste là."]))

    def game(self,name):
        self.moodset("hype"); self.say("Mika",f"{name} détecté. 🎮 Allez, montre-moi ce que tu sais faire.")

    def timer_dialog(self):
        win=tk.Toplevel(self.root); win.title("Mika Timer"); win.configure(bg="#171b28")
        tk.Label(win,text="Combien de minutes ?",fg="white",bg="#171b28",
                 font=("Segoe UI",11,"bold")).pack(padx=20,pady=(18,8))
        e=tk.Entry(win,bg="#202638",fg="white",insertbackground="white",relief="flat")
        e.insert(0,"5"); e.pack(padx=20,pady=5,ipady=7)
        def go():
            try: mins=max(1,int(e.get()))
            except ValueError: messagebox.showerror("Mika","Entre un nombre entier."); return
            win.destroy(); self.timer(mins)
        tk.Button(win,text="Lancer",command=go,bg="#718cff",fg="white",bd=0,padx=15,pady=7).pack(pady=15)

    def timer(self,mins):
        memory["timers"]+=1; save(); self.say("Mika",f"⏱ Timer de {mins} minutes lancé.")
        def wait():
            time.sleep(mins*60)
            self.root.after(0,lambda:self.say("Mika","⏰ Temps écoulé !"))
            self.root.after(0,lambda:self.moodset("surprised"))
            self.root.after(0,lambda:self.root.bell())
        threading.Thread(target=wait,daemon=True).start()

    def stats_text(self):
        return f"📊 Sessions: {memory['sessions']} | Messages: {memory['messages']} | Timers: {memory['timers']} | Souvenirs: {len(memory['user_notes'])}"

    def stats(self):
        self.moodset("happy"); self.say("Mika",self.stats_text())

    def idle_reaction(self):
        self.status.set(random.choice(["Je te surveille. 👀","T'as besoin de moi ?","Toujours là.","...tu joues à quoi ?"]))
        self.root.after(12000,self.idle_reaction)

root=tk.Tk()
Mika(root)
root.mainloop()
