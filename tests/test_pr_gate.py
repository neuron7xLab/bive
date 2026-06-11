from pathlib import Path

from bive.pr_gate import check_docs, compile_python


def test_check_docs_on_repo_root():
    repo = Path(__file__).resolve().parents[1]
    assert check_docs(repo) == []


def test_compile_python_on_repo_root():
    repo = Path(__file__).resolve().parents[1]
    assert compile_python(repo) == []
