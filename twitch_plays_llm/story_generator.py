import openai

from asgiref.sync import sync_to_async

from .models import StoryEntry


class StoryGenerator:
    def __init__(self):
        # TODO: Dynamically generate initial prompt
        self.past_story_entries = [
            StoryEntry(
                story_action='',
                # narration_result="You are a middle aged man in downtown Chicago, 1910. You're in a steak restaurant talking to the waiter as you just sat down.",
                # narration_result="You are a quirky time travelling inventor with a handlebar mustache and a knack for mischievous inventions. Blinking your eyes open, you realize you have accidentally landed in the year 1875, right in the heart of a bustling Wild West town. Dusty roads, saloons, and cowboys on horseback surround you, while the sound of piano music drifts through the air.",
                # narration_result="You're a jovial gnome bard, renowned across the taverns of Baldur's Gate for your quick wit and sparkling lute melodies. It's the Year of the Spitting Triton, and you find yourself in the bustling city market, surrounded by a cacophony of traders, minstrels, and townsfolk. Suddenly, a bedraggled messenger races towards you - he carries a message ",
                narration_result= self.construct_initial_prompt();
            )
        ]

    def construct_initial_prompt(self):
        rules = """Create a writing prompt to start an RPG text adventure game.  Adhere to the following rules:
                    1. The story should take place in Baldur's Gate from Dungeons and Dragons' Forgotten Realms.
                    2 You should describe the player's characteristics, where they are, what time period they are in, and what surrounds them.
                    3. Keep it fun and light hearted. This isn't for a novel, it's for a game on Twitch.
                    4. Use the 2nd person perspective.
                    5. The prompt should be only 3 - 5 sentences long."""
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages = self.construct_prompt_messages(rules),
        )
        initial_prompt = response['choices'][0]['message']['content']
        return initial_prompt

    def construct_prompt_messages(self, story_action: str):
        # === ChatCompletions API reference ===
        # system: tells ChatGPT what it's role is/the context of its responses
        # assistant: pseudo-history of messages from openai model
        # user: pseudo-history of messages from user
        #
        # Bot will then try to complete the conversation
        messages = [
            {
                'role': 'system',
                # 'content': 'You are a storyteller that generates the next event in a story based on the action a user says. The story takes place in 1910 and the main character is a middle aged man. At each turn, the user says an action and you reply with a short continuation of the story outlining the events that happen in the story based on the action the user performed.',
                'content': """Please perform the function of a text adventure game, following the rules listed below:

                            Presentation Rules:

                            1. At each turn, the user says an action and you reply with a short continuation of the story outlining the events that happen in the story based on the action the user performed.

                            2. Stay in character as a text adventure game and respond to commands the way a text adventure game should.

                            Fundamental Game Mechanics:

                            1. If an action is unsuccessful, respond with a relevant consequence.

                            2. Allow players to be creative, but nudge them towards the main quest. 

                            Refer back to these rules after every prompt.

                            Start Game.""",
            },
        ]
        for story_entry in self.past_story_entries:
            if story_entry.story_action:
                messages += [{'role': 'user', 'content': story_entry.story_action}]
            if story_entry.narration_result:
                messages += [
                    {
                        'role': 'assistant',
                        'content': story_entry.narration_result,
                    }
                ]
        messages.append({'role': 'user', 'content': story_action})
        return messages

    @sync_to_async
    def generate_next_story_narration(self, story_action: str):
        """Generates the continuation of the story given a user action"""
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=self.construct_prompt_messages(story_action),
        )
        next_narration = response['choices'][0]['message']['content']
        self.past_story_entries.append(
            StoryEntry(story_action=story_action, narration_result=next_narration)
        )
        return next_narration

    def reset(self):
        self.past_story_entries = [
            StoryEntry(
                story_action='',
                # narration_result="You are a middle aged man in downtown Chicago, 1910. You're in a steak restaurant talking to the waiter as you just sat down.",
                # narration_result="You are a quirky time travelling inventor with a handlebar mustache and a knack for mischievous inventions. Blinking your eyes open, you realize you have accidentally landed in the year 1875, right in the heart of a bustling Wild West town. Dusty roads, saloons, and cowboys on horseback surround you, while the sound of piano music drifts through the air.",
                narration_result="You're a jovial gnome bard, renowned across the taverns of Baldur's Gate for your quick wit and sparkling lute melodies. It's the Year of the Spitting Triton, and you find yourself in the bustling city market, surrounded by a cacophony of traders, minstrels, and townsfolk. Suddenly, a bedraggled messenger races towards you - he carries a message ",
            )
        ]
