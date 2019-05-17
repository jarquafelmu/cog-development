import contextlib
from datetime import datetime, timedelta

import discord
from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import humanize_list
from redbot.core.utils.predicates import MessagePredicate

from .logger import logger


class CSS(commands.Cog):
    """
    Custom functions to handle running the Computer Science Studybuddies server
    """
    utility_roles = {
        "admin": {
            "id": 484368083897679882,
            "ref": None
        },
        "staff": {
            "id": 492382906241777678,
            "ref": None
        }
    }

    properties = {
        "prod_protection_days": 2,
        "channels": None,
        "logic": None
    }

    def __init__(self, bot, args):
        """Initialization function"""
        self.bot = bot
        self.guild_id = args["guild_id"]
        self.properties["channels"] = args["channels"]
        self.properties["logic"] = args["logic"]
        self.db = Config.get_conf(self, identifier=1742113358, force_registration=True)
        default_member = {
            "last_prodded": None
        }
        self.db.register_member(**default_member)

        self.utility_roles["admin"]["ref"] = self.bot.get_guild(self.guild_id).get_role(self.utility_roles["admin"]["id"])
        self.utility_roles["staff"]["ref"] = self.bot.get_guild(self.guild_id).get_role(self.utility_roles["staff"]["id"])

    async def pastGreet(self, ctx=None):
        """
        Greets members that joined the server while the bot was unavailable
        """
        recentlyJoinedMembers = []
        messageLimit = 50

        # scan through the `messageLimit` most recent messages, add any new member announcment to the list of
        # `recentlyJoinedMembers` exit as soon as there is message from the bot found
        async for message in self.properties["channels"].newMembers.history(limit=messageLimit):
            if not message.author.bot:
                if message.author.guild == self.bot.get_guild(self.guild_id) and message.type == discord.MessageType.new_member:
                    recentlyJoinedMembers.append(message)
            else:
                break

        size = len(recentlyJoinedMembers)
        await self.properties["channels"].log.send(f"{size} new member{'s' if size != 1 else ''} greeted since I was last online.")

        # if our list is empty then we don't want to do anything else
        if not recentlyJoinedMembers:
            return

        members = [message.author for message in recentlyJoinedMembers]

        #  for message in recentlyJoinedMembers:
        await self.welcome(self.properties["channels"].newMembers, members)
        

    async def prodMember(self, ctx, member: discord.Member = None):
        """
        DM's the user asking them to tell the server what courses they have
        """
        if member is None:
            return False
        
        last_prodded = await self.db.member(member).last_prodded()
        now = datetime.utcnow()
        logger.debug(f"attempting to prod member {member.display_name}")         
        if last_prodded is not None:
            last_prodded = datetime.fromtimestamp(last_prodded)
            # member should be protected from being prodded for a set amount of time
            if last_prodded + timedelta(days=self.properties["prod_protection_days"]) > now:                
                logger.debug("member has been prodded too recently")
                return False

        with contextlib.suppress(discord.HTTPException):
            # we don't want blocked DMs preventing us from prodding
            await member.send(
                f"Hi {member.display_name}.\n"
                f"You have been on the **{member.guild.name}** discord server for a bit but haven't signed up for any courses.\n\n"
                "In order to get the most use out of the server you will need to do that so that you can see the groups for your courses.\n\n"
                "Don't reply to this message as this is just a bot.\n"
                f"Instead visit server and grab your courses in the **#{self.properties['channels'].courseList.name}** channel. Hope to see you soon."
            )

        await self.db.member(member).last_prodded.set(now.timestamp())
        logger.debug("prodded member")

        await self.properties["channels"].log.send(f"Prodded **{member.display_name}** as requested.")

        return True
        

    async def welcome(self, channel=None, members=None):
        """
        Helper function to handle the welcoming of a user
        """

        # We don't want to do anything if we don't have a channel or any members
        if channel is None or members is None:
            return

        # if members isn't already a list, then make it one
        if not isinstance(members, list):
            members = [members]

        # if the list is empty then return as we are done
        if not members:
            return

        mentionList = [member.mention for member in members]

        await channel.send(
            f"Welcome {humanize_list(mentionList)}! Check out the {self.properties['channels'].anchor(self.properties['channels'].welcome.id)} channel for some information about the server."
        )
        

    # user commands
    @commands.command()
    @checks.mod()
    async def greet(self, ctx, user: discord.Member = None):
        """
        Welcomes a user to the server
        """
        if user is None:
            user = ctx.author

        await self.welcome(ctx, user)

        await ctx.channel.send("Done.")
        

    @commands.command()
    @checks.admin()
    async def prod(self, ctx, user: discord.Member = None):
        """
        DM's the user asking them to tell the server what courses they have
        """
        if user is None:
            return

        # single user
        result = await self.prodMember(ctx, user)
        if result:
            msg = "Prodded member."    
        else:
            msg = (
                "Prodding was unsuccessful\n"
                "Either the member was recently prodded or the supplied member was invalid."
            )
            
        await ctx.channel.send(msg)

    @commands.command()
    @checks.admin()
    async def prodAll(self, ctx):
        """
        Prods all the members of the server who do not have roles.
        """
        confirmed = await self.properties["logic"].confirm(ctx)

        if confirmed:
            # build list of members without roles
            membersWithoutRoles = [member for member in ctx.guild.members if len(member.roles) < 2]

            log = self.properties["channels"].log

            size = len(membersWithoutRoles)
            if size == 0:
                return await ctx.send("All members are have courses.")

            await ctx.send(f"Prodding {size} member{'s' if size != 1 else ''}.")

            async with log.typing():
                for member in membersWithoutRoles:
                    await self.prodMember(ctx, member)

            # announce that the bot is done prodding members
            await log.send(f"\n\nCompleted prodding necessary members.")

            await ctx.send(f"Finished.")
        else:
            return await ctx.send("Standing down.")
        

    # custom events
    async def is_loaded(self):
        """
        Handles actions that are done when the bot is loaded and ready to work.
        """
        await self.pastGreet()

    # event triggers
    async def on_member_join(self, member):
        """
        Welcome's a new user to the server
        """

        # we only want to announce if this is the right server
        if member.guild != self.bot.get_guild(self.guild_id):
            return

        await self.welcome(self.properties["channels"].newMembers, member)
        

    async def on_member_remove(self, member):
        """
        event happens when a member leaves the server
        """
        # we only want to announce if this is the right server
        if member.guild != self.bot.get_guild(self.guild_id):
            return

        await self.properties["channels"].log.send(f"<@&{self.utility_roles['admin']['id']}>: {member.display_name} ({member.name}#{member.discriminator}) has left the building.")
