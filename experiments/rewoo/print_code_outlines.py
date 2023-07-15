# pylint: disable=wrong-import-position
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.append(str(Path(__file__).parents[2]))

from experiments.rewoo.generate_code_outlines import BOTMERGER_OUTLINES_PATH
from experiments.rewoo.rewoo_utils import list_botmerger_files


def main() -> None:
    for file in list_botmerger_files():
        print()
        print()
        print((BOTMERGER_OUTLINES_PATH / f"{file}.txt").read_text(encoding="utf-8"))
        print()


if __name__ == "__main__":
    main()
