from redbot.core import commands
from .logger import logger

import discord
import random

class RoleHandler(commands.Cog):
    def __init__(self, bot, args):
        """
        Initialize the CourseAssignment object
        """
        self.bot = bot
        self.logic = args["logic"]
        self.channels = args["channels"]    

    def getRolesForUser(self, user: discord.Member = None):
        """
        Gets a list of the roles assigned to the user,
        omitting the '@everyone' role
        """
        if user is None:
            return []

        return [role.name for role in user.roles if role.name != "@everyone"]

    async def create_role(self, ctx, role_name: str):
        """
        Confirms that the user wants to create the role.
        If so the role is created and returned to the calling function.
        Otherwise, NoneType is returned.
        """
        createRole = await self.logic.confirm(ctx, msg=f"Role `{role_name}` does not exist. Would you like to create it?")
        if (createRole):
            color = self.get_role_color()
            try:
                # create the role in the guild
                role_obj = await ctx.guild.create_role(name=role_name, color=color)
            except discord.InvalidArgument:
                logger.exception("InvalidArgument")
            except discord.Forbidden:
                logger.exception(f"Bot lacks permission to add roles to the server.")
            except discord.HTTPException:
                logger.exception(f"Creating the role failed.")
            else:
                logger.info(f"Creating role for {role_name}.")
                return role_obj
        return None

    def get_role_color(self):
        """
        Generates a random color for a role between 0xaaaaaa and 0xfffffe
        """
        def gen_color_segment():
            # 153 == 99
            # 255 == ff
            return random.randint(153, 255)

        while True:
            color = discord.Color.from_rgb(gen_color_segment(), gen_color_segment(), gen_color_segment())

            # prevent white (0xffffff) from being a role color.
            if color.value != 16777215:
                break

        return color

    async def update_member(self, member: discord.Member, role: discord.Role, add: bool):
        """
        Adds or removes a role from mbember
        """
        if member is None:
            return logger.error("Member is none")
        
        if not self.logic.validate_member(member):
            return logger.debug(f"Member ({member.id}) {member.display_name} is no longer a member of the server.")

        if add:
            await member.add_roles(role)
        else:
            await member.remove_roles(role)
        debug_msg = (
            f"{'Added' if add else 'Removed'} role: `{role.name}` to member: `{member.name}`"
        )
        logger.debug(debug_msg)
        await self.channels.log.send(debug_msg)

    async def update_role_name(self, ctx, role_id: int, new_name: str):
        """
        Updates the name of the role
        """
        assert (role_id), "role_id is not supplied"
        assert (new_name), "new_name is not supplied"

        await ctx.guild.get_role(role_id).edit(name=new_name)