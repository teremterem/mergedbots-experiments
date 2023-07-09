from pathlib import Path

from botmerger import SingleTurnContext
from langchain import LLMChain
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

from experiments.common.bot_merger import bot_merger, FAST_GPT_MODEL, SLOW_GPT_MODEL
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
EXPLAIN_FILE_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template("Here is the content of `{file_path}`:"),
        HumanMessagePromptTemplate.from_template("{file_content}"),
        SystemMessagePromptTemplate.from_template("Please explain this content in plain English."),
    ]
)
REWOO_PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            """\
For the following tasks, make plans that can solve the problem step-by-step. For each plan, indicate which external \
tool together with tool input to retrieve evidence. You can store the evidence into a variable #E that can be called \
by later tools. (Plan, #E1, Plan, #E2, Plan, ...)

Tools can be one of the following:
Google[input]: Worker that searches results from Google. Useful when you need to find short and succinct answers \
about a specific topic. Input should be a search query.
LLM[input]: A pretrained LLM like yourself. Useful when you need to act with general world knowledge and common \
sense. Prioritize it when you are confident in solving the problem yourself. Input can be any instruction.

Which Asian capital city is known as Krung Thep to its inhabitants and stands on the Chao Phraya River?
Plan: Search for more information about Krung Thep
#E1 = Wikipedia[Krung Thep]
Plan: Search for more information about Chao Phraya River
#E2 = Wikipedia[Chao Phraya River]
Plan: Find out the name of the river on which Bakewell stands.
#E3 = LLM[What is the name of the river on which Bakewell stands? Given context: #E1 and #E2]

Begin! Describe your plans with rich details. Each Plan should be followed by only one #E.\
"""
        ),
        HumanMessagePromptTemplate.from_template("{request}"),
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

    file_list = list_files_in_repo(repo_dir, additional_gitignore_content="README.md\ntests/")
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
            await context.yield_final_response(file_path)
            return True

        return False

    if await yield_file_path(context.request.content):
        return

    async def figure_out_the_file_path(model_name: str) -> bool:
        chat_llm = PromptLayerChatOpenAI(
            model_name=model_name,
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
        return await yield_file_path(file_path)

    if not await figure_out_the_file_path(FAST_GPT_MODEL):
        if not await figure_out_the_file_path(SLOW_GPT_MODEL):
            raise ValueError(f"{file_list_msg.content}\n" f"Please specify the file.")


@bot_merger.create_bot("ReadFileBot", description="Reads a file from the repo.")
async def read_file_bot(context: SingleTurnContext) -> None:
    file_path_msg = await get_file_path_bot.bot.get_final_response(context.request)

    repo_dir_msg = await repo_path_bot.bot.get_final_response()
    file_path = Path(repo_dir_msg.content) / file_path_msg.content

    await context.yield_final_response(file_path.read_text(encoding="utf-8"))


@bot_merger.create_bot(
    "ExplainFileBot",
    description="Explains the content of a file from the repo in plain English.",
)
async def explain_file_bot(context: SingleTurnContext) -> None:
    file_path_msg = await get_file_path_bot.bot.get_final_response(context.request)

    # TODO use the future `InquiryBot` to report this interim result ? and move it to the `get_file_path_bot` ?
    await context.yield_interim_response(file_path_msg)

    file_content_msg = await read_file_bot.bot.get_final_response(file_path_msg.content)

    chat_llm = PromptLayerChatOpenAI(
        model_name=SLOW_GPT_MODEL,
        temperature=0.0,
        # TODO model_kwargs={"user": str(message.originator.uuid)},
        pl_tags=["explain_file_bot"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=EXPLAIN_FILE_PROMPT,
    )
    file_explanation = await llm_chain.arun(file_path=file_path_msg.content, file_content=file_content_msg.content)
    await context.yield_final_response(file_explanation)


# TODO summarize/outline the content of the file
# TODO check prompts in smol.ai for inspiration
# TODO answer a question about the repo, about a concept from the repo (ReWOO based, recursive)


@bot_merger.create_bot("ReWOO")
async def rewoo(context: SingleTurnContext) -> None:
    chat_llm = PromptLayerChatOpenAI(
        model_name=SLOW_GPT_MODEL,
        temperature=0.5,
        # TODO model_kwargs={"user": str(message.originator.uuid)},
        pl_tags=["explain_file_bot"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=REWOO_PLANNER_PROMPT,
    )
    generated_plan = await llm_chain.arun(request=context.request.content)
    await context.yield_final_response(generated_plan)
