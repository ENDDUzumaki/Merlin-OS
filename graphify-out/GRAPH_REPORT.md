# Graph Report - Merlin-OS-repo  (2026-07-29)

## Corpus Check
- 42 files · ~5,505 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 255 nodes · 562 edges · 25 communities (24 shown, 1 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 46 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- bootstrap.py
- AIRequest
- FakeProvider
- SqliteMemoryStore
- TodoistSkill
- TodoistClient
- PARTE 2: MERLIN OS
- PromptBuilder
- main
- README.md

## God Nodes (most connected - your core abstractions)
1. `FakeProvider` - 27 edges
2. `AIRequest` - 21 edges
3. `AIProvider` - 19 edges
4. `ModelRouter` - 19 edges
5. `_build_service()` - 18 edges
6. `AIResponse` - 17 edges
7. `ProviderRegistry` - 16 edges
8. `RecordingProvider` - 16 edges
9. `SqliteMemoryStore` - 15 edges
10. `PromptBuilder` - 14 edges

## Surprising Connections (you probably didn't know these)
- `FakeMemoryStore` --uses--> `MemoryMessage`  [INFERRED]
  tests/unit/fakes.py → src/merlin/ai/memory/models.py
- `FakeMemoryStore` --uses--> `MemoryStore`  [INFERRED]
  tests/unit/fakes.py → src/merlin/ai/memory/store.py
- `RecordingProvider` --uses--> `AIProvider`  [INFERRED]
  tests/unit/test_model_router.py → src/merlin/ai/models/base.py
- `RecordingProvider` --uses--> `ProviderRegistry`  [INFERRED]
  tests/unit/test_model_router.py → src/merlin/ai/models/registry.py
- `FakeMemoryStore` --uses--> `MessageRole`  [INFERRED]
  tests/unit/fakes.py → src/merlin/ai/models/request.py

## Import Cycles
- None detected.

## Communities (25 total, 1 thin omitted)

### Community 0 - "bootstrap.py"
Cohesion: 0.09
Nodes (39): BaseModel, command, build_ai_service(), build_todoist_skill(), default_session_id(), Composition root del sistema. Aquí se construyen y conectan las piezas…, Construye la Skill de Todoist. El token viene de .env, no de YAML., AppSettings (+31 more)

### Community 1 - "AIRequest"
Cohesion: 0.13
Nodes (21): Contrato que todo AIProvider debe cumplir. Un AIProvider solo sabe generar…, Genera una respuesta a partir de un AIRequest., AIRequest, ConversationTurn, Request enviado hacia un AIProvider. Es un contrato estable: ningún provider…, AIResponse, Response devuelta por un AIProvider. Igual que AIRequest: contrato estable e…, ModelRouter (+13 more)

### Community 2 - "FakeProvider"
Cohesion: 0.11
Nodes (24): AIProvider, ABC, Interfaz base para cualquier proveedor de modelos de IA., Identificador único del provider (p. ej. 'ollama')., Indica si el provider está operativo (servicio arriba, etc.)., ProviderNotFoundError, ProviderRegistry, Exception (+16 more)

### Community 3 - "SqliteMemoryStore"
Cohesion: 0.11
Nodes (18): Enum, MemoryMessage, Modelos de dominio para la memoria de conversación., Path, Implementación de MemoryStore sobre SQLite. Único módulo del sistema que conoce…, SqliteMemoryStore, MemoryStore, ABC (+10 more)

### Community 4 - "TodoistSkill"
Cohesion: 0.14
Nodes (17): Protocol, Skill de gestión de tareas vía Todoist. Las Skills son las únicas piezas del…, Contrato mínimo que la Skill necesita de un backend de tareas., Crea una tarea. `due` acepta lenguaje natural ('mañana', 'lunes 9am')., Devuelve las tareas activas, hasta `limit`., TaskProvider, TodoistSkill, Modelos de dominio para la integración con Todoist. Contrato estable hacia… (+9 more)

### Community 5 - "TodoistClient"
Cohesion: 0.15
Nodes (15): AsyncBaseTransport, Request, Response, Exception, Fallo al comunicarse con Todoist o respuesta inesperada., TodoistClient, TodoistError, _client() (+7 more)

### Community 6 - "PARTE 2: MERLIN OS"
Cohesion: 0.11
Nodes (18): Arquitectura del proyecto, Caso de uso pendiente (para cuando existan recordatorios/cron), Contexto generalAUsuario: Juan (usuario Linux: **endduzu**, 24 años). Sistema operativo: **Arch Linux (XeroLinux)**., Estado actual, Estado actual del desarrollo, Estrategia de monetización acordada (por etapas), Herramientas recomendadas (sin control de puertos), Identidad de Merlin (+10 more)

### Community 7 - "PromptBuilder"
Cohesion: 0.38
Nodes (6): PromptBuilder, Construye el system_prompt que acompaña a cada AIRequest. Hoy solo interpola la…, PersonalityConfig, test_build_system_prompt_appends_rules_block_when_present(), test_build_system_prompt_interpolates_personality_fields(), test_build_system_prompt_omits_rules_block_when_empty()

### Community 8 - "main"
Cohesion: 0.67
Nodes (3): callback, main(), Merlin OS CLI. Ejemplo: merlin ask "Hola".

## Knowledge Gaps
- **16 isolated node(s):** `Contexto generalAUsuario: Juan (usuario Linux: **endduzu**, 24 años). Sistema operativo: **Arch Linux (XeroLinux)**.`, `Objetivo`, `Estrategia de monetización acordada (por etapas)`, `Herramientas recomendadas (sin control de puertos)`, `Estado actual` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TodoistSkill` connect `TodoistSkill` to `bootstrap.py`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `TodoistClient` connect `TodoistClient` to `bootstrap.py`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `SqliteMemoryStore` connect `SqliteMemoryStore` to `bootstrap.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `FakeProvider` (e.g. with `AIProvider` and `ProviderNotFoundError`) actually correct?**
  _`FakeProvider` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `AIRequest` (e.g. with `AIProvider` and `ModelRouter`) actually correct?**
  _`AIRequest` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AIProvider` (e.g. with `AIRequest` and `AIResponse`) actually correct?**
  _`AIProvider` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ModelRouter` (e.g. with `ProviderRegistry` and `AIRequest`) actually correct?**
  _`ModelRouter` has 7 INFERRED edges - model-reasoned connections that need verification._