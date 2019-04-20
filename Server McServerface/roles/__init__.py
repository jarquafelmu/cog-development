from .roles import RoleManager


def setup(bot):
    cog = RoleManager(bot)
    bot.add_cog(cog)
