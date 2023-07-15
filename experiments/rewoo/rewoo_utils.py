from pathlib import Path

from experiments.common.repo_access_utils import list_files_in_repo

BOTMERGER_REPO_PATH = (Path(__file__).parents[3] / "botmerger").resolve()


def list_botmerger_files() -> list[str]:
    file_list = list_files_in_repo(BOTMERGER_REPO_PATH, additional_gitignore_content="README.md\ntests/")
    return [file.as_posix() for file in file_list]
