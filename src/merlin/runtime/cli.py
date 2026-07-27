"""Interfaz de línea de comandos de Merlin OS.

Capa de presentación: traduce input del usuario a llamadas al AIService y
formatea la salida. No contiene lógica de negocio ni conoce providers.
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from merlin.core.bootstrap import build_ai_service, default_session_id

app = typer.Typer(name="merlin", help="Merlin OS — Personal Cognitive Operating System")
console = Console()


@app.callback()
def main() -> None:
    """Merlin OS CLI. Ejemplo: merlin ask "Hola"."""


@app.command()
def ask(
    prompt: str,
    session: str = typer.Option(None, help="ID de sesión de memoria. Por defecto: la de config."),
) -> None:
    """Envía un prompt al modelo por defecto y muestra la respuesta."""
    ai_service = build_ai_service()
    session_id = session or default_session_id()

    with console.status("[bold cyan]Pensando..."):
        response = asyncio.run(ai_service.ask(prompt, session_id=session_id))

    console.print(f"[bold green]{response.provider}/{response.model}:[/bold green]")
    console.print(response.text)


if __name__ == "__main__":
    app()
