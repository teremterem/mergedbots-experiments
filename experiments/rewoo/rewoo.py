from botmerger import SingleTurnContext

from experiments.common.bot_merger import bot_merger


@bot_merger.create_bot("ChatGPT")
async def chat_gpt(context: SingleTurnContext) -> None:
    await context.yield_final_response("ChatGPT")


@bot_merger.create_bot("ReWOO")
async def rewoo(context: SingleTurnContext) -> None:
    await context.yield_from(
        await chat_gpt.bot.trigger(context.request),
        indicate_typing_afterwards=True,
    )
    await context.yield_final_response("ReWOO")
