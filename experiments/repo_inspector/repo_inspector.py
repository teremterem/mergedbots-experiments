"""TODO"""
from pathlib import Path
from typing import AsyncGenerator

from mergedbots import MergedMessage, MergedBot

from experiments.repo_inspector.repo_access_utils import list_files_in_repo

repo_inspector = MergedBot(handle="RepoInspector")


@repo_inspector
async def repo_inspector_func(bot: MergedBot, message: MergedMessage) -> AsyncGenerator[MergedMessage, None]:
    """TODO"""
    conversation = message.get_full_conversion()
    if not conversation:
        yield message.service_followup_as_final_response(bot, "```\nCONVERSATION RESTARTED\n```")
        return

    file_list: list[Path] = list_files_in_repo("../mergedbots")
    print(file_list)
    file_list_str = "\n".join([f.as_posix() for f in file_list])
    yield message.final_bot_response(bot, f"```\n{file_list_str}\n```")
