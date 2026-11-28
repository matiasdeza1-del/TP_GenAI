"""Pruebas técnicas sin API ni descarga del modelo de embeddings."""
import csv
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "etapa1"))

import agentes
import tools
from streamlit.testing.v1 import AppTest


class FlujoTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.historial = Path(self.temporal.name) / "historial.csv"
        shutil.copyfile(tools.HISTORIAL, self.historial)
        parche = patch.object(tools, "HISTORIAL", self.historial)
        parche.start()
        self.addCleanup(parche.stop)
        self.original = self.historial.read_bytes()
        agentes._grafo.cache_clear()
        self.addCleanup(agentes._grafo.cache_clear)

    def ejecutar(self, veredictos, guardar=True):
        revisiones = iter(veredictos)
        llamadas = []

        def consultar(esquema, instrucciones, entrada):
            llamadas.append(esquema)
            if esquema is agentes.Pedido:
                return agentes.Pedido(canal="Instagram", segmento="Premium",
                                      promocion="ninguna", guardar=guardar, es_marketing=True)
            if esquema is agentes.Pieza:
                return agentes.Pieza(titulo="Pieza de prueba",
                                     texto="Conocé la colección. #HorneroEnCasa #Exterior #Colección")
            veredicto = next(revisiones)
            return agentes.Revision(veredicto=veredicto, observacion="Observación de prueba.")

        brief = {"pedido": "Pedido de prueba", "reglas_aplicables": {}, "historial": [],
                 "estrategia": {"objetivo": "Comunicar", "enfoque": "Colección",
                                "antecedentes_a_evitar": [], "datos_faltantes": []}}
        with patch.object(agentes, "_consultar", side_effect=consultar), \
                patch.object(agentes, "preparar_brief", return_value=brief):
            resultado = agentes.responder("Pedido de prueba")
        self.assertIsInstance(resultado["respuesta"], str)
        self.assertIsInstance(resultado["detalle"], list)
        for paso in resultado["detalle"]:
            self.assertIn("titulo", paso)
            self.assertIn("contenido", paso)
        return resultado, llamadas

    def test_aprobacion_sin_pedido_de_guardado_no_escribe(self):
        self.ejecutar(["aprobar"], guardar=False)
        self.assertEqual(self.original, self.historial.read_bytes())

    def test_correccion_y_aprobacion_guarda_una_fila(self):
        with self.historial.open(encoding="utf-8-sig", newline="") as archivo:
            antes = list(csv.DictReader(archivo))
        resultado, llamadas = self.ejecutar(["corregir", "aprobar"])
        with self.historial.open(encoding="utf-8-sig", newline="") as archivo:
            despues = list(csv.DictReader(archivo))
        self.assertEqual(len(despues), len(antes) + 1)
        self.assertEqual(despues[-1]["titulo"], "Pieza de prueba")
        self.assertEqual(llamadas.count(agentes.Pieza), 2)
        self.assertIn("Pieza guardada", resultado["respuesta"])

    def test_segunda_correccion_termina_sin_escribir(self):
        resultado, llamadas = self.ejecutar(["corregir", "corregir"])
        self.assertEqual(llamadas.count(agentes.Revision), 2)
        self.assertIn("Borrador", resultado["respuesta"])
        self.assertIn("Conocé la colección", resultado["respuesta"])
        self.assertEqual(self.original, self.historial.read_bytes())

    def test_pedir_datos_termina_sin_escribir(self):
        resultado, llamadas = self.ejecutar(["pedir_datos", "pedir_datos"])
        self.assertEqual(llamadas.count(agentes.Pieza), 2)
        self.assertIn("Borrador", resultado["respuesta"])
        self.assertIn("Conocé la colección", resultado["respuesta"])
        self.assertEqual(self.original, self.historial.read_bytes())

    def test_whatsapp_sin_enlace_pasa_por_agentes_y_muestra_borrador(self):
        pedido = agentes.Pedido(canal="WhatsApp", segmento="Nuevos", promocion="descuento",
                                guardar=True, es_marketing=True)
        pieza = agentes.Pieza(titulo="", texto="Hola, tenés 15% en Cocina.")
        def consultar(esquema, instrucciones, entrada):
            if esquema is agentes.Pedido:
                return pedido
            if esquema is agentes.MensajeWhatsApp:
                return agentes.MensajeWhatsApp(cuerpo=pieza.texto)
            return agentes.Revision(veredicto="pedir_datos", observacion="Guía sección 6: falta enlace a bases.")
        brief = {"pedido": "WhatsApp con 15%", "reglas_aplicables": {}, "historial": [], "estrategia": {}}
        with patch.object(agentes, "_consultar", side_effect=consultar) as consulta, \
                patch.object(agentes, "preparar_brief", return_value=brief):
            resultado = agentes.responder(
                "Proponé un WhatsApp para Nuevos con un 15% de descuento en Cocina y guardalo.")
        self.assertGreater(consulta.call_count, 1)
        self.assertTrue(any(p["titulo"] == "Redactor" for p in resultado["detalle"]))
        self.assertIn(pieza.texto, resultado["respuesta"])
        self.assertIn("[PENDIENTE: enlace a bases]", resultado["respuesta"])
        self.assertEqual(self.original, self.historial.read_bytes())

    def test_revision_reune_formato_y_ortografia_desde_primera_pasada(self):
        estado = {
            "pregunta": "Post de Instagram", "pedido": agentes.Pedido(
                canal="Instagram", segmento="Premium", promocion="ninguna", guardar=False, es_marketing=True),
            "brief": {"pedido": "Post de Instagram", "reglas_aplicables": {}, "historial": []},
            "pieza": agentes.Pieza(titulo="Colección", texto="Elegi " + "x" * 2200 + " 🌿✨🏡🌞"),
        }
        with patch.object(agentes, "_consultar", return_value=agentes.Revision(
                veredicto="corregir", observacion="Voz y tono: corregí Elegi por Elegí.")):
            revision = agentes._revisor(estado)["revision"]
        self.assertEqual(revision.veredicto, "corregir")
        for hallazgo in ("2200", "hashtags", "#HorneroEnCasa", "emojis", "Elegí"):
            self.assertIn(hallazgo, revision.observacion)

    def test_datos_faltantes_conservan_otros_hallazgos(self):
        estado = {
            "pregunta": "Post de Instagram", "pedido": agentes.Pedido(
                canal="Instagram", segmento="Premium", promocion="ninguna", guardar=True, es_marketing=True),
            "brief": {"pedido": "Post de Instagram", "reglas_aplicables": {}, "historial": []},
            "pieza": agentes.Pieza(titulo="Colección", texto="Elegi la colección."),
        }
        with patch.object(agentes, "_consultar", return_value=agentes.Revision(
                veredicto="pedir_datos", observacion="Corregí Elegi por Elegí. Sección 6: falta vigencia.")):
            revision = agentes._revisor(estado)["revision"]
        self.assertEqual(revision.veredicto, "pedir_datos")
        self.assertIn("hashtags", revision.observacion)
        self.assertIn("Elegí", revision.observacion)
        self.assertIn("vigencia", revision.observacion)

    def test_python_no_prohibe_el_cta_literal_de_la_guia_para_push(self):
        estado = {
            "pregunta": "Push sobre aires", "pedido": agentes.Pedido(
                canal="Push", segmento="Recurrentes", promocion="ninguna", guardar=False, es_marketing=True),
            "brief": {"pedido": "Push sobre aires", "reglas_aplicables": {}, "historial": []},
            "pieza": agentes.Pieza(titulo="Aires acondicionados", texto="Abre la app"),
        }
        with patch.object(agentes, "_consultar", return_value=agentes.Revision(
                veredicto="aprobar", observacion="Cumple.")):
            revision = agentes._revisor(estado)["revision"]
        self.assertEqual(revision.veredicto, "aprobar")

    def test_marcadores_no_se_guardan_como_piezas_aprobadas(self):
        estado = {
            "pregunta": "WhatsApp", "pedido": agentes.Pedido(
                canal="WhatsApp", segmento="Nuevos", promocion="ninguna", guardar=True, es_marketing=True),
            "brief": {"pedido": "WhatsApp", "reglas_aplicables": {}, "historial": []},
            "pieza": agentes.Pieza(titulo="", texto="Consultá [PENDIENTE: enlace a bases]"),
        }
        with patch.object(agentes, "_consultar", return_value=agentes.Revision(
                veredicto="aprobar", observacion="Cumple.")):
            estado.update(agentes._revisor(estado))
        resultado = agentes._terminar(estado)
        self.assertEqual(estado["revision"].veredicto, "pedir_datos")
        self.assertIn(estado["pieza"].texto, resultado["respuesta"])
        self.assertEqual(self.original, self.historial.read_bytes())

    def test_sin_historial_no_se_inventan_antecedentes(self):
        estrategia = agentes.BriefEstrategico(objetivo="Anunciar", enfoque="Colección",
            antecedentes_a_evitar=["Ejemplo mal de la guía"])
        with patch.object(agentes, "consultar_guia_marca") as guia, \
                patch.object(agentes, "consultar_historial") as historial, \
                patch.object(agentes, "crear_estratega") as crear:
            guia.invoke.return_value = {"obligatorias": [], "contexto": []}
            historial.invoke.return_value = []
            crear.return_value.invoke.return_value = {"structured_response": estrategia}
            brief = agentes.preparar_brief("Post Premium", canal="Instagram", segmento="Premium")
        self.assertEqual(brief["estrategia"]["antecedentes_a_evitar"], [])

    def test_rag_no_mezcla_promociones_ni_canales_ajenos_al_pedido(self):
        chunks = [
            "Promociones y legales obligatorios — Envío sin cargo: monto mínimo.",
            "Reglas por canal — Canal: WhatsApp | 300 caracteres",
            "Segmentos de clientes y cómo hablarles — Nuevos: variedad",
            "Ejemplos — Cupón de otra campaña",
            "Reglas por canal — Canal: Instagram (post) | 3 a 5 hashtags",
            "Segmentos de clientes y cómo hablarles — Premium: acceso anticipado",
            "Voz y tono — La voz de Hornero es cálida.",
            "Voz y tono — El tono se ajusta según la situación.",
        ]
        modelo, indice = MagicMock(), MagicMock()
        indice.search.return_value = (None, [list(range(len(chunks)))])
        with patch.object(tools, "_cargar_guia", return_value=(modelo, indice, chunks)):
            resultado = tools.consultar_guia_marca.invoke({
                "situacion": "Anuncio de muebles", "canal": "Instagram", "segmento": "Premium"})
        evidencia = " ".join(resultado["obligatorias"] + resultado["contexto"])
        self.assertIn("Instagram", evidencia)
        self.assertIn("Premium", evidencia)
        for ajeno in ("Envío sin cargo", "WhatsApp", "Nuevos", "Ejemplos"):
            self.assertNotIn(ajeno, evidencia)

    def test_redactor_sustituye_enlace_inventado_sin_exigir_verificacion_del_sitio(self):
        pedido = agentes.Pedido(canal="WhatsApp", segmento="Nuevos", promocion="descuento",
                                guardar=True, es_marketing=True)
        for enlace, dado in (("bit.ly/inventado", False), ("https://example.com/bases", True)):
            with self.subTest(enlace=enlace):
                estado = {"pedido": pedido, "correcciones": 0,
                    "brief": {"pedido": "15% en Cocina" + (" Bases: " + enlace if dado else ""),
                              "reglas_aplicables": {}, "estrategia": {}}}
                pieza = agentes.Pieza(titulo="", texto="Tenés 15% en Cocina. Bases: " + enlace)
                with patch.object(agentes, "_consultar", return_value=agentes.MensajeWhatsApp(cuerpo=pieza.texto)):
                    salida = agentes._redactor(estado)["pieza"]
                if dado:
                    self.assertEqual(salida.texto.count(enlace), 1)
                    self.assertNotIn("[PENDIENTE:", salida.texto)
                else:
                    self.assertNotIn(enlace, salida.texto)
                    self.assertIn("[PENDIENTE: enlace a bases]", salida.texto)

    def test_whatsapp_conserva_el_texto_para_que_el_revisor_pueda_evaluarlo(self):
        estado = {"pedido": agentes.Pedido(canal="WhatsApp", segmento="Nuevos", promocion="descuento",
                    guardar=False, es_marketing=True), "correcciones": 0,
                  "brief": {"pedido": "15% en Cocina", "reglas_aplicables": {}, "estrategia": {}}}
        cuerpo = "Hola, tenés 15% en Cocina. Usá el código COCINA15. Aprovechá el link: bit.ly/falso y consultá bases y condiciones:"
        with patch.object(agentes, "_consultar", return_value=agentes.MensajeWhatsApp(cuerpo=cuerpo)):
            salida = agentes._redactor(estado)["pieza"].texto
        self.assertIn("tenés 15% en Cocina", salida)
        self.assertIn("COCINA15", salida)
        self.assertNotIn("Aprovechá el link", salida)
        self.assertEqual(salida.count("Bases y condiciones:"), 1)
        self.assertEqual(salida.count("[PENDIENTE:"), 1)

    def test_app_muestra_respuesta_y_detalle(self):
        respuesta = {"respuesta": "Respuesta técnica de prueba", "detalle": [
            {"titulo": "Paso de prueba", "contenido": "Sin llamada externa"}]}
        with patch.object(agentes, "responder", return_value=respuesta):
            app = AppTest.from_file(str(BASE / "etapa1/main.py"), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0)
            app.chat_input[0].set_value("Consulta de prueba").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.chat_message), 2)
        self.assertTrue(any("Respuesta técnica" in item.value for item in app.markdown))
        self.assertEqual(self.original, self.historial.read_bytes())


if __name__ == "__main__":
    unittest.main()
