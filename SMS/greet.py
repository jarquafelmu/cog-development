from redbot.core import commands, checks
from redbot.core.utils.chat_formatting import humanize_list, error
from .logger import logger

import discord


class Greet(commands.Cog):
    """
    Greets new members to the Server McServerface server.
    """
    
    def __init__(self, bot, args):
        self.bot = bot
        self.args = args
        self.guild_id = args["guild_id"]
        self.channels = args["channels"]
    
    def guild(self):
        return self.bot.get_guild(self.guild_id)
        
    @commands.command()
    @checks.mod()
    async def greet(self, ctx, user: discord.Member = None):
        """
        Welcomes a user to the server
        """
        if user is None:
            return

        await self.welcome(ctx, user)
        
    async def greetMember(self, member):
        """Greets members when they join"""
        
        if member.bot or member.guild != self.guild():
            # don't greet bots
            return
        
        await self.welcome(self.channels.newMembers, member)
    
    async def pastGreet(self, ctx=None):
        """
        Greets members that joined the server while the bot was unavailable
        """
        recentlyJoinedMembers = []

        # scan through the `messageLimit` most recent messages, add any new member announcment to the list of
        # `recentlyJoinedMembers` exit as soon as there is message from the bot found
        # logger.debug(f"Greetings: {ChannelIds.GREETINGS}")
        logger.debug(f"Greetings: {self.channels.greetings}")

        if (self.channels.greetings is None):
            await ctx.send(error("Channels.Greetings is none!"))
            return logger.error("Channels.Greetings is none!")

        async for message in self.channels.greetings.history(limit=None):
            if not message.author.bot:
                if message.author.properties["guild"] == self.guild() and message.type == discord.MessageType.new_member:
                    recentlyJoinedMembers.append(message)
            else:
                break

        size = len(recentlyJoinedMembers)
        await self.args["channels"].log.send(f"{size} new member{'s' if size != 1 else ''} greeted since I was last online.")

        # if our list is empty then we don't want to do anything else
        if not recentlyJoinedMembers:
            return

        members = [message.author for message in recentlyJoinedMembers]

        #  for message in recentlyJoinedMembers:
        await self.welcome(self.args["channels"].greetings, members)        
        
        
    async def welcome(self, channel=None, members=None):
        """
        Helper function to handle the welcoming of a user
        """

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
            f"{self.channels.anchor(self.channels.rules_id)} and {self.channels.anchor(self.channels.server_orientation_id)}.\n"
            "Once you accept the rules, by denoting as specified, you will be automatically given the reader role."
        )

    # custom events
    async def is_loaded(self):
        """
        Handles actions that are done when the bot is loaded and ready to work.
        """
        await self.pastGreet()
