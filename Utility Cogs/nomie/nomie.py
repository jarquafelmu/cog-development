from redbot.core import commands
from redbot.core.utils.chat_formatting import error

import discord
import asyncio

class Nomie(commands.Cog):
    """
    Handles actions related to nicknames
    """
    properties = {
        "channels": None,
        "logic": None
    }

    def __init__(self, bot, args):
        self.bot = bot
        self.guild_id = args["guild_id"]
        self.properties["channels"] = args["channels"]
        self.properties["logic"] = args["logic"]

    @bot.listen('on_member_update')
    async def nickname_updated(self, before, after):
        """
        Interested in the nickname update event
        """
        pre_nick = before.nick
        # cause = 

    async def responsible_user(self):
        """
        Determines who caused the update to happen and returns a reference to them.
        """
        await asyncio.sleep(1);
        # get the members with the 'Marquis de Nomie' role.
        # find out of these members, which one (if any) cause the recent name change
        # if found, return a reference to that user

        # get role from role id
        role_id = -1
        role = self.bot.get_role(role_id)
        if role is None:
            return

        # list of members with this role
        members = role.members

        
