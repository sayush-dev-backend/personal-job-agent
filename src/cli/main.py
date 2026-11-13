"""Typer entry point for the job agent."""

import typer

from config.settings import Settings
from llm.gemini import GeminiProvider
from storage.database import Database
from agent.orchestrator import ApplicationOrchestrator

app = typer.Typer(help="Personal Job Search Agent")


@app.command()
def version() -> None:
    """Show the application version."""
    typer.echo("personal-job-agent 0.1.0")


@app.command("init-db")
def init_db() -> None:
    """Initialize the configured SQLite database."""
    settings = Settings()
    orchestrator = ApplicationOrchestrator(
        database=Database(settings.database_path),
        llm_provider=GeminiProvider(settings),
    )
    orchestrator.initialize()
    typer.echo(f"Initialized database at {settings.database_path}")


if __name__ == "__main__":
    app()
