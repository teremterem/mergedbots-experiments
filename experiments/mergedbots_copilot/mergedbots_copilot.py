"""A bot that can inspect a repo."""
import re

from langchain import LLMChain
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate, ChatPromptTemplate
from mergedbots import MergedBot, MergedMessage

from experiments.common.bot_manager import bot_manager, FAST_GPT_MODEL

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
    ai_goals_str = "\n".join([f"{i + 1}. {goal}" for i, goal in enumerate(ai_goals)])

    yield await message.final_bot_response(
        bot,
        f"AI NAME: {ai_name}\n" f"AI ROLE: {ai_role}\n" f"AI GOALS:\n{ai_goals_str}",
    )
