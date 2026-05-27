# 🎧 DJ-Youtube-Music — Virtual Music Curator

**DJ-Youtube-Music** es una aplicación de escritorio moderna e interactiva inspirada en la estética de Spotify, diseñada para transformar tu estado de ánimo o peticiones en un set musical continuo y automatizado.

El núcleo del proyecto utiliza Inteligencia Artificial local para actuar como un DJ virtual ("Onda"), generando comentarios de transición fluidos y seleccionando el siguiente track ideal basándose en el contexto actual y en el perfil de gustos reales del usuario.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)  
![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)  
![LLM](https://img.shields.io/badge/Local_LLM-Gemma%20%2F%20DeepSeek-orange?style=for-the-badge)

---

# ✨ Características Principales

- **Cabina de DJ Inteligente:** Conexión directa con modelos de lenguaje locales (Gemma, DeepSeek, Qwen) ejecutándose en **LM Studio**.
- **Arquitectura Multihilo (Asincrónica):** Uso de `QThread` (`DJWorkerThread`) en PySide6 para evitar bloqueos de la interfaz gráfica (`QMainWindow`) durante procesos de IA, síntesis de voz o streaming de audio.
- **Inyección de Contexto Real:** Lectura segura del historial reciente del usuario mediante `ytmusicapi` para mejorar el perfil musical del DJ (con fallback automático a modo público).
- **Autenticación Nativa Blindada:** Inicio de sesión integrado usando un navegador Chromium/Edge embebido (`pywebview`) capaz de interceptar y generar automáticamente firmas criptográficas de sesión.
- **Streaming de Audio Invisible:** Extracción dinámica de URLs de streaming (`.googlevideo`) usando `yt-dlp` y reproducción síncrona mediante el motor **mpv**.
- **Controles Multimedia Interactivos:** Botones nativos para Pausar/Reproducir, Avanzar (Skip) y Retroceder (Back) mediante comunicación IPC (`stdin` pipes).
- **Atajos de Teclado Nativos:** Soporte completo para barra espaciadora y flechas del teclado.
- **Actualización de Contexto en Caliente:** Cambia el género, artista o mood en tiempo real mientras se reproduce música.

---

# 🛠️ Requisitos del Sistema

## 1. Dependencias del Sistema Operativo

La aplicación transmite audio directamente sin descargar archivos locales, por lo que requiere tener instalado **mpv**.

### Windows (Recomendado vía Scoop)

```
scoop bucket add extrasscoop install mpv
```

### Linux

```
sudo apt install mpv
```

### macOS

```
brew install mpv
```

---

## 2. Configuración del Entorno Local de IA

1. Descarga e instala **LM Studio**.
2. Descarga un modelo compatible:
    - Gemma 2
    - Qwen 2.5
    - DeepSeek V4 / Flash
3. Abre la pestaña:
    - **Developer**
    - **Local Server**
4. Activa el servidor local en el puerto:

```
http://localhost:1234/v1
```

---

# 🚀 Instalación Paso a Paso

## 1. Clonar el Repositorio

```
git clone https://github.com/TU_USUARIO/DJ-Youtube-Music.gitcd DJ-Youtube-Music
```

---

## 2. Crear el Entorno Virtual

### Windows (PowerShell)

```
python -m venv .venv.\.venv\Scripts\activate
```

### Linux/macOS

```
python3 -m venv .venvsource .venv/bin/activate
```

---

## 3. Instalar Dependencias

```
pip install -r requirements.txt
```

---

# 🔐 Configuración de Google Cloud (client_secret.json)

Para permitir que la aplicación acceda legítimamente a playlists, historial y datos de YouTube Music:

## Paso 1 — Crear Proyecto

1. Ingresa a Google Cloud Console.
2. Crea un nuevo proyecto:
    - Ejemplo: `dj-youtube-music`

---

## Paso 2 — Habilitar API

1. Busca:

```
YouTube Data API v3
```

2. Haz clic en **Habilitar**.

---

## Paso 3 — Configurar OAuth

Ve a:

```
API y servicios > Pantalla de consentimiento OAuth
```

### Configuración

- Tipo de usuario: **Externo**
- Completa:
    - Nombre de la aplicación
    - Correos de contacto

---

## Paso 4 — Agregar Usuario de Prueba

En:

```
Usuarios de prueba (Test users)
```

Haz clic en:

```
Add Users
```

Agrega exactamente el correo de Google que utilizas en YouTube Music.

⚠️ **Importante:** Si no agregas tu cuenta aquí, Google bloqueará el inicio de sesión.

---

## Paso 5 — Crear Credencial OAuth

Ve a:

```
Credenciales > + Crear credenciales > ID de cliente OAuth
```

Selecciona:

```
Desktop App
```

Asigna un nombre y crea la credencial.

---

## Paso 6 — Descargar JSON

1. Descarga el archivo JSON generado.
2. Renómbralo como:

```
client_secret.json
```

3. Colócalo en la raíz del proyecto:

```
DJ-Youtube-Music/client_secret.json
```

---

# ▶️ Ejecutar la Aplicación

Con LM Studio encendido y `client_secret.json` configurado:

```
python app.py
```

---

# 🔑 Flujo de Inicio de Sesión

## Primer Inicio

1. La interfaz detectará que no existe una sesión activa.
2. Haz clic en:

```
Authenticate with Google
```

3. Se abrirá un navegador integrado mostrando el login oficial de YouTube Music.

---

## Captura Automática de Sesión

Una vez iniciada la sesión:

- La aplicación intercepta las cookies de acceso.
- Genera localmente la firma criptográfica `SAPISIDHASH`.
- Guarda automáticamente:

```
browser.json
```

---

## Resultado

La ventana de login se cerrará automáticamente y la cabina del DJ quedará desbloqueada mostrando:

- Historial reciente
- Portadas de álbumes
- Playlists
- Recomendaciones musicales

---

# 🎮 Controles Disponibles

|Acción|Tecla|
|---|---|
|Play / Pause|Barra espaciadora|
|Siguiente canción|Flecha derecha|
|Canción anterior|Flecha izquierda|

---

# 🧠 Arquitectura del Proyecto

```
DJ-Youtube-Music/│├── app.py├── requirements.txt├── client_secret.json├── browser.json│├── core/│   ├── dj_worker.py│   ├── llm_controller.py│   ├── audio_engine.py│   └── auth_manager.py│├── ui/│   ├── main_window.py│   ├── widgets/│   └── assets/│└── services/    ├── ytmusic_service.py    ├── streaming_service.py    └── transition_generator.py
```

---

# 🤝 Contribuciones

Si deseas extender el proyecto:

## 1. Haz un Fork

```
git fork
```

---

## 2. Crea una Rama

```
git checkout -b feature/MiNuevaMejora
```

---

## 3. Realiza tus Cambios

```
git commit -m "feat: add support for local Ollama endpoints"
```

---

## 4. Sube la Rama

```
git push origin feature/MiNuevaMejora
```

---

## 5. Abre un Pull Request

Describe detalladamente:

- Funcionalidad añadida
- Mejoras realizadas
- Bugs corregidos
- Impacto técnico

---

# 📌 Tecnologías Utilizadas

- Python 3.11+
- PySide6 / Qt6
- LM Studio
- Gemma / DeepSeek / Qwen
- mpv
- yt-dlp
- ytmusicapi
- pywebview

---

# 📄 Licencia

Este proyecto está distribuido bajo la licencia MIT.

Puedes modificarlo, redistribuirlo y adaptarlo respetando los términos de la licencia.

---

# ❤️ Créditos

Desarrollado para crear una experiencia musical inteligente, fluida y completamente local utilizando IA moderna y tecnologías open-source.
