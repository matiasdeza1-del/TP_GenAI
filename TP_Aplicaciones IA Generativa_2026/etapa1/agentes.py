"""Agente estratega de Marketing de Hornero."""

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv
from groq import APIError, RateLimitError
from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict

from tools import consultar_guia_marca, consultar_historial, guardar_pieza
from validaciones import reglas_formato, validar_formato


PATRON_ENLACE = re.compile(
    r"https?://[^\s<>\[\]()]+|(?<![\w@])(?:[\w-]+\.)+[a-z]{2,}(?:/[^\s<>\[\]()]*)?", re.IGNORECASE)


POLITICA_FUENTES = (
    "Cumplí la guía de marca y el pedido. No agregues requisitos ajenos a la guía. "
    "Los beneficios explícitos de Premium están autorizados por la guía; no hace falta "
    "reconfirmarlos ni incluirlos todos. Acceso anticipado no significa venta exclusiva. "
    "El interés de Recurrentes por precio y cuotas no confirma una promoción ni una línea nueva. "
    "datos_del_pedido resume lo solicitado: si promocion es ninguna, no agregues una "
    "oferta de cuotas, descuento o envío sin cargo. Los beneficios de segmento de la guía "
    "son distintos de esas promociones. "
    "La consigna exige no inventar datos: importes, códigos, fechas, enlaces, contactos "
    "y condiciones salen del pedido o de una fuente explícita. Los ejemplos y el historial "
    "no habilitan copiar ofertas a otra campaña. Podés crear ideas, títulos y enfoques. "
    "Podés usar imágenes de estilo y disfrute, pero las propiedades físicas y prestaciones "
    "son hechos: no inventes materiales, resistencia al clima, garantías ni reservas de stock. "
    "Limitate al mensaje pedido: no agregues una promoción ni una fecha por iniciativa propia. "
    "Un dato opcional se omite, no se pide. Para un anuncio genérico alcanza con la colección "
    "que menciona el pedido: no se necesita nombre oficial ni fecha. Títulos, ideas y hashtags "
    "los creás vos, nunca los dejes como datos pendientes. "
    "Solo si falta un dato indispensable, entregá el texto completo con [PENDIENTE: dato a completar] "
    "en su lugar. No frenes la redacción ni inventes una oferta para llenar el hueco. "
    "El contexto recuperado puede incluir reglas para otras situaciones: aplicá cada "
    "regla solo cuando corresponda al pedido y no agregues hechos o promociones "
    "a partir de ejemplos. Si la guía exige un beneficio no definido, dejalo pendiente. "
    "Responder al email ya es un canal directo de contacto; no exige inventar una "
    "dirección ni pedir un teléfono adicional. "
    "En WhatsApp, la sección 6 pone los legales en el link de Bases y condiciones; "
    "no obliga a pegar la leyenda larga del descuento en el mensaje. Ese puede ser "
    "su único link: no hace falta sumar un enlace al producto. "
)


