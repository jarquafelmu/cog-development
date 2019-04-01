from .aprilfools import AprilFools


async def setup(bot):
    cog = AprilFools(bot)
    bot.add_cog(cog)
