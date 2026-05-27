import webview
import threading
import time
import json
import http.cookies
import hashlib
import re
from pathlib import Path

AUTH_COOKIES = {"__Secure-1PSID", "SAPISID", "LOGIN_INFO"}

def _coerce_cookie_dict(raw_cookies):
    result = {}
    for c in raw_cookies:
        if isinstance(c, http.cookies.SimpleCookie):
            for key, morsel in c.items():
                if key:
                    result[str(key)] = str(morsel.value)
            continue
        if isinstance(c, dict):
            name = c.get("name", c.get("Name", c.get("key", "")))
            value = c.get("value", c.get("Value", ""))
            if name:
                result[str(name)] = str(value)
            continue
        name = getattr(c, "name", getattr(c, "Name", getattr(c, "_name", "")))
        value = getattr(c, "value", getattr(c, "Value", getattr(c, "_value", "")))
        if name:
            result[str(name)] = str(value)
    return result

def run_login_window() -> bool:
    root = Path(__file__).resolve().parent.parent
    result = {"ok": False}

    def _poll_cookies(window):
        print("\n[LOGIN POLLER] 🕵️‍♂️ Sabueso iniciado. Esperando login...")
        while not result["ok"]:
            time.sleep(2)
            try:
                url = window.get_current_url()
                if not url or "music.youtube.com" not in url:
                    continue

                raw = window.get_cookies()
                if not raw:
                    continue

                normalized = _coerce_cookie_dict(raw)
                if not AUTH_COOKIES.intersection(normalized):
                    continue

                parts = [f"{k}={v}" for k, v in normalized.items()]
                cookie_str = "; ".join(parts)

                # 🎯 1. Buscamos la cookie SAPISID para generar la firma de Google
                match = re.search(r'(SAPISID|__Secure-1PAPISID)=([^;]+)', cookie_str)
                if not match:
                    continue # Seguimos esperando si la cookie aún no se ha inyectado
                    
                sapisid = match.group(2)
                timestamp = int(time.time())
                hash_str = f"{timestamp} {sapisid} https://music.youtube.com"
                hash_val = hashlib.sha1(hash_str.encode()).hexdigest()

                # 🎯 2. Construimos el diccionario perfecto eludiendo el bug de ytmusicapi
                browser_data = {
                    "accept": "*/*",
                    "accept-language": "es-ES,es;q=0.9",
                    "content-type": "application/json",
                    "Cookie": cookie_str, # Mayúscula estricta
                    "Authorization": f"SAPISIDHASH {timestamp}_{hash_val}", # Firma inyectada
                    "origin": "https://music.youtube.com",
                    "x-goog-authuser": "0",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }

                filepath = root / "browser.json"
                with open(filepath, "w") as f:
                    json.dump(browser_data, f, indent=4)

                print("✅ [LOGIN] Sesión interceptada, firmada y sellada nativamente.")
                result["ok"] = True
                window.destroy()
                break
            except Exception:
                pass 

    try:
        window = webview.create_window(
            "Login to QueNota?",
            "https://music.youtube.com",
            width=900,
            height=700,
        )
        t = threading.Thread(target=_poll_cookies, args=(window,), daemon=True)
        t.start()
        webview.start(private_mode=False)
    except Exception as e:
        print(f"[LOGIN] pywebview error: {e}")

    return result["ok"]