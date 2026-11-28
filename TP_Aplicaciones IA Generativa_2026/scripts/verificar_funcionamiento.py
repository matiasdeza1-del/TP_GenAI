"""Smoke test técnico. --live agrega Groq; nunca modifica el CSV de entrega."""
import argparse
import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "etapa1"))


def verificar(live=False):
    for nombre in ("streamlit", "groq", "langchain", "langchain_groq", "langgraph",
                   "langchain_community", "sqlalchemy", "langchain_mcp_adapters",
                   "mcp_weather_server", "pdfplumber", "sentence_transformers", "faiss",
                   "sklearn", "lightgbm", "joblib", "pandas"):
        importlib.import_module(nombre)
    print("OK: imports de dependencias", flush=True)

    # Cada interfaz en su proceso, con una entrada y un título explícitos.
    for carpeta, archivo, titulo in (
        (BASE / "ejemplos", "main_ejemplo.py", "Ejemplo básico"),
        (BASE / "etapa1", "main.py", "Etapa 1 · Marketing"),
    ):
        codigo = (
            "import sys; from streamlit.testing.v1 import AppTest; "
            "a = AppTest.from_file(sys.argv[1], default_timeout=60).run(); "
            "assert not len(a.exception), str(a.exception); "
            "assert sys.argv[2] in a.title[0].value; "
            "assert len(a.chat_input) == 1; print('OK: interfaz inicial')"
        )
        resultado = subprocess.run([sys.executable, "-c", codigo, archivo, titulo], cwd=carpeta,
                                   capture_output=True, text=True, encoding="utf-8",
                                   env={**os.environ, "PYTHONIOENCODING": "utf-8",
                                        "GROQ_API_KEY": "functional-test-no-api-call"}, timeout=120)
        if resultado.returncode:
            # No volcar trazas que puedan contener argumentos con credenciales.
            raise RuntimeError(f"La interfaz de {carpeta.name} falló; revisar con AppTest local")
        print(f"OK: arranque de {carpeta.relative_to(BASE)}/{archivo}", flush=True)

    import agentes
    import tools
    from rag_guia import abrir_indice, extraer_chunks

    origen = tools.HISTORIAL
    original = origen.read_bytes()
    with tempfile.TemporaryDirectory() as temporal:
        copia = Path(temporal) / "historial.csv"
        shutil.copyfile(origen, copia)
        tools.HISTORIAL = copia
        try:
            fragmentos = extraer_chunks()
            assert fragmentos, "El PDF no produjo fragmentos"
            inicio = time.perf_counter()
            reglas = tools.consultar_guia_marca.invoke({
                "situacion": "WhatsApp para Nuevos con descuento en Cocina",
                "canal": "WhatsApp", "segmento": "Nuevos", "promocion": "descuento"})
            for referencia in ("Canal: WhatsApp", "— Nuevos:", "— Descuentos:"):
                assert any(referencia in regla for regla in reglas["obligatorias"]), "Falta regla: " + referencia
            modelo, indice, chunks = tools._cargar_guia()
            indice2, chunks2 = abrir_indice(modelo)
            assert chunks == chunks2 and indice.ntotal == indice2.ntotal == len(chunks)
            print(f"OK: PDF, embeddings, FAISS, persistencia y recuperación ({len(chunks)} chunks, "
                  f"{time.perf_counter() - inicio:.1f}s)", flush=True)
            assert tools.consultar_historial.invoke({"canal": "Push", "segmento": "Recurrentes"})
            tools.guardar_pieza.invoke({"canal": "Push", "segmento": "Todos",
                                       "titulo": "Prueba técnica", "texto": "Texto de prueba."})
            assert copia.read_bytes() != original
            print("OK: lectura y escritura de historial temporal", flush=True)

            if live:
                from dotenv import load_dotenv
                load_dotenv(BASE / ".env")
                assert os.getenv("GROQ_API_KEY"), "Falta GROQ_API_KEY"
                inicio = time.perf_counter()
                salida = agentes.responder(
                    "Armá un post de Instagram para clientes Premium anunciando la nueva "
                    "colección de muebles de exterior. No lo guardes.")
                assert isinstance(salida["respuesta"], str) and salida["respuesta"].strip()
                pasos = [p["titulo"] for p in salida["detalle"]]
                assert any(p.startswith("Estratega") for p in pasos), "No completó estrategia"
                assert "Redactor" in pasos, "No completó redacción"
                assert any(p.startswith("Revisor") for p in pasos), "No completó revisión"
                print(f"OK: Groq y grafo real ({len(pasos)} pasos, "
                      f"{time.perf_counter() - inicio:.1f}s); sin evaluación editorial", flush=True)
        finally:
            tools.HISTORIAL = origen
            assert origen.read_bytes() == original, "Cambió el CSV original"
    print("OK: CSV de entrega intacto", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Incluir llamada real a Groq")
    args = parser.parse_args()
    try:
        verificar(args.live)
    except Exception as error:
        # El tipo y un mensaje controlado bastan; no imprimir valores de configuración.
        print(f"FALLO: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
