from pathlib import Path
from typing import AsyncGenerator

from mergedbots import MergedBot, MergedMessage

from experiments.common.bot_manager import bot_manager
from experiments.common.repo_access_utils import list_files_in_repo

REPO_DIR = (Path(__file__).parents[3] / "mergedbots").as_posix()
REPO_NAME = Path(REPO_DIR).name


@bot_manager.create_bot(handle="ListRepoTool")
async def list_repo_tool(bot: MergedBot, message: MergedMessage) -> AsyncGenerator[MergedMessage, None]:
    file_list = list_files_in_repo(REPO_DIR)
    file_list_strings = [file.as_posix() for file in file_list]
    file_list_string = "\n".join(file_list_strings)

    result = (
        f"Here is the complete list of files that can be found in `{REPO_NAME}` repo:\n```\n{file_list_string}\n```"
    )
    yield await message.final_bot_response(bot, result, custom_fields={"file_list": file_list_strings})


@bot_manager.create_bot(handle="ReadFileBot")
async def read_file_bot(bot: MergedBot, message: MergedMessage) -> AsyncGenerator[MergedMessage, None]:
    # TODO implement bot fulfillment caching
    # TODO implement a utility function that simply returns the final bot response
    file_list_msg = [resp async for resp in list_repo_tool.merged_bot.fulfill(message)][-1]
    yield file_list_msg  # TODO here is where it would be cool to override `is_still_typing`
    file_list = file_list_msg.custom_fields["file_list"]

    yield await message.final_bot_response(bot, "Hello world!")
