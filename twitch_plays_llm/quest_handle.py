# placeholder for quest handler
from ..models.py import StoryEntry


class QuestHandler:
    def __init__(self, quest):
        self.quest = quest

    def evaluateQuest(self, context: list[StoryEntry]):
        """Evaluates the current quest and returns a boolean indicating whether the quest is complete"""
        [
            {
                'role': 'system',
                'content': """Acting as a quest classifier for a adventure game, classify whether a player has fulfilled the quest or not. Classify and respond with "Complete", "Incomplete", or "Failure" """,
            },
        ]
