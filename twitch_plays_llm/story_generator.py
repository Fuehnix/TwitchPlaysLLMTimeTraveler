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
                narration_result=
                "In the heart of the soot-covered city of Cogspeak, where towering edifices of "
                "brass and iron belch steam into the clouded sky, resides Esther, a blend of "
                "artist, programmer, and aviary admirer. Her living quarters, an entanglement of "
                "refurbished clockwork machinery and assorted avian-inspired artworks, oscillates "
                "between the symphony of grinding gears and the harmonious chirping of caged "
                "mechanical birds. Esther’s world is steeped in Steampunk charm, yet it brims "
                "with the arcane; she wields the power to morph into any bird she desires, an "
                "ability she often uses for swift travel across the sprawling metropolis or for "
                "surreptitious spying on the city's upper echelons. In the maelstrom of her mind, "
                "a multitude of voices echoes - a chorus she lovingly dubs her 'Twitch'. These "
                "voices command her actions, guiding her through time-warping exploits that not "
                "only defy the standard tick-tock flow of her world but also have a profound "
                "impact on Cogspeak’s timeline, with every decision setting off a chain of events "
                "that ripple through her reality. One balmy evening, as Esther was transforming "
                "back to her human form after an exhilarating flight across Cogspeak, a "
                "thunderous tremor rocked the city, followed by the eerie whine of a machine in "
                "duress. When she looked out, she saw a pillar of ghostly green light shooting "
                "skywards from the center of the city, a place notoriously known as the "
                "Clocktower Citadel - the heart of time itself. In the aftermath, the rhythmic "
                "ticking that underpinned life in Cogspeak fell silent, and time stood eerily "
                "still. Soon, her 'Twitch' was overwhelmed with pleas for help from terrified "
                "cityfolk frozen in time. Esther knew she had to restore the Citadel's Clockwork "
                "Heart to set time in motion again. Guided by the cacophony of her Twitch, she "
                "embarked on a perilous quest through a city locked in a timeless prison, "
                "carrying the hope of every soul entrapped within Cogspeak."
            )
        ]

    def construct_initial_prompt(self):
        """Not used
        construct initial prompt for story generation"""
        rules = """Create a writing prompt to start an RPG text adventure game.  Adhere to the following rules:
                    1. The story should take place in Baldur's Gate from Dungeons and Dragons' Forgotten Realms.
                    2  You should describe the player's characteristics, where they are, what time period they are in, and what surrounds them.
                    3. Keep it fun and allow people to be creative.
                    4. Use the 2nd person perspective.
                    5. The prompt should be only 3 - 5 sentences long."""
        messages = [{ 'role': 'user',
                'content': rules}]

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages = messages,
        )
        initial_prompt = response['choices'][0]['message']['content']
        print('generated initial prompt')
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
