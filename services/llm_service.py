import json
import re
from typing import Any, Dict, List, Optional

import requests

LOCAL_LLM_ENDPOINT = "http://192.168.1.28:1234/v1/chat/completions"

SYSTEM_PROMPT_TEMPLATE = """You are 'QueNota?', an elite AI music curator for {user}.
Your task is to analyze the user's request and their [USER_CONTEXT], then determine the exact song and artist to play.

[USER_CONTEXT]
{user_context}

RULES:
1. If the user asks for a mood/vibe (e.g., "algo que me gusta", "pon algo suave"), YOU MUST pick a specific, real song from the [USER_CONTEXT] history above.
2. If the user asks for an artist explicitly (e.g., "lo mas reciente de Juanes"), set the search term to find that specific artist.
3. NEVER put the user's raw instruction into the 'musica_elegida' field.

FORMAT: You must output a valid JSON containing exactly these keys:
{{
  "razonamiento_interno": "Strictly 1 or 2 short sentences explaining your logic.",
  "musica_elegida": "Artist Name - Song Title",
  "comentario_personalizado": "Hola {user}... (your presentation of the track)",
  "termino_busqueda_yt": "Keywords to search on YouTube"
}}

EXAMPLES:
User Instruction: "Pon algo que me gusta"
JSON: {{"razonamiento_interno": "The user wants something they like. I see 'La Camisa Negra - Juanes' in their history. I will select that.", "musica_elegida": "Juanes - La Camisa Negra", "comentario_personalizado": "Vamos a lo seguro, {user}. Aquí tienes algo de Juanes que sé que te encanta.", "termino_busqueda_yt": "Juanes La Camisa Negra"}}

User Instruction: "Quiero escuchar lo más reciente de Bad Bunny"
JSON: {{"razonamiento_interno": "The user is explicitly asking for Bad Bunny's latest release. I will format the search term to find his newest track.", "musica_elegida": "Bad Bunny - Nuevo lanzamiento", "comentario_personalizado": "Claro que sí, {user}. Aquí tienes lo más fresco de Bad Bunny.", "termino_busqueda_yt": "Bad Bunny nuevo 2024"}}"""


class LocalLLMClient:
    def __init__(self, endpoint: str = LOCAL_LLM_ENDPOINT, username: str = "Oyente"):
        self.endpoint = endpoint
        self._username = username

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, name: str):
        self._username = name or "Oyente"

    def get_llm_response(
        self, prompt: str, user_context: str = "", timeout: int = 120,
        avoid_list: List[str] = None,
    ) -> Optional[Dict[str, Any]]:
        # truncate context to avoid 400 Bad Request
        MAX_CONTEXT_CHARS = 2000
        if len(user_context) > MAX_CONTEXT_CHARS:
            user_context = user_context[:MAX_CONTEXT_CHARS] + "\n... (truncated)"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            user=self._username,
            user_context=user_context or "No recent history available.",
        )

        avoid_block = ""
        if avoid_list:
            avoid_block = (
                "\n\nCRITICAL AVOID LIST: You MUST NOT suggest any of the following tracks: "
                f"{', '.join(avoid_list)}. Pick something different but related."
            )

        user_content = (
            f"<system>\n{system_prompt}\n</system>\n\n"
            f"<user>\nUSER INSTRUCTION: {prompt}{avoid_block}\n"
            f"Follow the RULES and FORMAT above. Think step by step in 'razonamiento_interno'. Output ONLY the JSON object.</user>"
        )

        temp = 0.2
        if avoid_list and len(avoid_list) > 2:
            temp = 0.5

        payload = {
            "model": "local-model",
            "messages": [{"role": "user", "content": user_content}],
            "temperature": temp,
            "max_tokens": 1024,
            "stream": False,
        }

        try:
            response = requests.post(self.endpoint, json=payload, timeout=timeout)
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
            print(f"[LLM ERROR] Timeout after {timeout}s: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[LLM ERROR] Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[LLM ERROR] Status: {e.response.status_code}, Body: {e.response.text[:300]}")
            return None
        except Exception as e:
            print(f"[LLM ERROR] Unexpected response parsing: {e}")
            return None

        # Strip markdown code fences, then extract JSON
        raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json.strip())
        raw_json = re.sub(r"\s*```$", "", raw_json)
        # if missing closing brace, append it (truncated response)
        if raw_json.count("{") > raw_json.count("}"):
            raw_json += "}"
            print(f"[LLM DEBUG] Appended missing '}}' to truncated response")
        json_match = re.search(r"\{.*\}", raw_json, re.DOTALL)
        if json_match:
            raw_json = json_match.group()
        else:
            print(f"[LLM ERROR] No JSON object found in response. Raw text:\n{raw_json[:500]}")
            return None

        try:
            parsed = json.loads(raw_json)
            required_keys = {"musica_elegida", "comentario_personalizado", "razonamiento_interno"}
            missing = required_keys - set(parsed.keys())
            if missing:
                print(f"[LLM WARNING] Missing keys: {missing}. Have: {set(parsed.keys())}")
            razon = parsed.get("razonamiento_interno", "")
            if razon:
                print(f"[LLM] Chain-of-thought: {razon[:150]}")
            print(f"[LLM] Parsed OK: musica_elegida='{parsed.get('musica_elegida', '')}', "
                  f"search='{parsed.get('termino_busqueda_yt', '')}'")
            return parsed
        except json.JSONDecodeError as e:
            print(f"[LLM ERROR] JSON decode failed: {e}")
            print(f"[LLM ERROR] Cleaned text for parsing:\n{raw_json[:500]}")
            return None
