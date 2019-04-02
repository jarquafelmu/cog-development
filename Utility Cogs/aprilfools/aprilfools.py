from redbot.core import commands, checks, Config
from redbot.core.utils.chat_formatting import error, warning, humanize_list
from redbot.core.utils.predicates import MessagePredicate

import logging
import discord
from enum import Enum


# create log with 'spam_application'
log = logging.getLogger("aprilfools.py")
log.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter(
    "%(asctime)s - %(name)s::%(funcName)s::%(lineno)d"
    "- %(levelname)s - %(message)s"
)

# create console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(formatter)

# add the handlers to the log
# allows to add only one instance of file handler and stream handler
if log.handlers:
    for handler in log.handlers:
        # add the handlers to the log
        # makes sure no duplicate handlers are added

        if not isinstance(handler, logging.StreamHandler):
            log.addHandler(consoleHandler)
            print('added stream handler')
else:
    log.addHandler(consoleHandler)
    print('added handler for the first time')
 
class Action(Enum):
    DEPLOY = 0
    REVERT = 1

class AprilFools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1745013358, force_registration=True)
        
        default_guild = {
            "prank_name": ""
        }

        default_user = {
            "cached_name": "",
            "pranking_allowed": True
        }

        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)

    @commands.group(name="AprilFools", aliases=["aprilfools", "ap"])
    @checks.admin()
    async def _aprilfools(self, ctx):
        """
        A group of commands for the april fools cog.
        """
        pass
    
    @_aprilfools.group(name="name")
    async def _aprilfools_name(self, ctx):
        """
        A group of commands for prank name manipulation.
        """
        pass
    
    @_aprilfools_name.command(name="set")
    async def _aprilfools_name_set(self, ctx, *, new_name: str):
        """
        Set the name that should be used when changing user's display name for april fools.
        """
        current_name = await self.config.guild(ctx.guild).prank_name()
        await self.config.guild(ctx.guild).prank_name.set(new_name)
        await ctx.send(f"Changed name from {current_name} to {new_name}")
    
    @_aprilfools_name.command(name="check")
    async def _aprilfools_name_check(self, ctx):
        """
        Shows what the current prank name is.
        """
        await ctx.send(f"Current name is {await self.config.guild(ctx.guild).prank_name()}")

    @_aprilfools.command(name="forbidden", aliases=["forbid"])
    async def _aprilfools_set_forbidden_users(self, ctx, user_ids: commands.Greedy[int]):
        """
        Sets the provided user ids as forbidden from pranking.
        """
        forbidden_users = []
        for user_id in user_ids:
            user = self.bot.get_user(user_id)
            if user is None:
                continue
            await self.config.user(user).pranking_allowed.set(False)
            forbidden_users.append(user.name)

        await ctx.send(f"Marked {humanize_list(forbidden_users)} as foridden to be pranked.")
    
    @_aprilfools.command(name="deploy")
    @checks.admin()
    async def _aprilfools_deploy(self, ctx):
        """
        Changes the display name all users of this guild to the prank name.

        Note: Will not fire if the prank name has not been set for this guild.
        """
        if not await self.confirm(ctx):
            await ctx.send("Standing down.")

        if not await self.config.guild(ctx.guild).prank_name():
            return await ctx.send(error("Prank name is not set. Cannot proceed until it is set."))

        await self.process(ctx, Action.DEPLOY)
        pass
    
    @_aprilfools.command(name="revert")
    @checks.admin()
    async def _aprilfools_revert(self, ctx):
        """
        Reverts all the display names of the users of this guild to there previous display name if possible.
        If not possible then it will fall back to using their main name.

        Note: Will only change names that match the current prank name. Names that are different are preserved 
        to prevent new names being wiped out.
        """
        if not await self.confirm(ctx):
            await ctx.send("Standing down.")

        if not await self.config.guild(ctx.guild).prank_name():
            return await ctx.send(error("Prank name is not set. Cannot proceed until it is set."))

        await self.process(ctx, Action.REVERT)
        pass

    async def process(self, ctx, action: Action):
        log.debug(f"Using '{await self.config.guild(ctx.guild).prank_name()}' as prank name ")
        async with ctx.channel.typing():
            # guild = self.bot.get_guild(self.guild_id)
            members = ctx.guild.members
            current = 0
            total = len(members)
            msg = await ctx.send(f"Processed {current} of {total} members.")
            for member in members:
                current += 1
                if member.bot: 
                    continue

                if action == Action.DEPLOY:
                    await self.prank(ctx, member)
                elif action == Action.REVERT:
                    await self.unprank(ctx, member)

                try:
                    await msg.edit(content=f"Processed {current} of {total} members.")
                except discord.HTTPException:
                    await ctx.send(error("Failed to edit message."))
                
            await ctx.send("Done.")

    async def prank(self, ctx, user: discord.User = None):
        """
        Pranks a user by saving a cached version of the nickname and then changing their nickname to 
        the prank name.
        """
        if user is None:
            return
        
        try:
            if not await self.config.user(user).pranking_allowed():
                # Pranking of this user is not allowed
                return

            await self.config.user(user).cached_name.set(user.display_name)
            prank_name = await self.config.guild(ctx.guild).prank_name()
            await self.update_name(ctx, reason="Changing name for April Fools prank.", name=prank_name, user=user)
        except KeyError:
            await ctx.send(error("User doesn't exist in database."))
            log.exception("User doesn't exist in database.")
        pass

    async def unprank(self, ctx, user: discord.User = None):
        """
        Revert's a user's display name back to their cached name or to their 
        default username if the cached version does not exist.
        """
        if user is None:            
            return log.debug("No user object supplied.")

        # only revert the name if it's still the prank name
        prank_name = await self.config.guild(ctx.guild).prank_name()
        if not user.display_name == prank_name:
            return log.debug(f"{user.name}'s display name '{user.display_name}' is no longer the prank name '{prank_name}'. Terminating")

        try:
            cached_name = await self.config.user(user).cached_name()
            name = cached_name
            name_used = "cached name"
        except KeyError:
            log.warning(f"No cached version of {user.name} exists. Using default username.")
            name = user.name
            name_used = "default name"
        except discord.HTTPException:
            await log.exception(f"Failed to edit {user.name}'s name.")
            return

        await self.update_name(ctx, reason=f"Reverting name from april fools prank. Used {name_used}.", name=name, user=user)

    async def update_name(self, ctx, *, user: discord.User = None, name: str = None, reason: str = None):
        """
        Updates the user with the new name.
        """
        if user is None or name is None or reason is None:
            return log.error("Cannot update name if any one item of the following are not provided: user, name, or reason")

        try:
            await user.edit(reason=reason, nick=name)
        except discord.Forbidden:
            # Changing this users name is not allowed due to insuffienct permissions.
            log.debug(f"Changing {user.name}'s name is not allowed due to insuffienct permissions.")
        except discord.HTTPException:
            await log.exception(f"Failed to edit {user.name}'s name.")      

    async def confirm(self, ctx, *, msg="Are you sure?"):
        """
        Handles confirmations for commands.
        Optionally can supply a message that is displayed to the user. Defaults to 'Are you sure?'.
        """
        await ctx.channel.send(f"{msg} (y/n)")
        pred = MessagePredicate.yes_or_no(ctx)
        await self.bot.wait_for("message", check=pred)
        return pred.result        