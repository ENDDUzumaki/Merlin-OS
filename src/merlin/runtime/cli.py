"""Interfaz de línea de comandos de Merlin OS.

Capa de presentación: traduce input del usuario a llamadas al AIService y
formatea la salida. No contiene lógica de negocio ni conoce providers.
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from merlin.core.bootstrap import (
    build_ai_service,
    build_intent_classifier,
    build_planner,
    build_todoist_skill,
    default_session_id,
)
from merlin.integrations.todoist.client import TodoistError
from merlin.services.planner import UnknownIntentError

app = typer.Typer(name="merlin", help="Merlin OS — Personal Cognitive Operating System")
console = Console()


@app.callback()
def main() -> None:
    """Merlin OS CLI. Ejemplo: merlin ask "Hola"."""


@app.command()
def ask(
    prompt: str,
    session: str = typer.Option(None, help="ID de sesión de memoria. Por defecto: la de config."),
    task: str = typer.Option(
        None, "--task", help="Tipo de tarea para elegir modelo (ver config/routing.yaml)."
    ),
) -> None:
    """Envía un prompt al modelo por defecto y muestra la respuesta."""
    ai_service = build_ai_service()
    session_id = session or default_session_id()

    with console.status("[bold cyan]Pensando..."):
        response = asyncio.run(ai_service.ask(prompt, session_id=session_id, task_type=task))

    console.print(f"[bold green]{response.provider}/{response.model}:[/bold green]")
    console.print(response.text)


@app.command()
def do(
    request: str,
    session: str = typer.Option(None, help="ID de sesión de memoria. Por defecto: la de config."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Ejecuta sin pedir confirmación."),
) -> None:
    """Interpreta una petición y ejecuta la acción correspondiente, o conversa."""
    classifier = build_intent_classifier()

    with console.status("[bold cyan]Interpretando..."):
        intent = asyncio.run(classifier.classify(request))

    if not intent.is_actionable:
        console.print("[dim]Sin acción reconocida; respondo como conversación.[/dim]")
        _run_conversation(request, session)
        return

    try:
        planner = build_planner()
    except TodoistError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold yellow]Acción propuesta:[/bold yellow] {planner.describe(intent)}")
    if not yes and not typer.confirm("¿Ejecutar?"):
        console.print("[dim]Cancelado.[/dim]")
        return

    try:
        result = asyncio.run(planner.execute(intent))
    except (UnknownIntentError, TodoistError, KeyError, ValueError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold green]{result}[/bold green]")


def _run_conversation(prompt: str, session: str | None) -> None:
    ai_service = build_ai_service()
    session_id = session or default_session_id()
    with console.status("[bold cyan]Pensando..."):
        response = asyncio.run(ai_service.ask(prompt, session_id=session_id))
    console.print(f"[bold green]{response.provider}/{response.model}:[/bold green]")
    console.print(response.text)


todo_app = typer.Typer(help="Gestión de tareas vía Todoist.")
app.add_typer(todo_app, name="todo")


@todo_app.command("add")
def todo_add(
    content: str,
    due: str = typer.Option(None, "--due", help="Fecha en lenguaje natural: 'mañana', 'lunes'."),
) -> None:
    """Crea una tarea en Todoist."""
    try:
        skill = build_todoist_skill()
        task = asyncio.run(skill.add_task(content, due=due))
    except (TodoistError, ValueError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    due_text = f" (vence: {task.due})" if task.due else ""
    console.print(f"[bold green]Tarea creada:[/bold green] {task.content}{due_text}")


@todo_app.command("list")
def todo_list(
    limit: int = typer.Option(None, "--limit", help="Máximo de tareas a mostrar."),
) -> None:
    """Lista las tareas activas de Todoist."""
    try:
        skill = build_todoist_skill()
        tasks = asyncio.run(skill.list_tasks(limit=limit))
    except TodoistError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    if not tasks:
        console.print("[dim]No hay tareas activas.[/dim]")
        return

    for task in tasks:
        due_text = f" [dim](vence: {task.due})[/dim]" if task.due else ""
        console.print(f"• {task.content}{due_text}")


if __name__ == "__main__":
    app()
