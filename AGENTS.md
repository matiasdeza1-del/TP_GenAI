# Trabajo en este repositorio

## Antes de cambiar código

1. Leer `README.md`, `docs/ROADMAP.md` y la bitácora de la etapa afectada.
2. Revisar `git status` y el código actual. No sobrescribir cambios de otra persona.
3. Identificar la tarea por su ID del roadmap. Si es nueva, agregarla sin duplicar otra.
4. La consigna es `TP_Aplicaciones IA Generativa_2026/Consigna_TP.pdf`. Ante diferencias, explicarlas; no inventar requisitos.

## Arquitectura y alcance

- La implementación de Marketing vive en `TP_Aplicaciones IA Generativa_2026/etapa1/`.
- Los ejemplos originales viven en `TP_Aplicaciones IA Generativa_2026/ejemplos/`; su interfaz es `main_ejemplo.py` y sus módulos son `agentes_ejemplo.py` y `tools_ejemplo.py`.
- `etapa2/` contiene por ahora documentación de diseño, no una aplicación terminada.
- Conservar las aplicaciones independientes `etapa1/main.py` y `etapa2/main.py` que exige la consigna.
- Mantener `responder(pregunta) -> {"respuesta": str, "detalle": list[dict]}` y pasos con `titulo` y `contenido`.
- Separar interfaz, coordinación, herramientas y acceso a datos. Crear módulos nuevos cuando haya una responsabilidad concreta, sin armar frameworks anticipadamente.
- Los datos de referencia viven en `datos/`. Las pruebas de escritura usan copias temporales del CSV.
- En Marketing prima la guía de marca para reglas y beneficios explícitos del segmento. Premium puede comunicar acceso anticipado sin reconfirmarlo por campaña. El pedido aporta detalles particulares; ejemplos, historial y textos de legales no autorizan promociones nuevas. No agregar restricciones que contradigan esa política en un prompt de un rol aislado.
- Diferenciar datos concretos verificables de expresiones publicitarias generales: no inventar precios, plazos, códigos, condiciones, garantías ni especificaciones, pero no bloquear lenguaje general de estilo, comodidad o durabilidad solo por falta de una ficha técnica. Respetar las prohibiciones de la guía.
- Los bloqueos editoriales deben corresponder a requisitos de la guía o de la consigna. Una recomendación no es una prohibición. Si faltan datos, entregar la pieza completa como borrador con marcadores `[PENDIENTE: dato]`; no sustituirla por una negativa ni pedir datos para sostener una oferta inventada por el redactor. Los borradores incompletos no van al CSV de aprobados.

## Implementación y verificación

- No leer ni imprimir secretos de `.env`. Usar variables de entorno y compartir solo `.env.example`.
- Usar UTF-8 explícito al leer/escribir texto; rutas basadas en `Path(__file__)` para datos.
- No usar `ejemplos/ejemplo_mcp.py` como prueba de imports: ejecuta conexiones y llamadas externas al importarse.
- Mantener compatibles con Windows y macOS los cambios de código; documentar comandos y dependencias específicos de cada plataforma por separado.
- Ejecutar `python -m unittest discover -s tests -v` desde la carpeta del TP para cambios del flujo.
- Ejecutar `python scripts/verificar_funcionamiento.py` para verificar dependencias, RAG y ambas interfaces. `--live` agrega una consulta real a Groq; tiene consumo de API.
- Una respuesta de error del proveedor no cuenta como integración exitosa. Distinguir pruebas simuladas, pruebas reales y evaluación editorial.
- No evaluar calidad de contenido cuando la tarea solo pide funcionamiento.
- No agregar skills por defecto. Automatizar primero con comandos o scripts versionados que todo el equipo pueda ejecutar.

## Al cerrar una tarea

- Actualizar el estado y evidencia en `docs/ROADMAP.md`; no marcar terminado algo no probado.
- Registrar decisiones, alternativas y resultados en la bitácora correspondiente. El roadmap conserva estado actual; la bitácora conserva historia.
- Explicar cambios, comandos ejecutados y límites pendientes. No hacer commits, push o publicaciones sin que estén pedidos.
- No asignar responsables humanos por suposición. Usar `Sin asignar` hasta que el equipo lo acuerde.
