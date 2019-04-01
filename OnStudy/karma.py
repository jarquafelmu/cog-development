from redbot.core import Config, commands, checks
from redbot.core.utils.chat_formatting import error, info, warning
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.embed import randomize_color
from .logger import logger
from enum import Enum

import discord

class Karma(commands.Cog):
    """
    Handles functions regarding karma
    """
    class Endorsements(Enum):
        MEMBER = {
            "emoji": "\N{Thumbs Up Sign}",
            "value": 1
        }
        STAFF = {
            "emoji": "\N{Exploding Star}",
            "value": 5
        }

    properties = {
        "channels": None,
        "logic": None,
        "karma_per_vote": 1
    }
    karma_roles = {
        "thanked": {
            "name": "been_thanked",
            "id": 543540754702794772
        },
        "thanking": {
            "name": "thanked_others",
            "id": 543540865789067265
        }
    }

    def __init__(self, bot, args):
        """Initialization function"""
        self.bot = bot
        self.guild_id = args["guild_id"]
        self.properties["channels"] = args["channels"]
        self.properties["logic"] = args["logic"]
        endorsements_values = set(item.value["emoji"] for item in self.Endorsements)     
    
        self.db = Config.get_conf(self, identifier=1742113358, force_registration=True)
        
        default_member = {
            "been_thanked": {
                "total": 0,
                "current": 0
            },
            "thanked_others": {
                "total": 0,
                "current": 0
            }
        }

        self.db.register_member(**default_member)

        
    def getEndorsement(self, emoji: str) -> dict:
        # gets the first item rom fthe Endorsements enum which contains an emoji 
        # that matches the passed in one
        return next((x.value for x in self.Endorsements if x.value.emoji == emoji), None)

    @commands.group(name="karma", aliases=["k", "Karma"])
    async def _karma(self, ctx):
        """
        A group of commands for the karma cog.
        """
        # if ctx.invoked_subcommand is None:
        #     await self.build_karma_view(ctx, ctx.author)
        pass
        
    @_karma.command(name="check", aliases=["c"])
    async def _check_user_karma(self, ctx, member: discord.Member):
        """
        Displays a user's karma score.
        """
        karma_view = await self.build_karma_view(ctx, member)
        if karma_view:
            await ctx.send(embed=karma_view)
        else:
            await ctx.send(error("Member wasn't found."))


    async def build_karma_view(self, ctx, member: discord.Member):
        """
        Displays a user's karma score.
        """
        if not isinstance(member, discord.Member):
            try:
                member = self.bot.get_guild(self.guild_id).get_member(int(member))
            except ValueError:
                msg = f"{member} is not a valid member id."
                logger.exception(msg)
                await ctx.send(warning("Oops, Something went wrong. Ask an **admin** or **bot-dev** to check the log."))
                return await self.properties["channels"].log.send(error(msg))        
        
        if member is None:
            return await ctx.send(warning(
                "User not found."
            ))

        def build_field(group):
            return (
                f"**Current:** {group['current']}\n"
                f"**All Time:** {group['total']}"
            )

        try:
            been_thanked_val = build_field(
                await self.db.member(member).been_thanked()
            )
            thanked_others_val = build_field(
                await self.db.member(member).thanked_others()
            )
        except KeyError:
            logger.error("Member does not exist.")
            return None
        else:
            embed = discord.Embed(title=f"{member.display_name}'s karma")
            embed.add_field(name="Thanked by others", value=been_thanked_val, inline=False)
            embed.add_field(name="Thanked others", value=thanked_others_val, inline=False)
            return randomize_color(embed)

    @_karma.command(name="sync")
    @checks.admin()
    async def _karma_sync(self, ctx):
        """
        Syncs the karma scores for all users across the server. 
        **WARNING**: This could take a long time. Please be patient.
        """
        # confirm this request
        pred = await self.properties["logic"].confirm(ctx, msg=(
            "This will reset all karma scores and then will process all of the messages on the server. "
            "This process could take a while. **Are you sure you wish to continue?**"
        ))
        if pred is False:
            return await ctx.send("Standing down.")
        else:
            await ctx.send("Beginning process.")
            logger.debug("Syncing karma scores.")

        # reset karma scores
        await self.clear_karma(ctx)

        async def status_msg(ctx, msg, *, msgObj = None):
            if msgObj is None:
                return await ctx.send(msg)
            try:
                await msgObj.edit(content=msg)
            except discord.HTTPException:
                logger.exception("Editing sync heartbeat message failed.")

        # get the list of channels
        channels = self.bot.get_guild(self.guild_id).text_channels
        channels_processed = 0

        # annouce how many channels are to be processed
        channels_processed_msg = lambda current, total: f"Processed {current} of {total} channels."
        processedMsgObj = await status_msg(ctx, channels_processed_msg(channels_processed, len(channels)))

        latest_channel_msgObj = None
        async with ctx.channel.typing():
            # iterate through each channel:
            for channel in channels:
                if channel.id in self.properties["channels"].ids.values():
                    logger.info(f"Skipping channel {channel.name} during karma sync.")
                    continue

                endorsements = 0     
                msg_count = 0
                # iterate through the message history
                async for message in channel.history(limit=None):
                    msg_count += 1
                    # process the reactions for the karma one
                    payload = {}
                    if message.author.bot:
                        continue
                    if not self.properties["logic"].validate_member(message.author):
                        await self.properties["channels"].log.send(error(
                                    f"Skipped author {message.author.display_name} for message "
                                    f"{message.id} in channel {channel.name} as "
                                    "this user is not a valid member."
                            ))
                        continue
                    payload["recipient"] = message.author                        
                    for react in message.reactions:
                        if (str(react.emoji) not in self.endorsements_values):
                            continue

                        logger.debug("Found endorsement")

                        async for user in react.users():
                            if not self.properties["logic"].validate_member(user):
                                await self.properties["channels"].log.send(error(
                                    f"Skipped user {user.display_name} for message "
                                    f"{message.id} in channel {channel.name} as "
                                    "this user is not a valid member."
                                    ))
                                continue

                            # we have a user who is a valid member of the guild
                            payload["sender"] = user

                            await self.properties["channels"].log.send(
                                f"Endorsement to `{payload['recipient'].display_name}` from `{payload['sender'].display_name}`"
                            )

                            # apply the normal rules for adding karma
                            await self.process_reaction(payload=payload)
                            endorsements += 1

                # announce channel is done
                latest_channel = lambda channel: f"Processed channel: {channel}."
                if latest_channel_msgObj is None:
                    latest_channel_msgObj = await status_msg(ctx, latest_channel(channel.name))
                else:                    
                    await status_msg(ctx, latest_channel(channel.name), msgObj = latest_channel_msgObj)
                logger.debug(latest_channel(channel.name))

                await ctx.send(info(
                    f"**__{channel.name}:__**\n"
                    f"messages: {msg_count}\n"
                    f"endorsements: {endorsements}"
                ))
                
                channels_processed += 1

                # edit channel processed message to update the completed number
                await status_msg(ctx, channels_processed_msg(channels_processed, len(channels)), msgObj=processedMsgObj)
            await ctx.send("Done.")
            logger.debug("Done.")

    @_karma.group(name="settings", aliases=["s", "set"])
    @checks.admin()
    async def _karma_settings(self, ctx):
        """
        A group of commands for managing the settings for the karma cog
        """
        pass

    @_karma_settings.command(name="reset")
    @checks.admin()
    async def _karma_settings_reset(self, ctx):
        """
        Clears the karma data.
        """

        # clears all the data stored for member of this guild in the database
        msg = (
            "Reset the karma for all members?"
            " There is **no** undo option!"
        )
        if await self.properties["logic"].confirm(ctx, msg=msg):
            await self.clear_karma(ctx)
        await ctx.send("Done.")

    async def clear_karma(self, ctx):
        logger.info("Resetting all member's karma scores!")
        await ctx.send("Resetting all member's karma scores!")
        await self.db.clear_all_members(ctx.guild)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Member agrees to the rules.
        """
        await self.process_reaction(payload=payload, is_add_action=True)
        

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """
        Member no longer agrees to the rules.
        """
        await self.process_reaction(payload=payload, is_add_action=False)
        

    async def process_reaction(self, *, payload = None, is_add_action: bool = True):
        """
        Processes the reaction to see if it is a karma reaction.
        """
        if payload is None:            
            return logger.error("payload is none!")

        if isinstance(payload, dict):
            member_receiving = payload["recipient"]
            member_giving = payload["sender"]
            emoji = str(payload["emoji"])
        else:
            # get the member from the guild using the user_id in the payload
            member_giving = self.bot.get_guild(self.guild_id).get_member(payload.user_id)
            channel = self.bot.get_guild(self.guild_id).get_channel(payload.channel_id)
            message = await channel.get_message(payload.message_id)
            member_receiving = message.author
            emoji = str(payload.emoji)

        if emoji not in self.endorsements_values:
            return

        if member_giving.id == member_receiving.id:
            return logger.debug("member cannot give themselves karma.")

        if member_receiving.bot:
            return logger.debug("bot may not receive karma.")

        endorsement = self.getEndorsement(emoji)
        if endorsement is None:
            return logger.error(f"Endorsement {emoji} not recognized.")

        modifier = endorsement["value"] * 1 if is_add_action else -1

        await self.modify_karma(member_giving, member_receiving, modifier)
        
    async def modify_karma(self, member_giving, member_receiving, modifier):
        """
        Adds a karma point to both users
        """
        await self.update_karma_category(member_giving, self.karma_roles["thanking"]["name"], modifier)

        await self.update_karma_category(member_receiving, self.karma_roles["thanked"]["name"], modifier)

        msg = f"{member_giving.name} { 'added' if modifier > 0 else 'removed'} an endorsement { 'to' if modifier > 0 else ' from '} {member_receiving.name}"
        await self.properties["channels"].log.send(msg)
        logger.debug(msg)
                
    def nonnegative(self, val: int):
        """
        Returns either the `val` or zero.
        """
        return max(val, 0)

    async def update_karma_category(self, member: discord.Member, category_id: str, modifier: int):
        """
        Applies the modifier to the user's thanked score.
        """
        try:
            thank_category = await self.db.member(member).get_raw(category_id)

            thank_category["total"] = self.nonnegative(
                thank_category["total"] + modifier
            )
            thank_category["current"] = self.nonnegative(
                thank_category["current"] + modifier
            )

            await self.db.member(member).set_raw(category_id, value=thank_category)
        except KeyError:
            logger.exception("Member doesn't exist.")