"""Nox commands for linting/testing."""

import argparse
import os
import shlex
import tomllib

from nox_poetry import Session, session

PYTHON_VERSIONS = ["3.12"]
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, "src")
TESTS_DIR = os.path.join(SCRIPT_DIR, "tests")
PYTHON_DIRS = [SRC_DIR, TESTS_DIR, os.path.join(SCRIPT_DIR, "noxfile.py")]

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    "--mypy-extra-args", type=str, default="", help="Extra args passed to mypy."
)
arg_parser.add_argument(
    "--pylint-extra-args", type=str, default="", help="Extra args passed to pylint."
)


def get_dependencies(group: str) -> list[str]:
    """Get the dependencies in the given poetry optional dependency in the pyproject.toml."""

    with open(os.path.join(SCRIPT_DIR, "pyproject.toml"), "rb") as toml_file:
        toml = tomllib.load(toml_file)

    return list(toml["tool"]["poetry"]["group"][group]["dependencies"].keys())


@session(python=PYTHON_VERSIONS)
def black(nox_session: Session) -> None:
    """Runs black in check mode to ensure all files are formatted."""
    nox_session.install("black")
    nox_session.run(
        "black",
        "--check",
        *PYTHON_DIRS,
    )


@session(python=PYTHON_VERSIONS)
def isort(nox_session: Session) -> None:
    """Runs isort in check mode to ensure all files have sorted imports."""
    nox_session.install("isort")
    nox_session.run(
        "isort",
        "--check",
        *PYTHON_DIRS,
    )


@session(python=PYTHON_VERSIONS)
def mypy(nox_session: Session) -> None:
    """Runs mypy to validate typing is correct."""
    args = arg_parser.parse_args(nox_session.posargs)
    deps = get_dependencies("nox")  # Required to analyze this file
    deps += get_dependencies("tests")  # Required to analyze tests package

    nox_session.install("mypy", *deps, ".")
    nox_session.run(
        "mypy",
        *shlex.split(args.mypy_extra_args),
        # TODO: config file
        *PYTHON_DIRS,
    )


@session(python=PYTHON_VERSIONS)
def pylint(nox_session: Session) -> None:
    """Runs pylint to validate there are no errors detected."""
    args = arg_parser.parse_args(nox_session.posargs)
    deps = get_dependencies("nox")  # Required to analyze this file
    deps += get_dependencies("tests")  # Required to analyze tests package

    nox_session.install("pylint", *deps, ".")
    nox_session.run(
        "pylint",
        *shlex.split(args.pylint_extra_args),
        "--recursive=y",
        # TODO: config file
        *PYTHON_DIRS,
    )


@session(python=PYTHON_VERSIONS)
def pytest(nox_session: Session) -> None:
    """Runs the pytest suite."""
    # Install all dependencies in the test group in poetry.  We don't want to use poetry itself to do this,
    # because we need non-editable install; but we can just pass packages with no version, because by virtue of
    # how nox_poetry works, the versions are constrained to what's in the lock file.
    deps = get_dependencies("tests")
    deps.append(".")
    nox_session.install(*deps)

    # Run pytest
    nox_session.run("pytest", TESTS_DIR)
