from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import warning, error, box
from .channels import Channels
from .logger import logger

import discord

class RoleManager(commands.Cog):
    """Manages roles for Server McServerface"""

    def __init__(self, bot, args):
        self.bot = bot
        self.channels = args["channels"]
        self.logic = args["logic"]
        self.guild_id = args["guild_id"]
        self.log = self.channels.log

        self.db = Config.get_conf(self, 268451739)

        default_guild = {
            "registered_roles": {}
        }

        self.db.register_guild(**default_guild)

    def build_record(self, role_id: int, emoji: str, message_id: int):
        """
        Builds a role record for registering
        """
        assert(role_id), "role_id must not be blank."
        assert(emoji), "emoji must not be blank."
        assert(message_id), "message_id must not be blank."

        key = str(role_id) + str(message_id)
        return {
            key: {
                "role_id": role_id,
                "emoji": emoji,
                "message_id": message_id
            }
        }

    @commands.group(name="roles")
    async def _roles_settings(self, ctx):
        """
        Settings for roles.
        """
    
    @_roles_settings.command(name="register", aliases=["reg", "r"])
    async def _roles_settings_register(self, ctx, role_id: int = None, emoji: str = None, msg_id: int = None):
        """
        Registers a new role.
        """
        guild = self.bot.get_guild(self.guild_id)

        try:
            newRole = self.build_record(role_id, emoji, msg_id)
        except AssertionError as error:
            await ctx.send(error(error))
            logger.exception()
            return
        
        logger.debug("set values for new role")

        # converts our python dict to a json object
        async with self.db.guild(guild).registered_roles() as roles:
            roles.update(newRole)
            logger.debug("stored role")
        
        logger.debug("registered role")
        self.log("Registered.")

    @_roles_settings.command(name="view", aliases=["v"])
    async def _roles_settings_view(self, ctx):
        """
        Prints out a list of the currently registered roles.
        """
        guild = self.bot.get_guild(self.guild_id)

        registered_roles = await self.db.guild(guild).get_raw("registered_roles")

        async with ctx.channel.typing():
            for key, val in registered_roles.items():
                logger.debug(f"role: {val}")
                role_id = val['role_id']
                await ctx.send(box(
                    f"id: {key}\n"
                    f"role: {guild.get_role(role_id).name}\n"
                    f"role_id: {role_id}\n"
                    f"emoji: {val['emoji']}\n"
                    f"message_id: {val['message_id']}"
                ))
    
    async def on_raw_reaction_add(self, payload):        
        """
        Member agrees to the rules
        """        
        await self.process_reaction(payload, True)
                
    async def on_raw_reaction_remove(self, payload):        
        """
        Member no longer agrees to the rules
        """        
        await self.process_reaction(payload, False)
                
    async def process_reaction(self, payload, isAddingRole: bool):
        """
        Handles the processing of the reaction
        """
        member = self.bot.get_guild(self.guild_id).get_member(payload.user_id)
        emoji = str(payload.emoji)
        guild = self.bot.get_guild(self.guild_id)
        
        if member is None:
            return logger.debug(f"Member {member.name} not found as a valid member.")        

        # build a list of just the values from the registered roles
        registered_roles = await self.db.guild(guild).get_raw("registered_roles")
        collection = list(registered_roles.values())

        # filter out any role that doesn't share the current message id
        matches = list(filter(lambda x: x["message_id"] == payload.message_id, collection))

        if not matches:
            return logger.debug(f"No registered role found to match message id: '{payload.message_id}'")

        # find a match which has our emoji
        role = next(iter([match for match in matches if str(payload.emoji).startswith(match['emoji'])]), None)

        if role is None:
            return logger.debug(f"No registered role found to match the provided emoji.")

        role_obj = guild.get_role(int(role["role_id"]))

        try:
            if isAddingRole:
                action = "added"
                await member.add_roles(role_obj)
            else:
                action = "removed"
                await member.remove_roles(role_obj)
        except discord.Forbidden:
            logger.exception(f"I do not have permission to modify roles for member {member.name}.")
        except discord.HTTPException:
            logger.exception("Updating the role failed.")
        else:            
            msg = f"`{member.name}` {action} {role_obj.name} role."
            await self.log.send(msg)
            logger.info(msg)