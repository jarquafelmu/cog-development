from .rolemanager import RoleManager
from .greet import Greet
from .channels import Channels
from .logic import Logic


async def setup(bot):
    args = {
        "guild_id": 493875452046475275,
        "channels": Channels(bot),
        "logic": Logic(bot)
    }

    # RoleManager cog stuff
    cog = RoleManager(bot, args)
    bot.add_cog(cog)

    # Greet cog stuff
    cog = Greet(bot, args)
    bot.add_cog(cog)
