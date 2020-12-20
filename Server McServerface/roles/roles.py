from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import warning
from redbot.core.utils.predicates import MessagePredicate
import emoji
from .logger import logger

import discord
import contextlib

# TODO: update for rules role and the others
# TODO: Create tool where a role can be assigned to a reaction emoji from bot commands


class RoleManager(commands.Cog):
    """Manages roles for Server McServerface"""

    # guild_id = 493101259012702208  # Bot Dev
    guild_id = 493875452046475275  # The Nool

    msg_rule_agreement_id = 508393348067885066
    msg_author_id = 513857600152928279

    log_id = 509041710651670548

    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.get_channel(self.log_id)
        logger.debug("Test debug message.")

        self.db = Config.get_conf(
            self, identifier=1712118358, force_registration=True)

        default_guild = {
            "reaction_roles": []
        }

        self.db.register_guild(**default_guild)
        self.roles = {
            "member": {
                "id": 567886671245475869
            },
            "reader": {
                "id": 506657944860098561
            },
            "author": {
                "id": 506657837498368014
            }
        }

        # self.roles["member"]["obj"] = self.bot.get_guild(
        #     self.guild_id).get_role(self.roles["member"]["id"])
        # self.roles["reader"]["obj"] = self.bot.get_guild(
        #     self.guild_id).get_role(self.roles["reader"]["id"])
        # self.roles["author"]["obj"] = self.bot.get_guild(
        #     self.guild_id).get_role(self.roles["author"]["id"])

    @commands.Cog.listener("on_raw_reaction_add")
    async def on_raw_reaction_add(self, payload):
        """
        Member agrees to the rules
        """
        self.testLogger()
        await self.process_reaction(payload, True)

    @commands.Cog.listener("on_raw_reaction_remove")
    async def on_raw_reaction_remove(self, payload):
        """
        Member no longer agrees to the rules
        """
        self.testLogger()
        await self.process_reaction(payload, False)

    def testLogger(self):
        logger.debug("Test debug message..")
        # logger.debug("Test debug message.")
        logger.debug(logger)
        pass

    async def process_reaction(self, payload, add: bool):
        """
        Handles the processing of the reaction
        """
        member = self.bot.get_guild(self.guild_id).get_member(payload.user_id)

        if member is None:
            return

        reactionRoles = await self.getReactionRoles()
        print(reactionRoles)
        if not reactionRoles:  # if no role on reaction are left then we don't do anything
            return

        reactionRoles = filter(
            lambda x: x["msg_id"] == payload.message_id, reactionRoles)
        reactionRoles = filter(
            lambda x: emoji.demojize(
                x.emoji) == emoji.demojize(payload.emoji), reactionRoles
        )

        if not reactionRoles:  # if no role on reaction are left then we don't do anything
            return

        reactionRoleId = reactionRoles[0]["role_id"]
        role = self.getRoleFromServer(reactionRoleId)
        logger.debug(role)

        msg_id = payload.message_id
        if msg_id == self.msg_rule_agreement_id:
            await self.process_rule_agreement_reaction(member, emoji, add)
        elif msg_id == self.msg_author_id:
            await self.process_author_reaction(member, emoji, add)

    # async def process_reaction(self, payload, add: bool):
    #     """
    #     Handles the processing of the reaction
    #     """
    #     member = self.bot.get_guild(self.guild_id).get_member(payload.user_id)

    #     if member is None:
    #         return

    #     reactionRoles = self.getRoleOnReaction()

    #     emoji = str(payload.emoji)

    #     msg_id = payload.message_id
    #     if msg_id == self.msg_rule_agreement_id:
    #         await self.process_rule_agreement_reaction(member, emoji, add)
    #     elif msg_id == self.msg_author_id:
    #         await self.process_author_reaction(member, emoji, add)

    async def process_rule_agreement_reaction(self, member: discord.Member, emoji: str, add: bool):
        """
        Handles the rule agreement reaction
        """

        if emoji.startswith("\N{THUMBS UP SIGN}"):
            if add:
                msg = (
                    f"Thank you for agreeing to the rules of {member.guild.name}.\n"
                    "You have now been granted full access to the server."
                )
                action = "added"
                await member.add_roles(self.roles["member"]["obj"])
            else:
                msg = (
                    f"It is unfortunate that you can no longer agree to the rules of {member.guild.name}.\n"
                    "Your access to the server has been restricted.\n"
                    "If you decide to agree to the rules in the future, your access will be restored."
                )
                action = "removed"
                await member.remove_roles(self.roles["member"]["obj"])

            await self.log.send(f"`{member.name}` {action} `member` role.")
            with contextlib.suppress(discord.HTTPException):
                # we don't want blocked DMs preventing the function working
                await member.send(msg)
        else:
            await self.log.send(warning(f"`{member.name}` tried to add a role but used the wrong emoji."))

    async def process_author_reaction(self, member: discord.Member, emoji: str, add: bool):
        """
        Handles the rule agreement reaction
        """

        if emoji.startswith("\N{LOWER LEFT BALLPOINT PEN}"):
            if add:
                action = "added"
                await member.add_roles(self.roles["author"]["obj"])
            else:
                action = "removed"
                await member.remove_roles(self.roles["author"]["obj"])
            await self.log.send(f"`{member.name}` {action} `author` role.")
        else:
            await self.log.send(warning(f"`{member.name}` tried to add a role but used the wrong emoji."))

    @commands.command(name="registerReactionRole")
    async def registerRoleOnReactionInteractive(self, ctx):
        """[summary]

        Args:
            ctx ([type]): [description]
        """
        # will handle interaction with the user
        # ask: name of reaction?
        # wait for name
        # ask: for which message?
        # wait for message_id
        # ask: for which role?
        # wait for role_id
        # which emoji?
        # wait for emoji
        # fuzzy?
        pass

    # @commands.command(name="registerrole", aliases=['rra'])
    # async def registerRoleOnReaction(self, ctx, name: str, channel_id: str, msg_id: str, role_id: str, emoji: str, fuzzy: bool = False):
    #     """Registers a new entry for a Reaction-based Role Assignment
    #     Args:
    #         name (str): The name of this Reaction based role
    #         channel_id (str): The channel where the message resides
    #         msg_id (str): The message to monitor
    #         role_id (str): The role to add
    #         emoji (str): The emoji to look for
    #         fuzzy (bool, optional): If this should match other emoji of this kind. Defaults to False.
    #     """
    #     if (not name or not msg_id or not role_id or not emoji):
    #         return await ctx.channel.send(warning("Missing required parameter"))
    #     # verify that the role and message actually exist
    #     try:
    #         await self.getRoleFromServer(role_id)
    #     except:
    #         return await ctx.channel.send(warning("Role Id was not valid"))
    #     try:
    #         await self.getMessageFromServer(channel_id, msg_id)
    #     except:
    #         return await ctx.channel.send(warning("Message Id was not valid"))
    #     roleOnReaction = self.RoleOnReactionTemplate(
    #         ctx, name, msg_id, role_id, emoji, fuzzy
    #     )
    #     self.storeRoleOnReaction(roleOnReaction)
    #     pass
    # @commands.command(name="test", aliases=['rra'])
    # async def registerRoleOnReaction(self, ctx, name: str, channel_id: str, msg_id: str, role_id: str, emoji: str, fuzzy: bool = False):
    #     """Registers a new entry for a Reaction-based Role Assignment
    #     Args:
    #         name (str): The name of this Reaction based role
    #         channel_id (str): The channel where the message resides
    #         msg_id (str): The message to monitor
    #         role_id (str): The role to add
    #         emoji (str): The emoji to look for
    #         fuzzy (bool, optional): If this should match other emoji of this kind. Defaults to False.
    #     """
    #     roleOnReaction = self.RoleOnReactionTemplate(
    #         ctx, 'name', 'msg_id', 'role_id', '👍', False
    #     )
    #     self.storeRoleOnReaction(roleOnReaction)
    #     pass
    @commands.command(name="test", aliases=['rra'])
    async def registerRoleOnReaction(self, ctx):
        """Registers a new entry for a Reaction-based Role Assignment

        Args:
            name (str): The name of this Reaction based role
            channel_id (str): The channel where the message resides
            msg_id (str): The message to monitor
            role_id (str): The role to add
            emoji (str): The emoji to look for
            fuzzy (bool, optional): If this should match other emoji of this kind. Defaults to False.
        """
        # roleOnReaction = self.RoleOnReactionTemplate(
        #     ctx, 'name', 'msg_id', 'role_id', '👍', False
        # )
        await self.storeRoleOnReaction({
            "name": 'test',
            "msg_id": '0',
            "role_id": '0',
            "emoji": '👍',
            "fuzzy": False})
        # self.storeRoleOnReaction(roleOnReaction)
        pass

    @commands.command(name="show")
    async def show(self, ctx):
        roles = await self.getReactionRoles()
        print(roles)
        await ctx.channel.send(roles)
        pass

    async def getMessageFromServer(self, channel_id: str, msg_id: str):
        await self.self.get_guild().get_channel(channel_id).fetch_message(msg_id)
        pass

    async def getRoleFromServer(self, role_id: str) -> str:
        """
        Gets a role from the server that matches the passed in id

        Args:
            role_id (str): The role to nab

        Returns:
            json: A reference to the role
        """
        return self.get_guild().get_role(role_id)

    def getGuild(self):
        logger.debug(f"guid_id: {self.guild_id}")
        return self.bot.get_guild(self.guild_id)

    async def getReactionRoles(self):
        """Gets the reaction roles from the database

        Args:
            ctx (obj): current context

        Returns:
            json: The reaction roles stored in the database
        """
        guild = self.getGuild()
        print(guild)
        guildFromDb = self.db.guild(guild)
        print(guildFromDb)
        return await guildFromDb.reaction_roles()

    async def storeRoleOnReaction(self, role):
        """
        Stores the reaction roles in the database

        Args:
            ctx (obj): current context
            roles (json): A collection of reaction roles
        """
        print('storing role', role)
        await self.db.guild(self.getGuild()).reaction_roles.set(role)
        pass

        def RoleOnReactionTemplate(self, name: str, msg_id: str, role_id: str, emoji, fuzzy: bool = False):
            """Creates a new reaction role object

            Args:
                name (str): The name of the this reaction role
                channel_id (str): The id of the channel that the message resides in
                msg_id (str): The id of the message that should be watched for reactions
                role_id (str): The role to be given or removed
                emoji (str): The triggering emoji
                fuzzy (bool): Whether this reaction can match others of it's kind

            Returns:
                json: {
                "name": str,
                "msg_id": str,
                "role_id": str,
                "emoji": str,
                fuzzy: boolean
            }
            """
            return {
                "name": name,
                "msg_id": msg_id,
                "role_id": role_id,
                "emoji": emoji,
                "fuzzy": fuzzy}
