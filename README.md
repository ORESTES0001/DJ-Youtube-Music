# DJ-Youtube-Music
An automated virtual DJ desktop application powered by local LLMs (Gemma/DeepSeek via LM Studio), utilizing PySide6 multithreading, yt-dlp audio streaming, and public/private YT Music context injection.

# 🎧 DJ-Youtube-Music — Virtual Music Curator

**DJ-Youtube-Music** es una aplicación de escritorio moderna e interactiva inspirada en la estética de Spotify, diseñada para transformar tu estado de ánimo o peticiones en un set musical continuo y automatizado. 

El núcleo del proyecto utiliza Inteligencia Artificial local para actuar como un DJ virtual ("Onda"), generando comentarios de transición fluidos y seleccionando el siguiente track ideal basándose en el contexto actual y en el perfil de gustos reales del usuario.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![LLM](https://img.shields.io/badge/Local_LLM-Gemma%20%2F%20DeepSeek-orange?style=for-the-badge)

---

## ✨ Características Principales

* **Cabina de DJ Inteligente:** Conexión directa con modelos de lenguaje locales (Gemma, DeepSeek, Qwen) corriendo de forma nativa en **LM Studio**.
* **Arquitectura Multihilo (Asincrónica):** Implementación de `QThread` (`DJWorkerThread`) en PySide6 para evitar el congelamiento de la interfaz gráfica (`QMainWindow`) durante la inferencia de la IA, síntesis de voz o streaming de audio.
* **Inyección de Contexto Real:** Capacidad de leer de forma segura el historial reciente del usuario de YouTube Music (`ytmusicapi`) para afinar el perfil de gustos del DJ (con fallback automático a modo público).
* **Streaming de Audio Invisible:** Extracción dinámica de URLs de streaming (`.googlevideo`) mediante `yt-dlp` y reproducción síncrona en segundo plano utilizando el motor de **mpv**.
* **Controles Multimedia Interactivos:** Panel con botones de reproducción nativos para Pausar/Reproducir, Avanzar (Skip) y Regresar (Back) tracks mediante comunicación IPC (`stdin` pipes).
* **Atajos de Teclado Nativos:** Control total de la cabina usando la barra espaciadora (Pausa/Play) y las flechas del teclado (Navegación).
* **Actualización de Contexto en Caliente:** Permite cambiar el rumbo del set (género, artista o mood) en tiempo real mientras suena una canción, aplicando el cambio automáticamente en la siguiente transición.

---

## 🛠️ Requisitos del Sistema y Dependencias

### 1. Dependencias de Software (Host OS)
Este proyecto no descarga archivos de audio a disco; transmite directamente. Para ello, requiere el reproductor de medios **mpv** instalado en el sistema.

* **En Windows (Recomendado vía Scoop):**
    ```powershell
    scoop bucket add extras
    scoop install mpv
    ```

### 2. Entorno Local de IA
* Instanciar **LM Studio** con un modelo compatible (ej. Gemma 2 o DeepSeek V4/Flash).
* Habilitar el **Local Server** en el puerto `1234` garantizando el endpoint estándar de OpenAI (`/v1/chat/completions`).

---

## 🚀 Instalación y Uso

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TU_USUARIO/DJ-Youtube-Music.git](https://github.com/TU_USUARIO/DJ-Youtube-Music.git)
   cd DJ-Youtube-Music
