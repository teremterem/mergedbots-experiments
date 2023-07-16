# pylint: disable=wrong-import-position
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.append(str(Path(__file__).parents[2]))

from experiments.rewoo.rewoo_utils import list_botmerger_files, BOTMERGER_REPO_PATH

BOTMERGER_EXPLANATIONS_PATH = Path(f"{BOTMERGER_REPO_PATH.as_posix()}.inspection") / "explanations"


def get_botmerger_explanations() -> list[str]:
    result = [
        (BOTMERGER_EXPLANATIONS_PATH / f"{file}.txt").read_text(encoding="utf-8") for file in list_botmerger_files()
    ]
    return result


def main() -> None:
    for explanation in get_botmerger_explanations():
        print()
        print()
        print()
        print(explanation)
    print()
    print()
    print()
    print("\n".join(list_botmerger_files()))
    print()
    print()
    print()


if __name__ == "__main__":
    main()