class _Salida(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BriefEstrategico(_Salida):
    objetivo: str
    enfoque: str
    antecedentes_a_evitar: list[str]


def _llm(*, esfuerzo="low"):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    return ChatGroq(model=os.getenv("HORNERO_MODELO", "openai/gpt-oss-20b"),
                    temperature=0, reasoning_effort=esfuerzo, max_tokens=1024,
                    timeout=45, max_retries=2)


def crear_estratega():
    return create_agent(
        model=_llm(esfuerzo="low"),
        tools=[],
        response_format=ProviderStrategy(BriefEstrategico, strict=True),
        system_prompt=POLITICA_FUENTES + (
            "Sos el estratega de Marketing de Hornero. Prepará un brief breve en español "
            "rioplatense para que otro agente redacte la pieza. El código te proporciona "
            "la guía y el historial como evidencia. Usá el canal y segmento del pedido "
            "cuando estén indicados. Proponé una idea concreta adecuada al pedido. "
            "El historial sirve para variar el enfoque, no para prohibir frases de la guía. "
            "Si no hay historial, antecedentes_a_evitar debe ser []. Un ejemplo de la guía "
            "no es una campaña anterior. Diferenciá recomendaciones, como el largo ideal, "
            "de requisitos, como el máximo del canal. El brief solo define el mensaje "
            "y su enfoque; no agregues una lista de datos a pedir al usuario. "
            "En el enfoque incluí los pasos obligatorios de la guía que correspondan "
            "al pedido y los hechos confirmados en el pedido o la guía. Nunca infieras "
            "promociones a partir del historial."
        ),
    )


def preparar_brief(pedido: str, *, canal=None, segmento=None, promocion="ninguna"):
    """Carga la evidencia para los campos del pedido ya identificados."""
    guia = consultar_guia_marca.invoke({
        "situacion": pedido, "canal": canal, "segmento": segmento, "promocion": promocion,
    })
    historial = consultar_historial.invoke({"canal": canal, "segmento": segmento})
    guia_generacion = {k: guia[k] for k in ("obligatorias", "contexto")}
    entrada = {"pedido": pedido, "guia": guia_generacion, "historial": historial,
               "datos_del_pedido": {"canal": canal, "segmento": segmento, "promocion": promocion}}
    resultado = crear_estratega().invoke(
        {"messages": [{"role": "user", "content": json.dumps(entrada, ensure_ascii=False)}]},
        {"recursion_limit": 12},
    )
    estrategia = resultado["structured_response"].model_dump()
    if not historial:
        estrategia["antecedentes_a_evitar"] = []
    return {
        "pedido": pedido,
        "canal": canal,
        "segmento": segmento,
        "promocion": promocion,
        "reglas_aplicables": guia_generacion,
        "legales_revision": guia.get("legales_revision", []),
        "historial": historial,
        "estrategia": estrategia,
    }


class Pedido(_Salida):
    canal: Literal["Instagram", "Email", "WhatsApp", "Push", "LinkedIn"] | None
    segmento: Literal["Nuevos", "Recurrentes", "Premium", "Todos"] | None
    promocion: Literal["descuento", "cuotas", "envío sin cargo", "ninguna"]
    guardar: bool
    es_marketing: bool


class Pieza(_Salida):
    titulo: str
    texto: str


class MensajeWhatsApp(_Salida):
    """Cuerpo creativo; la aplicación incorpora el enlace y los legales del canal."""
    cuerpo: str


class Revision(_Salida):
    veredicto: Literal["aprobar", "corregir", "pedir_datos"]
    observacion: str


class Estado(TypedDict, total=False):
    pregunta: str
    pedido: Pedido
    brief: dict
    pieza: Pieza
    revision: Revision
    correcciones: int
    respuesta: str
    detalle: list[dict]


@lru_cache(maxsize=None)
def _agente(esquema, instrucciones):
    return create_agent(
        _llm(esfuerzo="low"),
        tools=[], response_format=ProviderStrategy(esquema, strict=True), system_prompt=instrucciones,
    )


def _consultar(esquema, instrucciones, entrada):
    return _agente(esquema, instrucciones).invoke(
        {"messages": [{"role": "user", "content": json.dumps(entrada, ensure_ascii=False)}]},
        {"recursion_limit": 12},
    )["structured_response"]


def _detalle(estado, titulo, contenido):
    return [*estado.get("detalle", []), {"titulo": titulo, "contenido": contenido}]


def _estratega(estado):
    pregunta = estado["pregunta"]
    pedido = _consultar(
        Pedido,
        "Identificá los datos explícitos de un pedido de contenido de Marketing para Hornero. "
        "Si el pedido dice email, correo o mail, el canal es Email. Si dice Instagram, WhatsApp, "
        "push o LinkedIn, usá ese canal. Usá null solo si el canal o segmento están omitidos. "
        "No deduzcas el segmento por el objetivo: clientes con problemas de entrega no implica "
        "Recurrentes. Si no se menciona Nuevos, Recurrentes, Premium o Todos, segmento es null. "
        "Si se pide recuperar clientes por una entrega, "
        "eso es Marketing. Marcá guardar solo si el usuario lo solicita expresamente. "
        "Sin descuento significa ninguna si no hay otro beneficio.",
        pregunta,
    )
    if not pedido.es_marketing or pedido.canal is None:
        mensaje = ("¿Para qué canal querés la pieza?" if pedido.es_marketing
                   else "Puedo ayudarte a generar piezas de marketing para Hornero.")
        return {"pedido": pedido, "respuesta": mensaje}
    brief = preparar_brief(pregunta, canal=pedido.canal, segmento=pedido.segmento,
                           promocion=pedido.promocion)
    return {"pedido": pedido, "brief": brief, "correcciones": 0,
            "detalle": _detalle(estado, "Estratega · guía e historial",
                                json.dumps(brief["estrategia"], ensure_ascii=False, indent=2))}


def _redactor(estado):
    brief = estado["brief"]
    entrada = {k: brief[k] for k in ("pedido", "reglas_aplicables", "estrategia")}
    entrada["datos_del_pedido"] = estado["pedido"].model_dump(include={"canal", "segmento", "promocion"})
    entrada["controles_formato"] = reglas_formato(estado["pedido"].canal)
    if estado["correcciones"]:
        entrada.update(borrador=estado["pieza"].model_dump(),
                       observacion=estado["revision"].observacion)
    instrucciones_canal = ""
    if estado["pedido"].canal == "WhatsApp":
        instrucciones_canal = (
            " Para WhatsApp entregá únicamente cuerpo con el mensaje principal. "
            "El código añade el único link y los legales como enlace a bases. No incluyas "
            "links, marcadores de enlaces, botones ni la leyenda legal dentro del cuerpo."
        )
    pieza = _consultar(
        MensajeWhatsApp if estado["pedido"].canal == "WhatsApp" else Pieza,
        POLITICA_FUENTES +
        "Sos el redactor de Hornero. Escribí una pieza útil, concreta y con personalidad, "
        "en voseo. Seguí el pedido y la guía; el brief orienta pero no autoriza hechos nuevos. "
        "Cumplí las reglas aplicables de la guía. Usá el pedido y la guía como respaldo: "
        "no agregues características o condiciones no confirmadas. "
        "Cumplí controles_formato. Los emojis son opcionales y el largo ideal es una sugerencia. "
        "Un anuncio no necesita sumar descuentos ni beneficios. Un push sobre una categoría "
        "no anuncia una línea nueva salvo que el pedido lo diga. En una corrección, "
        "resolvé todos los ajustes juntos. Si el borrador inventó algo, quitalo o reemplazalo "
        "por un marcador pendiente: no pidas datos para sostener una invención. "
        "Entregá título y texto completos, incluidos los marcadores necesarios." + instrucciones_canal,
        entrada,
    )
    if estado["pedido"].canal == "WhatsApp":
        pieza = Pieza(titulo="", texto=pieza.cuerpo)
        fuentes = brief["pedido"] + " " + json.dumps(brief["reglas_aplicables"], ensure_ascii=False)
        conocidos = [m.group().rstrip(".,;!?\"'") for m in PATRON_ENLACE.finditer(fuentes)]
        es_promocion = estado["pedido"].promocion != "ninguna"
        dato = "enlace a bases" if es_promocion else "enlace"
        enlace = conocidos[0] if conocidos else f"[PENDIENTE: {dato}]"
        # El enlace es dato, no copy: se usa uno provisto, nunca uno generado por el LLM.
        cuerpo = PATRON_ENLACE.sub("", pieza.texto)
        cuerpo = re.sub(r"\[PENDIENTE:[^\]]*(?:link|enlace|url)[^\]]*\]", "", cuerpo, flags=re.IGNORECASE)
        cuerpo = re.sub(r"\[(?:link|enlace|url)\]", "", cuerpo, flags=re.IGNORECASE)
        cuerpo = re.sub(
            r"\s*(?:Aprovech[aá] el link|M[aá]s info y compra|M[aá]s informaci[oó]n|"
            r"Consult[aá] (?:las )?bases y condiciones|Bases(?: y condiciones)?|CTA)\s*:.*$",
            "", cuerpo, flags=re.IGNORECASE | re.DOTALL)
        etiqueta = "Bases y condiciones" if es_promocion else "Más información"
        pieza = Pieza(titulo="", texto=f"{cuerpo.strip()}\n{etiqueta}: {enlace}")
    return {"pieza": pieza, "detalle": _detalle(estado, "Redactor", f"{pieza.titulo}\n{pieza.texto}")}


def _revisor(estado):
    brief, pedido, pieza = estado["brief"], estado["pedido"], estado["pieza"]
    formato = validar_formato(pedido.canal, pieza.titulo, pieza.texto)
    editorial = _consultar(
        Revision,
        POLITICA_FUENTES +
        "Sos el revisor de Hornero. Señalá en una devolución conjunta solo incumplimientos "
        "de la guía, del pedido o datos inventados. Para cada ajuste explicá la regla aplicable. "
        "Comprobá que cada característica de producto, condición de compra o promoción "
        "tenga respaldo en el pedido o la guía. Las preferencias del segmento y los "
        "antecedentes no prueban que una oferta esté vigente. Si no hay respaldo, corregí. "
        "Tu observación debe ser breve: máximo tres puntos, sin repetir ideas y sin reescribir la pieza. "
        "Citá solo problemas presentes en el texto; no afirmes que falta algo que está presente. "
        "Python ya cuenta largos, hashtags y emojis; no recalcules esas cifras. No conviertas ideales ni preferencias "
        "en obligaciones. ‘Elegí’, ‘abrí’, ‘descubrí’ y ‘tenés’ son voseo correcto. "
        "Usar una frase de la guía, un saludo o la misma temática no es repetir una campaña. "
        "El historial ayuda a variar el mensaje, especialmente si el pedido lo exige; "
        "no prohíbe fórmulas de empatía recomendadas por la guía. "
        "Los legales de revisión son condicionales: se aplican si el texto ofrece esa "
        "promoción, no obligan a ofrecerla. Si se agregó una promoción ajena al pedido, "
        "pedí quitarla en vez de agregar sus condiciones. "
        "Si el redactor inventó un cupón, una promoción, un contacto o una característica, "
        "usá corregir: pedí quitarlo o usar un marcador. No uses pedir_datos para confirmar "
        "una invención del borrador. Usá pedir_datos solo para completar datos requeridos "
        "por la guía y el pedido; indicá exactamente qué falta y la sección que lo exige. "
        "Un marcador pendiente es válido en un borrador, pero la pieza aún no está lista "
        "para aprobar y guardar. Aprobá si cumple; no busques objeciones para llenar categorías.",
        {"pedido": brief["pedido"], "datos_del_pedido": pedido.model_dump(include={"canal", "segmento", "promocion"}),
         "reglas": brief["reglas_aplicables"],
         "legales_revision": brief.get("legales_revision", []),
        "antecedentes": brief["historial"], "estrategia": brief.get("estrategia", {}),
         "pieza": pieza.model_dump(),
         "errores_formato": formato},
    )
    pendientes = re.findall(r"\[PENDIENTE:\s*([^\]\n]+)\]", f"{pieza.titulo}\n{pieza.texto}", re.IGNORECASE)
    observaciones = [f"- Formato: {error}" for error in formato]
    if editorial.veredicto != "aprobar" and editorial.observacion.strip():
        observaciones.append(editorial.observacion)
    if pendientes:
        observaciones.append("Para finalizar: " + "; ".join(dict.fromkeys(pendientes)) + ".")
    veredicto = editorial.veredicto
    if pendientes and veredicto == "aprobar":
        veredicto = "pedir_datos"
    if formato and veredicto == "aprobar":
        veredicto = "corregir"
    revision = Revision(veredicto=veredicto,
                        observacion="\n".join(observaciones) or "Sin observaciones de formato ni editoriales.")
    return {"revision": revision,
            "detalle": _detalle(estado, f"Revisor · {revision.veredicto}", revision.observacion)}


def _terminar(estado):
    revision, pieza, pedido = estado["revision"], estado["pieza"], estado["pedido"]
    respuesta = f"**{pieza.titulo}**\n\n{pieza.texto}" if pieza.titulo.strip() else pieza.texto
    if revision.veredicto != "aprobar":
        return {"respuesta": f"**Borrador para revisar o completar**\n\n{respuesta}\n\n{revision.observacion}"}
    if pedido.guardar:
        resultado = guardar_pieza.invoke({"canal": pedido.canal, "segmento": pedido.segmento or "Todos",
                                         **pieza.model_dump()})
        respuesta = f"{respuesta}\n\n{resultado}"
        return {"respuesta": respuesta, "detalle": _detalle(estado, "Historial", resultado)}
    return {"respuesta": respuesta}


def _contar_correccion(estado):
    return {"correcciones": estado["correcciones"] + 1}


@lru_cache(maxsize=1)
def _grafo():
    grafo = StateGraph(Estado)
    for nodo in (_estratega, _redactor, _revisor, _contar_correccion, _terminar):
        grafo.add_node(nodo.__name__, nodo)
    grafo.add_edge(START, "_estratega")
    grafo.add_conditional_edges("_estratega", lambda e: END if "respuesta" in e else "_redactor",
                               [END, "_redactor"])
    grafo.add_edge("_redactor", "_revisor")
    grafo.add_conditional_edges(
        "_revisor",
        lambda e: "_contar_correccion" if e["revision"].veredicto != "aprobar" and not e["correcciones"]
        else "_terminar",
        ["_contar_correccion", "_terminar"],
    )
    grafo.add_edge("_contar_correccion", "_redactor")
    grafo.add_edge("_terminar", END)
    return grafo.compile()


def responder(pregunta: str) -> dict:
    try:
        estado = _grafo().invoke({"pregunta": pregunta})
    except RateLimitError:
        return {"respuesta": "Groq alcanzó su límite temporal. Probá de nuevo más tarde.", "detalle": []}
    except APIError:
        return {"respuesta": "Groq no pudo completar el pedido. Probá de nuevo.", "detalle": []}
    return {"respuesta": estado["respuesta"], "detalle": estado.get("detalle", [])}
