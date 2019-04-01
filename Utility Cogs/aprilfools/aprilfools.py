from redbot.core import commands, checks, Config
from redbot.core.utils.chat_formatting import pagify, bold, error, warning, humanize_list

import logging
import discord
import enum


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
            "cached_username": "",
            "pranking_allowed": True
        }

        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)

    @commands.group(name="set", aliases=["set"])
    @checks.admin()
    async def _aprilfools(self, ctx):
        pass
    
    @_aprilfools.command(name="name")
    async def set_name(self, ctx, name: str):
        current_prank_name = await self.config.guild(ctx.guild).prank_name()
        await self.config.guild(ctx.guild).prank_name.set(name)
        await ctx.send(f"Changed name from {current_prank_name} to {name}")

    @_aprilfools.command(name="forbidden", aliases=["forbid"])
    async def set_forbidden_users(self, ctx, user_ids: commands.Greedy[int]):
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
    
    @commands.command()
    @checks.admin()
    async def deploy(self, ctx):
        if not await self.config.guild(ctx.guild).prank_name():
            return await ctx.send(error("Prank name is not set. Cannot proceed until it is set."))
        self.process(ctx, Action.DEPLOY)
        pass
    
    @commands.command()
    @checks.admin()
    async def revert(self, ctx):
        if not await self.config.guild(ctx.guild).prank_name():
            return await ctx.send(error("Prank name is not set. Cannot proceed until it is set."))
        self.process(ctx, Action.REVERT)
        pass

    async def process(self, ctx, action: Action):
        async with ctx.channel.typing():
            # guild = self.bot.get_guild(self.guild_id)
            users = ctx.guild.users
            current = 0
            total = len(users)
            msg = await ctx.send(f"Processed {current} of {total} users.")
            for user in users:
                current += 1
                if user.bot: 
                    continue

                if action == Action.DEPLOY:
                    self.prank(ctx, user)
                elif action == Action.REVERT:
                    self.unprank(ctx, user)

                try:
                    await msg.edit(content=f"Processed {current} of {total} users.")
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

            await self.config.user(user).cached_username.set(user.display_name)     
            await user.edit(reason=f"Changing name for April Fools prank.", nick=await self.config.guild(ctx.guild).prank_name())
        except KeyError:
            await ctx.send(error("User doesn't exist in database."))
            log.exception("User doesn't exist in database.")
        except discord.Forbidden:
            # Changing this users name is not allowed due to insuffienct permissions.
            log.debug(f"Changing this {user.name}'s name is not allowed due to insuffienct permissions.")
        except discord.HTTPException:
            await log.exception(f"Failed to edit {user.name}'s name.")
        pass

    async def unprank(self, ctx, user: discord.User = None):
        """
        Revert's a user's display name back to their cached name or to their 
        default username if the cached version does not exist.
        """
        if user is None:            
            return log.debug("No user object supplied.")

        # only revert the name if it's still the prank name
        if not user.display_name == await self.config.guild(ctx.guild).prank_name():
            return log.debug("User's display name is no longer the pranked name. Terminating")

        try:
            cached_user = await self.config.user(user)
            name = cached_user["name"]
            name_used = "cached name"
        except KeyError:
            log.warning(f"No cached version of {user.name} exists. Using default username.")
            name = user.name
            name_used = "default name"
        except discord.HTTPException:
            await log.exception(f"Failed to edit {user.name}'s name.")
            return

        await user.edit(reason=f"Reverting name from april fools prank. Used {name_used}.", nick=name)