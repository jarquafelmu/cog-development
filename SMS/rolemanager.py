from redbot.core import commands
from .logger import logger
import discord
import contextlib


class RoleManager(commands.Cog):
    """Manages roles for Server McServerface"""
    
    msg_rule_agreement_id = 508393348067885066
    msg_author_id = 513857600152928279
    
    def __init__(self, bot, args):
        self.bot = bot
        self.guild_id = args["guild_id"]
        self.args = args
        
        self.roles = {
            "reader": {
                "id": 506657944860098561
            },
            "author": {
                "id": 506657837498368014
            }
        }

    def guild(self):
        return self.bot.get_guild(self.guild_id)
    
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
                
    async def process_reaction(self, payload, add: bool):
        """
        Handles the processing of the reaction
        """
        member = self.guild().get_member(payload.user_id)
        
        if member is None:
            return
        if not self.args["logic"].validate_member(member):
            logger.error(f"{member.display_name} is no longer a valid member of the server.")        
        
        emoji = str(payload.emoji)
        
        msg_id = payload.message_id
        if msg_id == self.msg_rule_agreement_id:
            role_name = await self.process_rule_agreement_reaction(member, emoji, add)
        elif msg_id == self.msg_author_id:
            role_name = await self.process_author_reaction(member, emoji, add)

        msg = (
            f"{'Added' if add else 'Removed'} role: `{role_name}` {'to' if add else 'from'} member: `{member.display_name}`"
        )
        logger.debug(msg)
        await self.args["channels"].log.send(msg)        
        
                
    async def process_rule_agreement_reaction(self, member: discord.Member, emoji: str, add: bool):
        """
        Handles the rule agreement reaction
        """        

        if emoji.startswith("\N{THUMBS UP SIGN}"):
            role = self.guild().get_role(self.roles["reader"]["id"])
            if add:
                msg = (
                    f"Thank you for agreeing to the rules for {member.guild.name}.\n"
                    "You have now been granted access to the server."
                )
                await member.add_roles(role)
            else:
                msg = (
                    f"It is unfortunate that you can no longer agree to the rules for {member.guild.name}.\n"
                    "Your access to the server has been restricted.\n"
                    "If you decide to agree to the rules in the future, your access will be restored."
                )
                await member.remove_roles(role)

            with contextlib.suppress(discord.HTTPException):
                # we don't want blocked DMs preventing the function working
                await member.send(msg)

            return role.name

    async def process_author_reaction(self, member: discord.Member, emoji: str, add: bool):
        """
        Handles the rule agreement reaction
        """

        if emoji.startswith("\N{LOWER LEFT BALLPOINT PEN}"):
            role = self.guild().get_role(self.roles["author"]["id"])
            if add:
                await member.add_roles(role)
            else:
                await member.remove_roles(role)
                
            return role.name
