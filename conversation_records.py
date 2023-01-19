class ConversationRecords:
    def __init__(self):
        self.conversation_scripts: dict = {}
        self.conversation_user_turn: int = 0
        self.conversation_bot_turn: int = 0


    def next_user_turn(self):
        self.conversation_user_turn += 1
        return self.conversation_user_turn


    def next_bot_turn(self):
        self.conversation_bot_turn += 1
        return self.conversation_bot_turn


    def next_turn(self):
        return self.conversation_bot_turn + self.conversation_user_turn


    def add_turn(self, message: str, bot_turn: bool = True):
        if bot_turn:
            speaker = "bot"
            speaker_turn = self.next_bot_turn()
        else:
            speaker = "user"
            speaker_turn = self.next_user_turn()
        self.conversation_scripts[f"turn{str(self.next_turn())}_{speaker}{str(speaker_turn)}"] = message


    def reset(self):
        self.conversation_scripts = {}
        self.conversation_bot_turn = 0
        self.conversation_user_turn = 0
