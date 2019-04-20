
from .greet import Greet


def setup(bot):
    cog = Greet(bot)
    bot.add_listener(cog.greetMember, "on_member_join")
    bot.add_cog(cog)