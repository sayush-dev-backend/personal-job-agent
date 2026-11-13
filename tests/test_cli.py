from typer.testing import CliRunner

from cli.main import app


def test_cli_startup():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Personal Job Search Agent" in result.stdout


def test_cli_version():
    result = CliRunner().invoke(app, ["version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
