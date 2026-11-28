# TP de Aplicaciones de IA Generativa · Hornero

Asistente interno de un e-commerce ficticio. El TP requiere dos aplicaciones: Marketing secuencial (Etapa 1) y un asistente que coordine Marketing, RRHH y Supply chain (Etapa 2).

## Orientación

- [Estado y tareas](docs/ROADMAP.md): fuente única del avance actual.
- [Arquitectura y colaboración](docs/ARQUITECTURA.md): diagnóstico y propuesta para el equipo.
- [Bitácora general](docs/BITACORA.md): decisiones y verificaciones transversales.
- [Bitácora de Etapa 1](TP_Aplicaciones%20IA%20Generativa_2026/etapa1/criterios.md): historia de Marketing.
- [Bitácora de Etapa 2](TP_Aplicaciones%20IA%20Generativa_2026/etapa2/criterios.md): decisiones de la extensión.
- [Instrucciones para IA](AGENTS.md): reglas de trabajo en el repositorio.

`TP_Aplicaciones IA Generativa_2026/etapa1/` contiene la aplicación desarrollada. Los ejemplos originales están separados en `TP_Aplicaciones IA Generativa_2026/ejemplos/`, con la interfaz `main_ejemplo.py`. `Clase 1 - LLMs Intro/` y `Clase 3/` son material auxiliar. La raíz del TP ya no contiene un `main.py` de ejemplo.

## Instalación en Windows / PowerShell

Desde la raíz del repositorio, usar Python 3.12 y un entorno con ruta corta: PyTorch puede superar el límite de rutas de Windows si se instala dentro de este checkout de OneDrive.

```powershell
python -m venv "$env:USERPROFILE\.venvs\hornero-tp312"
& "$env:USERPROFILE\.venvs\hornero-tp312\Scripts\Activate.ps1"
cd '.\TP_Aplicaciones IA Generativa_2026'
python -m pip install -r requirements.txt
```

Para reproducir las versiones del entorno verificado, usar `requirements-lock.txt` en lugar de `requirements.txt`. El lock corresponde a Windows/Python 3.12; en otra plataforma puede requerir resolver dependencias con `requirements.txt` y volver a verificar.

Marketing usa `openai/gpt-oss-20b` en Groq y respuestas JSON nativas para los datos que pasan entre agentes. El modelo se puede cambiar con `HORNERO_MODELO` en `.env` y reiniciando la aplicación; el modo actual requiere soporte de JSON Schema nativo. La configuración es igual en Windows y macOS. Los ejemplos originales conservan su modelo de referencia.

Solo si todavía no existe `.env`, copiar la plantilla y completar la clave localmente:

```powershell
Copy-Item .env.example .env
```

No compartir `.env` ni el entorno virtual. `.gitignore` mantiene ambos fuera de los archivos nuevos de Git.

## Ejecutar Marketing

Desde la carpeta del TP, con el entorno activo:

```powershell
cd etapa1
python -m streamlit run main.py
```

Abrir la dirección que imprime Streamlit. La interfaz es local, los embeddings y FAISS se ejecutan localmente y el modelo generativo usa Groq. La primera consulta RAG puede descargar el modelo de embeddings. El CSV editorial está en `datos/etapa1/contenidos_aprobados.csv`.

La Etapa 2 aún no tiene aplicación ejecutable.

## Ejecutar los ejemplos originales

Desde la carpeta del TP, con el entorno activo, tanto en Windows como en macOS:

```sh
cd ejemplos
python -m streamlit run main_ejemplo.py
```

Esta interfaz dice **Hornero · Ejemplo básico** y solo dispone de la herramienta de fecha. La aplicación desarrollada dice **Hornero · Etapa 1 · Marketing**. Ambas leen la configuración local del mismo `.env` de la carpeta del TP.

El demo independiente de MCP se ejecuta desde `ejemplos/` con `python ejemplo_mcp.py`; conecta a DeepWiki y consume API de Groq.

## Verificar funcionamiento

Desde la carpeta del TP:

```powershell
python -m pip check
python -m unittest discover -s tests -v
python scripts/verificar_funcionamiento.py
python scripts/verificar_funcionamiento.py --live
```

Las pruebas unitarias verifican rutas del grafo, persistencia temporal e interfaz con el modelo simulado. El script comprueba imports, RAG real y arranque de interfaces. `--live` verifica además el recorrido completo de Marketing con Groq; consume API y requiere clave. No califica calidad editorial ni prueba un flujo de clima todavía no implementado.

## Colaboración

Tomar una tarea del roadmap, acordar responsable y trabajar en una rama por tarea, por ejemplo `feat/E2-02-politicas`. Integrar mediante un PR pequeño con problema, cambio y evidencia de pruebas. Otra persona revisa antes de integrar a `main`; configurar protección de rama en GitHub queda como tarea del equipo.

Cada integrante usa su propio clon, `.env` y entorno. Evitar trabajar sobre una misma carpeta sincronizada por OneDrive. Para conversaciones con IA: indicar ID de tarea y pedir lectura de `AGENTS.md` y del roadmap. Mantener bitácoras por etapa y registrar solo decisiones o resultados relevantes, sin pegar conversaciones completas.
