from redbot.core import commands, checks
from redbot.core.utils.chat_formatting import humanize_list
from .logger import logger

import discord

class Greet(commands.Cog):
    """My custom cog"""
     
    def __init__(self, bot, args):
        self.bot = bot
        self.channels = args["channels"]
        self.logic = args["logic"]
        self.guild_id = args["guild_id"]


    @commands.command()
    @checks.mod()
    async def greet(self, ctx, user: discord.Member = None):
        """Welcomes a user to the server"""
        if user is None:
            return

        await self.welcome(ctx, user)
        
    async def greetMember(self, member):
        """
        Greets members when they join
        """        
        if member.bot or member.guild.id != self.guild_id:
            # don't greet bots
            return        
        await self.welcome(self.channels.newMembers, member)
    
    async def pastGreet(self, ctx=None):
        """Greets members that joined the server while the bot was unavailable"""

        recentlyJoinedMembers = []
        messageLimit = 50

        log = self.channels.log

        if log is None:
            return

        # scan through the `messageLimit` most recent messages, add any new member announcment to the list of
        # `recentlyJoinedMembers` exit as soon as there is message from the bot found
        async for message in self.channels.newMembers.history(limit=messageLimit):
            if not message.author.bot:
                recentlyJoinedMembers.append(message)
            else:
                break

        size = len(recentlyJoinedMembers)
#        await log.send(f"{size} new member{'s' if size > 1 or size == 0 else ''} greeted since I was last online.")

        # if our list is empty then we don't want to do anything else
        if size == 0:
            return

        members = [message.author for message in recentlyJoinedMembers]

        #  for message in recentlyJoinedMembers:
        await self.welcome(self.channels.newMembers, members)
        
    async def welcome(self, channel=None, members=None):
        """Helper function to handle the welcoming of a user"""

        # We don't want to do anything if we 
        # don't have a channel or any members
        if channel is None or members is None:
            return

        # if members isn't already a list, then make it one
        if not isinstance(members, list):
            members = [members]

        # if the list is empty then return as we are done
        if len(members) == 0:
            return

        mentionList = [member.mention for member in members]

        # since we have members we now want to start doing work on them
        greetMembers = humanize_list(mentionList)

        await channel.send(
            f"Welcome {greetMembers}!\n"
            "Please take a moment to check out "
            f"{self.channels.anchor(self.channels.welcome_id)}.\n"
            "Following the instructions in there will allow you to gain full access to the server."
        )