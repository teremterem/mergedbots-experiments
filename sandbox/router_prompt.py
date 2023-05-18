"""This module contains the prompt for the router bot."""
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

SYS_TEMPLATE1 = "HERE IS A CONVERSATION BETWEEN A USER AND AN AI ASSISTANT."
SYS_MSG_PROMPT1 = SystemMessagePromptTemplate.from_template(SYS_TEMPLATE1)
SYS_TEMPLATE2 = "{conversation}"
SYS_MSG_PROMPT2 = SystemMessagePromptTemplate.from_template(SYS_TEMPLATE2)
SYS_TEMPLATE3 = "AND HERE IS A LIST OF BOTS WHO COULD BE USED TO RESPOND TO THE CONVERSATION ABOVE."
SYS_MSG_PROMPT3 = SystemMessagePromptTemplate.from_template(SYS_TEMPLATE3)
SYS_TEMPLATE4 = "{bots}"
SYS_MSG_PROMPT4 = SystemMessagePromptTemplate.from_template(SYS_TEMPLATE4)
USER_TEMPLATE = """\
Which of the bots above would you like to use to respond to the latest user message from the conversation above?

BOT NAME: \""""
USER_MSG_PROMPT = HumanMessagePromptTemplate.from_template(USER_TEMPLATE)

CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        SYS_MSG_PROMPT1,
        SYS_MSG_PROMPT2,
        SYS_MSG_PROMPT3,
        SYS_MSG_PROMPT4,
        USER_MSG_PROMPT,
    ]
)
