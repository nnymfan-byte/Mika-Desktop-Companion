import json, os, secrets, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request

HOST="0.0.0.0"; PORT=8765

def _ai_answer(msg, config):
    key=config.get("openai_key") or os.environ.get("MIKA_OPENAI_API_KEY")
    if not key:
        return "Je suis connectée au PC, mais la clé OpenAI n'est pas configurée. 👀"
    personalities={
        "Tsundere":"Tu es Mika, une fille anime gamer légèrement tsundere. Tu es sarcastique, taquine, intelligente et gentille au fond.",
        "Bestie":"Tu es Mika, une meilleure amie gamer très énergique, drôle, spontanée et encourageante.",
        "Gamer":"Tu es Mika, une gamer compétitive. Tu analyses les situations et donnes des conseils courts.",
        "Calme":"Tu es Mika, une compagne anime calme et intelligente. Tu es douce, concise et légèrement taquine."
    }
    body={"model":"gpt-4o-mini","messages":[
        {"role":"system","content":personalities.get(config.get("personality","Tsundere"),personalities["Tsundere"])+" Réponds en français, 1 à 3 phrases maximum."},
        {"role":"user","content":msg}
    ],"temperature":0.9}
    try:
        req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json","Authorization":"Bearer "+key})
        with urllib.request.urlopen(req,timeout=25) as r:
            return json.loads(r.read().decode())["choices"][0]["message"]["content"].strip()
    except Exception:
        return "J'ai eu un petit bug de connexion avec mon cerveau. 😭"

def start_sync_server(state, config):
    token=config.get("sync_token")
    if not token:
        token=secrets.token_urlsafe(18); config["sync_token"]=token
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"mika_config.json"),"w",encoding="utf-8") as f:
                json.dump(config,f,ensure_ascii=False,indent=2)
        except Exception: pass

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def authorized(self):
            return parse_qs(urlparse(self.path).query).get("token",[""])[0]==token
        def send_json(self,obj,code=200):
            data=json.dumps(obj,ensure_ascii=False).encode()
            self.send_response(code); self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(data)
        def do_OPTIONS(self):
            self.send_response(204); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS"); self.end_headers()
        def do_GET(self):
            path=urlparse(self.path).path
            if path=="/api/state":
                if not self.authorized(): return self.send_json({"error":"unauthorized"},401)
                return self.send_json({"messages":state.get("messages",[])[-100:],"personality":state.get("personality","Tsundere"),"mood":state.get("mood","happy"),"speaking":bool(state.get("speaking",False))})
            files={"/":"index.html","/index.html":"index.html","/app.js":"app.js","/manifest.json":"manifest.json"}
            if path in files:
                try:
                    fn=files[path]; p=os.path.join(os.path.dirname(os.path.abspath(__file__)),"mobile",fn)
                    with open(p,"rb") as f:data=f.read()
                    ct="text/html; charset=utf-8" if fn.endswith(".html") else ("application/javascript" if fn.endswith(".js") else "application/manifest+json")
                    self.send_response(200); self.send_header("Content-Type",ct); self.end_headers(); self.wfile.write(data)
                except Exception:self.send_error(404)
                return
            self.send_error(404)
        def do_POST(self):
            if urlparse(self.path).path!="/api/chat": return self.send_json({"error":"not found"},404)
            if not self.authorized(): return self.send_json({"error":"unauthorized"},401)
            try:
                n=int(self.headers.get("Content-Length","0")); payload=json.loads(self.rfile.read(n).decode()); msg=str(payload.get("message","")).strip()
                if not msg:return self.send_json({"error":"empty"},400)
                state.setdefault("messages",[]).append(("Toi",msg)); state["messages"]=state["messages"][-100:]
                answer=_ai_answer(msg,config); state["messages"].append(("Mika",answer)); state["messages"]=state["messages"][-100:]
                self.send_json({"answer":answer,"messages":state["messages"]})
            except Exception as e:self.send_json({"error":str(e)},500)
    def run():
        try: ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
        except Exception: pass
    threading.Thread(target=run,daemon=True).start()
    return f"http://127.0.0.1:{PORT}",token
