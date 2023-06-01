from typing import Callable, Optional
from typing import List

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.chains.llm import LLMChain
from langchain.chat_models.base import BaseChatModel
from langchain.experimental.autonomous_agents.autogpt.output_parser import (
    AutoGPTOutputParser,
    BaseAutoGPTOutputParser,
)
from langchain.experimental.autonomous_agents.autogpt.prompt import AutoGPTPrompt
from langchain.experimental.autonomous_agents.autogpt.prompt_generator import (
    FINISH_NAME,
)
from langchain.schema import (
    AIMessage,
    BaseMessage,
    Document,
    HumanMessage,
    SystemMessage,
)
from langchain.tools.base import BaseTool
from langchain.vectorstores.base import VectorStoreRetriever
from pydantic import Field
from pydantic import ValidationError


def _print_func(text: str) -> None:
    print("\n")
    print(text)


class HumanInputRun(BaseTool):
    """Tool that adds the capability to ask user for input."""

    name = "Human"
    description = (
        "You can ask a human for guidance when you think you "
        "got stuck or you are not sure what to do next. "
        "The input should be a question for the human."
    )
    prompt_func: Callable[[str], None] = Field(default_factory=lambda: _print_func)
    input_func: Callable = Field(default_factory=lambda: input)

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the Human input tool."""
        self.prompt_func(query)
        return self.input_func()

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the Human tool asynchronously."""
        raise NotImplementedError("Human tool does not support async")


class AutoGPT:
    """Agent class for interacting with Auto-GPT."""

    def __init__(
        self,
        ai_name: str,
        memory: VectorStoreRetriever,
        chain: LLMChain,
        output_parser: BaseAutoGPTOutputParser,
        tools: List[BaseTool],
        feedback_tool: Optional[HumanInputRun] = None,
    ):
        self.ai_name = ai_name
        self.memory = memory
        self.full_message_history: List[BaseMessage] = []
        self.next_action_count = 0
        self.chain = chain
        self.output_parser = output_parser
        self.tools = tools
        self.feedback_tool = feedback_tool

    @classmethod
    def from_llm_and_tools(
        cls,
        ai_name: str,
        ai_role: str,
        memory: VectorStoreRetriever,
        tools: List[BaseTool],
        llm: BaseChatModel,
        human_in_the_loop: bool = False,
        output_parser: Optional[BaseAutoGPTOutputParser] = None,
    ) -> "AutoGPT":
        prompt = AutoGPTPrompt(
            ai_name=ai_name,
            ai_role=ai_role,
            tools=tools,
            input_variables=["memory", "messages", "goals", "user_input"],
            token_counter=llm.get_num_tokens,
        )
        human_feedback_tool = HumanInputRun() if human_in_the_loop else None
        chain = LLMChain(llm=llm, prompt=prompt)
        return cls(
            ai_name,
            memory,
            chain,
            output_parser or AutoGPTOutputParser(),
            tools,
            feedback_tool=human_feedback_tool,
        )

    def run(self, goals: List[str]) -> str:
        user_input = "Determine which next command to use, " "and respond using the format specified above:"
        # Interaction Loop
        loop_count = 0
        while True:
            # Discontinue if continuous limit is reached
            loop_count += 1

            # Send message to AI, get response
            assistant_reply = self.chain.run(
                goals=goals,
                messages=self.full_message_history,
                memory=self.memory,
                user_input=user_input,
            )

            # Print Assistant thoughts
            print(assistant_reply)
            self.full_message_history.append(HumanMessage(content=user_input))
            self.full_message_history.append(AIMessage(content=assistant_reply))

            # Get command name and arguments
            action = self.output_parser.parse(assistant_reply)
            tools = {t.name: t for t in self.tools}
            if action.name == FINISH_NAME:
                return action.args["response"]
            if action.name in tools:
                tool = tools[action.name]
                try:
                    observation = tool.run(action.args)
                except ValidationError as e:
                    observation = f"Validation Error in args: {str(e)}, args: {action.args}"
                except Exception as e:
                    observation = f"Error: {str(e)}, {type(e).__name__}, args: {action.args}"
                result = f"Command {tool.name} returned: {observation}"
            elif action.name == "ERROR":
                result = f"Error: {action.args}. "
            else:
                result = (
                    f"Unknown command '{action.name}'. "
                    f"Please refer to the 'COMMANDS' list for available "
                    f"commands and only respond in the specified JSON format."
                )

            memory_to_add = f"Assistant Reply: {assistant_reply} " f"\nResult: {result} "
            if self.feedback_tool is not None:
                feedback = f"\n{self.feedback_tool.run('Input: ')}"
                if feedback in {"q", "stop"}:
                    print("EXITING")
                    return "EXITING"
                memory_to_add += feedback

            self.memory.add_documents([Document(page_content=memory_to_add)])
            self.full_message_history.append(SystemMessage(content=result))
