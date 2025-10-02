import os
import pytest
from typer.testing import CliRunner

@pytest.fixture(autouse=True)
def isolate_files(tmp_path):
    """
    Change working directory to a pytest-provided temporary folder for each test.
    """
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(old_cwd)

@pytest.fixture
def runner() -> CliRunner:
	"""
	Fixture para usar el runner de Typer en todos los tests.
	"""
	return CliRunner()

