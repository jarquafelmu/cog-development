from redbot.core import commands
from redbot.core.utils.predicates import MessagePredicate

import discord
import re

class Logic(commands.Bot):

    def __init__(self, bot):
        self.bot = bot    

    async def confirm(self, ctx, *, msg="Are you sure?"):
        """
        Handles confirmations for commands.
        Optionally can supply a message that is displayed to the user. Defaults to 'Are you sure?'.
        """
        await ctx.channel.send(f"{msg} (y/n)")
        pred = MessagePredicate.yes_or_no(ctx)
        await self.bot.wait_for("message", check=pred)
        return pred.result        

    def validate_member(self, member: discord.Member = None):
        """
        Validates if a member is still on the server or not.
        """
        if member is None:
            return False
        return hasattr(member, "guild")

    def validate_course(self, channel: discord.TextChannel = None):
        """
        Validates a course name by seeing if it matches the expected pattern.

        If it does match the pattern then `True` is returned. Otherwise, `False`.
        """
        # validates if the course name is two or more alpha characters followed by two or more digits
        if channel is None:
            return

        pattern = re.compile("^([A-Za-z]{2,}\d+{2,})$") 
        return pattern.match(channel.name)