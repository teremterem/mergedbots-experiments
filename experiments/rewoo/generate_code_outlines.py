# pylint: disable=wrong-import-position
import asyncio
import sys
from pathlib import Path

from botmerger import BotResponses
from dotenv import load_dotenv

load_dotenv()
sys.path.append(str(Path(__file__).parents[2]))

from experiments.rewoo.rewoo import generate_file_outline
from experiments.rewoo.rewoo_utils import list_botmerger_files


async def save_the_outline(file: str, bot_responses: BotResponses) -> None:
    outline = (await bot_responses.get_final_response()).content
    outline = f"FILE: {file}\n\n{outline}"
    print(f"\n{outline}\n")


async def main() -> None:
    tasks = []
    for file in list_botmerger_files():
        responses = await generate_file_outline.bot.trigger(file)
        tasks.append(asyncio.create_task(save_the_outline(file, responses)))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
