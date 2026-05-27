import json
import re
from typing import Any, Dict, Optional

import requests

LOCAL_LLM_ENDPOINT = "http://192.168.1.28:1234/v1/chat/completions"

SYSTEM_PROMPT = """Eres "Onda", un DJ virtual experto en curaduría musical. Tu objetivo es crear transiciones perfectas.
REGLAS:
1. Tu respuesta DEBE ser estrictamente un objeto JSON válido.
2. Formato esperado: {"comentario_dj": "...", "siguiente_cancion": "...", "artista": "...", "termino_busqueda_yt": "..."}"""


class LocalLLMClient:
    def __init__(self, endpoint: str = LOCAL_LLM_ENDPOINT):
        self.endpoint = endpoint

    def get_llm_response(
        self, prompt: str, user_history: str = ""
    ) -> Optional[Dict[str, Any]]:
        user_content = (
            f"<system>\n{SYSTEM_PROMPT}\n"
            f"HISTORIAL DE REPRODUCCIÓN LOCAL (últimas canciones):\n{user_history}\n</system>\n\n"
            f"<user>\nCONTEXTO ACTUAL: El usuario quiere escuchar música relacionada con: '{prompt}'.\n"
            f"Genera tu respuesta estrictamente en el formato JSON solicitado. No agregues texto introductorio ni conclusiones.</user>"
        )

        payload = {
            "model": "local-model",
            "messages": [{"role": "user", "content": user_content}],
            "temperature": 0.2,
            "max_tokens": 300,
            "stream": False,
        }

        try:
            response = requests.post(self.endpoint, json=payload, timeout=30)
            response.raise_for_status()
            choices = response.json().get("choices", [])
            if not choices:
                print(f"[LLM ERROR] No choices in response: {response.text[:200]}")
                return None
            raw_json = choices[0]["message"]["content"]
            print(f"[LLM] Raw response ({len(raw_json)} chars): {raw_json[:200]}...")
        except requests.exceptions.ConnectionError as e:
            print(f"[LLM ERROR] Connection failed to {self.endpoint}: {e}")
            return None
        except requests.exceptions.Timeout as e:
            print(f"[LLM ERROR] Timeout after 30s: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[LLM ERROR] Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[LLM ERROR] Status: {e.response.status_code}, Body: {e.response.text[:300]}")
            return None
        except Exception as e:
            print(f"[LLM ERROR] Unexpected response parsing: {e}")
            return None

        # Extract JSON block using regex — handles backtick fences and surrounding fluff
        json_match = re.search(r"\{.*\}", raw_json, re.DOTALL)
        if json_match:
            raw_json = json_match.group()
        else:
            print(f"[LLM ERROR] No JSON object found in response. Raw text:\n{raw_json[:500]}")
            return None

        try:
            parsed = json.loads(raw_json)
            required_keys = {"comentario_dj", "siguiente_cancion"}
            if not required_keys.issubset(parsed.keys()):
                print(f"[LLM WARNING] Missing required keys. Have: {set(parsed.keys())}, Need: {required_keys}")
            print(f"[LLM] Parsed OK: siguiente_cancion='{parsed.get('siguiente_cancion', '')}', "
                  f"artista='{parsed.get('artista', '')}'")
            return parsed
        except json.JSONDecodeError as e:
            print(f"[LLM ERROR] JSON decode failed: {e}")
            print(f"[LLM ERROR] Cleaned text for parsing:\n{raw_json[:500]}")
            return None
