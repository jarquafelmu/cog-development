from redbot.core import commands


class OSChannels(commands.Cog):
    """
    Enum for channels to make it simplier to access them when needed
    """    
    __channel_ids = {        
        "bot-commands": 484369915793637378,
        "bot-log": 485218362272645120,
        "courseList": 514518408122073116,
        "log": 485218362272645120,
        "newMembers": 484378858968055814,
        "warnings": 492816618808934410,
        "welcome": 514572072794587136
    }

    def __init__(self, bot):
        self.bot = bot
        self.ids = self.__channel_ids
        
        # channels
        self.__channel_courseList = None
        self.__channel_log = None
        self.__channel_newMembers = None
        self.__channel_welcome = None

    @property
    def courseList(self):
        """
        Course List channel object
        """
        if self.__channel_courseList is None:
            self.__channel_courseList = self.bot.get_channel(self.__channel_ids["courseList"])
        return self.__channel_courseList

    @property
    def log(self):
        """
        Logging channel object
        """
        if self.__channel_log is None:
            self.__channel_log = self.bot.get_channel(self.__channel_ids["log"])
        return self.__channel_log

    @property
    def newMembers(self):
        """
        New Members channel object
        """
        if self.__channel_newMembers is None:
            self.__channel_newMembers = self.bot.get_channel(self.__channel_ids["newMembers"])
        return self.__channel_newMembers

    @property
    def welcome(self):
        """
        Welcome channel object
        """
        if self.__channel_welcome is None:
            self.__channel_welcome = self.bot.get_channel(self.__channel_ids["welcome"])
        return self.__channel_welcome

    def anchor(self, channel):
        """
        Formats the channel for embedding in a string
        """
        return f"<#{channel}>"