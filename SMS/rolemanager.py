from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import warning, error, box
from .channels import Channels, ChannelIds
from .logger import logger

import discord
import contextlib


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
            "registered_roles": [],
            "default_role": {
                "role_name": None,
                "role_id": None,
                "emoji": None,
                "message_id": None
            }
        }

    @commands.group(name="roles")
    async def _roles_settings(self):
        """
        Settings for roles.
        """
    
    @_roles_settings.commands(name="register", aliases=["reg", "r"])
    async def _roles_settings_register(self, ctx, role_id: int = None, emoji: str = None, msg_id: int = None):
        """
        Registers a new role.
        """
        fail = False;
        if role_id is None:            
            msg = "role_id was not provided."
            fail = True

        if emoji is None:            
            msg = "emoji was not provided."
            fail = True

        if msg_id is None:            
            msg = "message_id was not provided."
            fail = True

        if (fail):
            await ctx.send(error(msg))
            logger.error(msg)
            return

        newRole = await self.db.guild(self.guild_id).default_role.get_raw()
        newRole["role_name"] = self.bot.get_guild(self.guild_id).get_role(role_id)
        newRole["role_id"] = role_id
        newRole["emoji"] = emoji
        newRole["message_id"] = msg_id

        async with self.db.guild(self.guild).registered_roles() as roles:
            roles.append(newRole)

    @_roles_settings.commands(name="view", aliases=["v"])
    async def _roles_settings_view(self, ctx):
        """
        Prints out a list of the currently registered roles.
        """
        async with ctx.channel.typing():
            async with self.db.guild(self.guild).registered_roles() as roles:
                for role in roles:
                    await ctx.send(box(
                        f"role: {role['role_name']}\n"
                        f"id: {role['role_id']}\n"
                        f"emoji: {role['emoji']}\n"
                        f"linked_message_id: {role['message_id']}"
                    ))
        await ctx.channel.send("Done.")
    
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
        
        if member is None:
            return logger.debug(f"Member {member.name} not found as a valid member.")
        
        emoji = str(payload.emoji)

        matches = {};
        async with self.db.guild(self.guild).registered_roles() as roles:
                for role_package in roles:
                    if (role_package["message_id"] == payload.message_id):
                        matches.append(role_package)

        if not matches:
            return logger.debug(f"No registered role found to match message id: '{payload.message_id}'")

        role = None
        for match in matches:
            if match["emoji"].startswith(payload.emoji):
                role = match        

        if role is None:
            return logger.debug(f"No registered role found to match the provided emoji.")

        try:
            if isAddingRole:
                action = "added"
                await member.add_roles(self.roles["author"]["obj"])
            else:
                action = "removed"
                await member.remove_roles(self.roles["author"]["obj"])
        except discord.Forbidden:
            logger.exception(f"I do not have permission to modify roles for member {member.name}.")
        except discord.HTTPException:
            logger.exception("Updating the role failed.")
        else:            
            await self.log.send(f"`{member.name}` {action} `author` role.")