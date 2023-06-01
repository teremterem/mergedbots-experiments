"""A bot that can inspect a repo."""
import re
import secrets

import faiss
from langchain import LLMChain, FAISS, InMemoryDocstore
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate, ChatPromptTemplate
from mergedbots import MergedBot, MergedMessage
from mergedbots.experimental.sequential import SequentialMergedBotWrapper, ConversationSequence

from experiments.common.bot_manager import bot_manager, FAST_GPT_MODEL, SLOW_GPT_MODEL
from experiments.mergedbots_copilot.autogpt import AutoGPT, HumanInputRun

AICONFIG_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            """\
Your task is to devise up to 5 highly effective goals and an appropriate role-based name (_GPT) for an autonomous \
agent, ensuring that the goals are optimally aligned with the successful completion of its assigned task.

The user will provide the task, you will provide only the output in the exact format specified below with no \
explanation or conversation.

Example input:
Help me with marketing my business

Example output:
Name: CMOGPT
Description: a professional digital marketer AI that assists Solopreneurs in growing their businesses by providing \
world-class expertise in solving marketing problems for SaaS, content products, agencies, and more.
Goals:
- Engage in effective problem-solving, prioritization, planning, and supporting execution to address your marketing \
needs as your virtual Chief Marketing Officer.

- Provide specific, actionable, and concise advice to help you make informed decisions without the use of platitudes \
or overly wordy explanations.

- Identify and prioritize quick wins and cost-effective campaigns that maximize results with minimal time and budget \
investment.

- Proactively take the lead in guiding you and offering suggestions when faced with unclear information or \
uncertainty to ensure your marketing strategy remains on track."""
        ),
        HumanMessagePromptTemplate.from_template(
            "Task: '{user_prompt}'\n"
            "Respond only with the output in the exact format specified in the system prompt, with no explanation "
            "or conversation.\n"
        ),
    ]
)


@bot_manager.create_bot(handle="AutoGPTConfigBot")
async def autogpt_aiconfig(bot: MergedBot, message: MergedMessage) -> None:
    chat_llm = PromptLayerChatOpenAI(
        model_name=FAST_GPT_MODEL,
        temperature=0.0,
        model_kwargs={
            "user": str(message.originator.uuid),
        },
        pl_tags=["autogpt_conf"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=AICONFIG_PROMPT,
    )

    output = await llm_chain.arun(user_prompt=message.content)

    try:
        ai_name = re.search(r"Name(?:\s*):(?:\s*)(.*)", output, re.IGNORECASE).group(1)
        ai_role = (
            re.search(
                r"Description(?:\s*):(?:\s*)(.*?)(?:(?:\n)|Goals)",
                output,
                re.IGNORECASE | re.DOTALL,
            )
            .group(1)
            .strip()
        )
        ai_goals = re.findall(r"(?<=\n)-\s*(.*)", output)
        custom_fields = {"autogpt_name": ai_name, "autogpt_role": ai_role, "autogpt_goals": ai_goals, "success": True}
    except Exception:
        # TODO what to do with the error ? report it somehow ? log it ?
        custom_fields = {"success": False}

    yield await message.final_bot_response(bot, output, custom_fields=custom_fields)


@SequentialMergedBotWrapper(bot_manager.create_bot(handle="AutoGPT"))
async def autogpt(bot: MergedBot, conv_sequence: ConversationSequence) -> None:
    embeddings_model = OpenAIEmbeddings()
    embedding_size = 1536
    index = faiss.IndexFlatL2(embedding_size)
    vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})

    message = await conv_sequence.wait_for_incoming()

    aiconfig_response = await autogpt_aiconfig.bot.get_final_response(message)

    # TODO here it would be cool to just override is_still_typing instead of creating a new message
    # await conv_sequence.yield_outgoing(aiconfig_response)
    await conv_sequence.yield_outgoing(
        await message.interim_bot_response(aiconfig_response.sender, aiconfig_response.content)
    )

    chat_llm = PromptLayerChatOpenAI(
        model_name=SLOW_GPT_MODEL,
        temperature=0.0,
        model_kwargs={
            "user": str(message.originator.uuid),
        },
        pl_tags=["mb_autogpt", secrets.token_hex(4)],
    )

    human_input_run = HumanInputRun(
        bot=bot,
        conv_sequence=conv_sequence,
        latest_inbound_msg=message,
    )
    tools = [human_input_run]  # TODO add other tools (bots as tools)

    autogpt_agent = AutoGPT.from_llm_and_tools(
        ai_name=aiconfig_response.custom_fields["autogpt_name"],
        ai_role=aiconfig_response.custom_fields["autogpt_role"],
        tools=tools,
        llm=chat_llm,
        memory=vectorstore.as_retriever(),
        feedback_tool=human_input_run,
    )
    # autogpt_agent.chain.verbose = True

    await autogpt_agent.arun([aiconfig_response.custom_fields["autogpt_goals"]])
