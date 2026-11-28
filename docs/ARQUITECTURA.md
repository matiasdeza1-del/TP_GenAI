# Arquitectura y trabajo en equipo

## Diagnóstico del checkout

La Etapa 1 tiene una separación razonable para el tamaño del TP: `main.py` presenta, `agentes.py` coordina, `tools.py` accede a guía/historial, `rag_guia.py` gestiona recuperación y `validaciones.py` comprueba formatos de canal sin LLM. Mantener carpetas por etapa coincide con el entregable. No hay necesidad actual de microservicios ni de una migración completa a `src/`.

El revisor devuelve un veredicto y una observación conjunta contra guía y pedido. Python suma los incumplimientos objetivos de formato. Siempre se muestra la pieza: si hay datos sin definir, se entrega como borrador con marcadores y aclaraciones. La ronda de corrección acotada limita llamadas, no oculta el trabajo producido. Solo las piezas completas y aprobadas que el usuario pidió guardar se agregan al historial.

Los roles usan `create_agent` con `ProviderStrategy`: Groq entrega el JSON de cada esquema de forma nativa, sin simular una herramienta para devolverlo. El modelo predeterminado es `openai/gpt-oss-20b`, configurable mediante `HORNERO_MODELO`. Este control es del formato de intercambio, no una restricción editorial. Referencias: [Structured Outputs de Groq](https://console.groq.com/docs/structured-outputs) y [ProviderStrategy de LangChain](https://docs.langchain.com/oss/python/langchain/structured-output).

El repositorio estaba preparado como prototipo individual: no tenía README, gitignore, guía de contribución, instrucciones para IA, tests versionados ni versiones resueltas de dependencias. La bitácora de Marketing conserva buena evidencia, pero mezcla decisiones históricas y pendientes que luego se resolvieron. Esto dificulta identificar el estado vigente.

Riesgos concretos:

- La confusión entre dos `main.py` con la misma pantalla se resolvió separando los ejemplos en `ejemplos/`, renombrando sus módulos y distinguiendo los títulos de ambas interfaces.
- Los imports `from tools import ...` y `from agentes import ...` dependen de qué carpeta se ejecuta y colisionarían al reutilizar Marketing ingenuamente desde Etapa 2.
- `agentes.py` concentra esquemas, prompts y grafo. Es tolerable hoy; separar por responsabilidad al extenderlo.
- El CSV es tanto entrada como salida. No tiene bloqueo ni deduplicación; no sirve como almacenamiento compartido con escritores concurrentes. Usar un clon por persona y consolidar las piezas de entrega conscientemente.
- Los índices son regenerables y su firma depende del código fuente. Un cambio de código o de finales de línea puede forzar reconstrucción.
- Agregar paquetes sin versiones permite que cada integrante obtenga combinaciones distintas.
- No se inspeccionaron permisos de GitHub, protección de rama ni CI remoto: no se puede afirmar que estén configurados.

## Organización propuesta

Conservar la estructura ejecutable por etapas. Los ejemplos originales se trasladaron a `ejemplos/` y usan nombres explícitos (`main_ejemplo.py`, `agentes_ejemplo.py`, `tools_ejemplo.py`), con rutas de datos y configuración ajustadas. `ejemplo_mcp.py` también vive allí como material de referencia. La implementación se inicia desde `etapa1/`.

```text
README.md                       Cómo orientarse, instalar, ejecutar y probar
AGENTS.md                       Reglas estables para asistentes de IA
docs/
  ROADMAP.md                    Estado actual y responsables
  BITACORA.md                   Decisiones transversales y verificaciones
  ARQUITECTURA.md                Este documento
TP_Aplicaciones IA Generativa_2026/
  requirements.txt              Dependencias directas
  requirements-lock.txt         Versiones del entorno verificado
  datos/                        Fuentes compartidas y CSV de entrega
  ejemplos/                     Material original de referencia
    main_ejemplo.py              Chat del agente básico de fecha
    agentes_ejemplo.py           Agente original
    tools_ejemplo.py             Herramienta original
    ejemplo_mcp.py               Demo independiente de DeepWiki
  etapa1/                       Aplicación Marketing existente
    criterios.md                Bitácora de Marketing
  etapa2/                       Aplicación futura; hoy solo criterios.md
    criterios.md                Bitácora de RRHH, Supply y orquestación
  tests/                        Pruebas técnicas reproducibles
  scripts/                      Verificaciones comunes
```

## Diseño propuesto para Etapa 2 (pendiente de implementar)

Un orquestador identifica el área y delega en especialistas, en lugar de aplicar la misma cadena a todos los pedidos:

```text
Chat -> Orquestador -> Marketing: reutiliza el grafo de Etapa 1
                   -> RRHH: RAG de políticas, SQL empleados y modelo attrition
                   -> Supply: SQL ventas, modelo ventas y pronóstico MCP
                   -> Fuera de alcance: rechazo
```

Preservar `main.py`, `agentes.py` y `tools.py` de Etapa 2. Agregar módulos `rrhh.py`, `supply.py`, `entrenar_modelos.py` y adaptador de Marketing cuando existan esas responsabilidades. Cada especialista recibe únicamente herramientas y datos de su área. SQL en modo solo lectura. Modelos entrenados fuera del pedido y cargados para inferencia. Medición con `perf_counter()` alrededor del punto de entrada.

Antes de conectar Marketing, resolver imports como paquete/adaptador con una prueba de que ambas apps siguen arrancando desde su propia carpeta. No copiar su implementación a Etapa 2: dos copias divergirían. La extracción de un módulo compartido solo se justifica cuando ambas etapas lo consuman.

## Trabajo con IA y bitácoras

Usar un único `AGENTS.md` raíz y un roadmap global. Las instrucciones obligan a leer el roadmap al empezar y actualizarlo al cerrar. El estado sigue dependiendo de que la herramienta cargue esas instrucciones y de que el equipo las mantenga: no es sincronización automática entre conversaciones.

Las bitácoras sirven para todos. Formato recomendado: fecha, autor o rama, tarea, cambio/decisión, alternativa, comando y resultado, próximo paso. Agregar entradas nuevas sin reescribir el historial. Corregir el estado vigente en el roadmap. Para reducir conflictos, cada rama registra entradas cortas sobre su propia etapa.

No crear skills todavía: serían otra fuente de instrucciones que instalar y mantener. Los scripts compartidos resuelven la repetición inmediata. Evaluar una skill solo si una rutina larga y estable se repite en varias tareas o repositorios y no alcanza con un comando documentado. Tampoco crear varios `AGENTS.md` mientras no haya reglas locales diferentes.

Propuesta de cuatro frentes de trabajo, sin asignar nombres: cierre de Marketing; RRHH/attrition; Supply/ventas/clima; orquestación/integración/informe. Acordar contratos antes de desarrollar en paralelo. Los cuatro integrantes revisan cambios de otro frente.
