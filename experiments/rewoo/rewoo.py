from botmerger import SingleTurnContext

from experiments.common.bot_merger import bot_merger


@bot_merger.create_bot("ReWOO")
async def rewoo(context: SingleTurnContext) -> None:
    pass
