"""Utility functions for accessing a repository."""
import os
from pathlib import Path

import magic
from pathspec import pathspec


def list_files_in_repo(repo_path: str | Path, additional_gitignore_content: str = "") -> list[Path]:
    """List all files in a repository, excluding files and directories that are ignored by git."""
    gitignore_content = f".*\n{additional_gitignore_content}\n{_read_gitignore(repo_path)}"
    spec = pathspec.PathSpec.from_lines("gitwildmatch", gitignore_content.splitlines())

    file_list = []
    for root, dirs, files in os.walk(repo_path):
        root = Path(root)
        # Remove excluded directories from the list to prevent os.walk from processing them
        dirs[:] = [d for d in dirs if not spec.match_file((root / d).relative_to(repo_path))]

        for file in files:
            file_path = root / file
            rel_file_path = file_path.relative_to(repo_path)
            if not spec.match_file(rel_file_path) and _is_text_file(file_path):
                file_list.append(rel_file_path)

    file_list.sort(key=lambda p: (p.as_posix().lower(), p.as_posix()))
    return file_list


def _read_gitignore(repo_path: str | Path) -> str:
    gitignore_path = Path(repo_path) / ".gitignore"
    if not gitignore_path.is_file():
        return ""

    with open(gitignore_path, "r", encoding="utf-8") as file:
        gitignore_content = file.read()
    return gitignore_content


def _is_text_file(file_path: str | Path):
    file_mime = magic.from_file(file_path, mime=True)
    # TODO is this the exhaustive list of mime types that we want to index ?
    return file_mime.startswith("text/") or file_mime.startswith("application/json")
