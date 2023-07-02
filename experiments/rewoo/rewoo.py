from pathlib import Path

from botmerger import SingleTurnContext
from langchain import LLMChain
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

from experiments.common.bot_merger import bot_merger, FAST_GPT_MODEL
from experiments.common.repo_access_utils import list_files_in_repo

EXTRACT_FILE_PATH_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template("{file_list}"),
        HumanMessagePromptTemplate.from_template(
            """\
HERE IS A REQUEST FROM A USER:

{request}"""
        ),
        SystemMessagePromptTemplate.from_template(
            """\
IF THE USER IS ASKING FOR A FILE FROM THE REPO ABOVE, PLEASE RESPOND WITH THE FOLLOWING JSON:
{{
    "file": "path/to/file"
}}

IF THE USER IS ASKING FOR A FILE THAT IS NOT LISTED ABOVE OR THERE IS NO MENTION OF A FILE IN THE USER'S REQUEST, \
PLEASE RESPOND WITH THE FOLLOWING JSON:
{{
    "file": ""  // empty string
}}

YOUR RESPONSE:
{{
    "file": "\
"""
        ),
    ]
)


@bot_merger.create_bot("RepoPathBot")
async def repo_path_bot(context: SingleTurnContext) -> None:
    repo_dir = (Path(__file__).parents[3] / "botmerger").resolve().as_posix()
    await context.yield_final_response(repo_dir)


@bot_merger.create_bot("ListRepoBot", description="Lists all the files in the repo.")
async def list_repo_bot(context: SingleTurnContext) -> None:
    repo_dir_msg = await repo_path_bot.bot.get_final_response()
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


@bot_merger.create_bot("GetFilePathBot")
async def get_file_path_bot(context: SingleTurnContext) -> None:
    file_list_msg = await list_repo_bot.bot.get_final_response()
    file_set = set(file_list_msg.extra_fields["file_list"])

    async def yield_file_path(file_path: str) -> bool:
        if not file_path:
            return False

        file_path = file_path.strip()
        if file_path in file_set:
            await context.yield_final_response(
                file_path,
                extra_fields={"success": True},
            )
            return True

        return False

    if await yield_file_path(context.request.content):
        return

    chat_llm = PromptLayerChatOpenAI(
        model_name=FAST_GPT_MODEL,
        temperature=0.0,
        model_kwargs={
            "stop": ['"', "\n"],
            # TODO "user": str(message.originator.uuid),
        },
        pl_tags=["get_file_path_bot"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=EXTRACT_FILE_PATH_PROMPT,
    )
    file_path = await llm_chain.arun(request=context.request.content, file_list=file_list_msg.content)

    if not await yield_file_path(file_path):
        await context.yield_final_response(
            f"{file_list_msg.content}\n" f"Please specify the file.",
            extra_fields={"success": False},
        )


@bot_merger.create_bot("ReadFileBot", description="Reads a file from the repo.")
async def read_file_bot(context: SingleTurnContext) -> None:
    file_path_msg = await get_file_path_bot.bot.get_final_response(context.request)
    if not file_path_msg.extra_fields.get("success"):
        await context.yield_final_response(
            file_path_msg,
            extra_fields={"success": False},
        )
        return

    repo_dir_msg = await repo_path_bot.bot.get_final_response()
    file_path = Path(repo_dir_msg.content) / file_path_msg.content

    await context.yield_final_response(
        file_path.read_text(encoding="utf-8"),
        extra_fields={"success": True},
    )


@bot_merger.create_bot("ReWOO")
async def rewoo(context: SingleTurnContext) -> None:
    await context.yield_from(
        await read_file_bot.bot.trigger(context.request),
        indicate_typing_afterwards=True,
    )
    await context.yield_final_response("💪ReWOO")
