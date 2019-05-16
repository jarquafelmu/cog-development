from redbot.core import commands
from redbot.core.utils.chat_formatting import error
from .logger import logger

import discord

class MessageHandler(commands.Cog):
    """
    Methods used to help with managing messages sent to discord
    """

    def __init__(self, bot):
        self.bot = bot

    async def send(self, ctx, channel, msg, *, msgObj = None):
        """
        Sends a message but also returns the message object so that it can be
        updated.
        """
        if msgObj is None:
            return await channel.send(msg)
        try:
            await msgObj.edit(content=msg)
        except discord.HTTPException:
            logger.exception("Editing message failed.")

    async def remove(self, ctx, *, msgObj = None):
        """
        Removes a message from discord.
        """
        try:
            await msgObj.delete()
        except discord.Forbidden:
            await ctx.send(error("I don't have persmissions to delete messages."))
            logger.exception(f"Bot didn't missing permission 'manage_message' to delete msg id #{msgObj.id}.")
        except discord.HTTPException:
            logger.exception(f"Failed to delete msg id #{msgObj.id}.")