import json
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
                return None
            raw_json = choices[0]["message"]["content"]
        except requests.exceptions.RequestException:
            return None

        raw_json = raw_json.strip()

        if raw_json.startswith("```"):
            lines = raw_json.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            raw_json = "\n".join(lines).strip()

        if "{" in raw_json:
            start = raw_json.find("{")
            end = raw_json.rfind("}")
            if end >= start:
                raw_json = raw_json[start : end + 1]

        if not raw_json.startswith("{"):
            return None

        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return None
