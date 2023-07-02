from pathlib import Path

from botmerger import SingleTurnContext

from experiments.common.bot_merger import bot_merger
from experiments.common.repo_access_utils import list_files_in_repo


@bot_merger.create_bot("RepoPathBot")
async def repo_path_bot(context: SingleTurnContext) -> None:
    repo_dir = (Path(__file__).parents[3] / "botmerger").resolve().as_posix()
    await context.yield_final_response(repo_dir)


@bot_merger.create_bot("ListRepoTool", description="Lists all the files in the repo.")
async def list_repo_tool(context: SingleTurnContext) -> None:
    repo_dir_msg = await repo_path_bot.bot.get_final_response(None)
    repo_dir = Path(repo_dir_msg.content)

    file_list = list_files_in_repo(repo_dir)
    file_list_strings = [file.as_posix() for file in file_list]
    file_list_string = "\n".join(file_list_strings)

    result = (
        f"Here is the complete list of files that can be found in `{repo_dir.name}` repo:\n"
        f"```\n"
        f"{file_list_string}\n"
        f"```"
    )
    await context.yield_final_response(result, extra_fields={"file_list": file_list_strings})


@bot_merger.create_bot("ReWOO")
async def rewoo(context: SingleTurnContext) -> None:
    await context.yield_from(
        await list_repo_tool.bot.trigger(context.request),
        indicate_typing_afterwards=True,
    )
    await context.yield_final_response("💪ReWOO")
