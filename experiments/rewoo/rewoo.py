import json
from pathlib import Path

from botmerger import SingleTurnContext
from langchain import LLMChain
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.schema import HumanMessage

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
You are a chatbot that is good at analysing the code in the following repository and answering questions about the \
concepts that can be found in this repository.

Repository name: {repo_name}
List of files in the repository:\
"""
        ),
        HumanMessagePromptTemplate.from_template("{repo_file_list}"),
        SystemMessagePromptTemplate.from_template(
            """\
For the following tasks, make plans that can solve the problem step-by-step. For each plan, indicate which external \
tool together with tool input to retrieve evidence. You can store the evidence into a variable that can be called \
by later tools.

Here is the expected format of your response:\
"""
        ),
        SystemMessagePromptTemplate.from_template(
            """\
{{
    "evidence1": {{
        "plan": "explanation of a step of the plan",
        "tool": "Tool1",
        "tool_input": "natural text input to the tool",
        "context": []
    }},
    "evidence2": {{
        "plan": "explanation of a step of the plan",
        "tool": "Tool2",
        "tool_input": "natural text input to the tool",
        "context": []
    }},
    "evidence3": {{
        "plan": "explanation of a step of the plan",
        "tool": "Tool1",
        "tool_input": "natural text input to the tool",
        "context": ["evidence2"]
    }},
    "evidence4": {{
        "plan": "explanation of a step of the plan",
        "tool": "Tool3",
        "tool_input": "natural text input to the tool",
        "context": ["evidence1", "evidence3"]
    }}
}}\
"""
        ),
        SystemMessagePromptTemplate.from_template(
            """\
Tools can be one of the following:

CodeOutlineGeneratorBot[input]: Displays the outline of a code file from the repository. Input should \
be a file path. Does not accept file paths that are not present in the list of files above.

FileReaderBot[input]: Displays the content of a file from the repository. Input should be a file path. \
Does not accept file paths that are not present in the list of files above. Useful when you need to \
look at the code directly.

ConceptExplorerBot[input]: A complex bot that is an exact copy of yourself. Capable of generating and \
carrying out elaborate plans just like you. Has access to all the same tools as you do. Input should \
be a question about a concept.

SimplerLLM[input]: A pretrained LLM like yourself. Useful when you need to act with general world \
knowledge and common sense. Unlike yourself, though, it is not capable of generating and carrying \
out plans. Prioritize it when you are confident in solving a problem in a single shot. Input can be \
any instruction.

Begin! Describe your plans with rich details. RESPOND WITH VALID JSON ONLY AND NO OTHER TEXT.\
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

    if await yield_file_path(context.concluding_request.content):
        return

    async def figure_out_the_file_path(model_name: str) -> bool:
        chat_llm = PromptLayerChatOpenAI(
            model_name=model_name,
            temperature=0.0,
            model_kwargs={"stop": ['"', "\n"]},
            pl_tags=["get_file_path_bot"],
        )
        llm_chain = LLMChain(
            llm=chat_llm,
            prompt=EXTRACT_FILE_PATH_PROMPT,
        )
        file_path = await llm_chain.arun(request=context.concluding_request.content, file_list=file_list_msg.content)
        return await yield_file_path(file_path)

    if not await figure_out_the_file_path(FAST_GPT_MODEL):
        if not await figure_out_the_file_path(SLOW_GPT_MODEL):
            raise ValueError(f"{file_list_msg.content}\n" f"Please specify the file.")


@bot_merger.create_bot(
    "FileReaderBot",
    description=(
        "Displays the content of a file from the repository. Input should be a file path. Does not accept file "
        "paths that are not present in the list of files above. Useful when you need to look at the code directly."
    ),
)
async def read_file_bot(context: SingleTurnContext) -> None:
    file_path_msg = await get_file_path_bot.bot.get_final_response(context.concluding_request)

    repo_dir_msg = await repo_path_bot.bot.get_final_response()
    file_path = Path(repo_dir_msg.content) / file_path_msg.content

    await context.yield_final_response(file_path.read_text(encoding="utf-8"))


@bot_merger.create_bot(
    "CodeOutlineGeneratorBot",
    description=(
        "Displays the outline of a code file from the repository. Input should be a file path. Does not accept "
        "file paths that are not present in the list of files above."
    ),
)
async def explain_file_bot(context: SingleTurnContext) -> None:
    file_path_msg = await get_file_path_bot.bot.get_final_response(context.concluding_request)

    # TODO use the future `InquiryBot` to report this interim result ? and move it to the `get_file_path_bot` ?
    await context.yield_interim_response(file_path_msg)

    file_content_msg = await read_file_bot.bot.get_final_response(file_path_msg.content)

    chat_llm = PromptLayerChatOpenAI(
        model_name=SLOW_GPT_MODEL,
        temperature=0.0,
        pl_tags=["explain_file_bot"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=EXPLAIN_FILE_PROMPT,
    )
    file_explanation = await llm_chain.arun(file_path=file_path_msg.content, file_content=file_content_msg.content)
    await context.yield_final_response(file_explanation)


@bot_merger.create_bot(
    "ConceptExplorerBot",
    description=(
        "A complex bot that is an exact copy of yourself. Capable of generating and carrying out elaborate plans "
        "just like you. Has access to all the same tools as you do. Input should be a question about a concept."
    ),
)
async def rewoo(context: SingleTurnContext) -> None:
    repo_dir = Path((await repo_path_bot.bot.get_final_response()).content)
    repo_file_list = "\n".join((await list_repo_bot.bot.get_final_response()).extra_fields["file_list"])

    chat_llm = PromptLayerChatOpenAI(
        model_name=SLOW_GPT_MODEL,
        temperature=0.5,
        pl_tags=["rewoo_planner"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=REWOO_PLANNER_PROMPT,
    )
    generated_plan = await llm_chain.arun(
        repo_name=repo_dir.name,
        repo_file_list=repo_file_list,
        request=context.concluding_request.content,
    )
    await context.yield_final_response(json.loads(generated_plan))


@bot_merger.create_bot(
    "CodeOutlineGeneratorBot",
    description=(
        "Displays the outline of a code file from the repository. Input should be a file path. Does not accept "
        "file paths that are not present in the list of files above."
    ),
)
async def simpler_llm(context: SingleTurnContext) -> None:
    chat_llm = PromptLayerChatOpenAI(
        model_name=SLOW_GPT_MODEL,
        temperature=0.0,
        pl_tags=["simpler_llm"],
    )
    result = await chat_llm.agenerate([[HumanMessage(content=context.concluding_request.content)]])
    await context.yield_final_response(json.loads(result.generations[0][0].text))
