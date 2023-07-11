import asyncio
import json
import time

from threading import Thread
from typing import Optional

# import time
import openai

from asgiref.sync import async_to_sync
from pydantic import BaseModel
from twitchio.ext import commands
from twitchio.channel import Channel


# Load the configuration file
with open('config.json') as config_file:
    config = json.load(config_file)

# Now you can access your keys
client_id = config['twitch']['clientkey']
channel_name = config['twitch']['hostchannel']
openai_api_key = config['openai']['api_key']
openai.api_key = openai_api_key

# constants
vote_delay = 20


# BaseModel is similar to a dataclass (used to store data in a structure way)
class StoryEntry(BaseModel):
    story_action: str
    narration_result: str


class Proposal(BaseModel):
    user: str
    message: str
    vote: int


class StoryGenerator:
    def __init__(self):
        # TODO: Dynamically generate initial prompt
        self.past_story_entries = [
            StoryEntry(
                story_action='',
                # narration_result="You are a middle aged man in downtown Chicago, 1910. You're in a steak restaurant talking to the waiter as you just sat down.",
                # narration_result="You are a quirky time travelling inventor with a handlebar mustache and a knack for mischievous inventions. Blinking your eyes open, you realize you have accidentally landed in the year 1875, right in the heart of a bustling Wild West town. Dusty roads, saloons, and cowboys on horseback surround you, while the sound of piano music drifts through the air.",
                narration_result="You're a jovial gnome bard, renowned across the taverns of Baldur's Gate for your quick wit and sparkling lute melodies. It's the Year of the Spitting Triton, and you find yourself in the bustling city market, surrounded by a cacophony of traders, minstrels, and townsfolk. Suddenly, a bedraggled messenger races towards you - he carries a message ",
            )
        ]

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

                            2. Sometimes, people are secretly bears.

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


# placeholder for quest handler
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


class VoteHandler:
    async def add_vote_option(self, username: str, message: str):
        """ "Adds a vote option to the list of proposals. Expects '!voteoption <string>' as a user command"""
        proposal = Proposal(user=username, message=message, vote=0)
        print(proposal)
        self.proposals.append(proposal)
        return f'Option {len(self.proposals)} added: {message}'

    async def add_mod_vote(self, username: str, vote_option: int):
        """ "Adds a vote to a currently existing proposal. Expects '!vote <int>' as a user command"""
        for idx, proposal in enumerate(self.proposals):
            if idx == vote_option - 1:
                proposal.vote += 999999
                return f'Mod Vote added for option {vote_option}. Current votes: {proposal.vote}'
        return f'Vote option not found: {vote_option}'

    def reset(self):
        """ "Clears all vote options"""
        self.proposals = []


class LlmGameHooks:
    def on_choose_proposal(self, proposal: Proposal):
        pass

    def on_get_narration_result(
        self, narration_result: str, proposal: Proposal, proposal_id: int
    ):
        pass


class LlmGame:
    def __init__(self, hooks: LlmGameHooks = LlmGameHooks()):
        self.generator = StoryGenerator()
        self.background_thread = None
        self.hooks = hooks
        self.proposals: list[Proposal] = []

    @property
    def initial_story_message(self) -> str:
        # We should always have at least the initial story message
        assert self.generator.past_story_entries
        return self.generator.past_story_entries[-1].narration_result

    def vote(self, proposal_id: int, weight: int = 1) -> int:
        if not 0 < proposal_id <= len(self.proposals):
            raise ValueError(f'Invalid proposal id: {proposal_id}')
        self.proposals[proposal_id - 1].vote += weight
        return self.proposals[proposal_id - 1].vote

    def restart(self):
        self.generator = StoryGenerator()
        self.background_thread = None

    def add_proposal(self, story_action: str, author: str) -> int:
        proposal = Proposal(user=author, message=story_action, vote=0)
        print(proposal)
        self.proposals.append(proposal)
        proposal_id = len(self.proposals)
        if self.background_thread is None:
            self.background_thread = Thread(
                target=self._background_thread_run, daemon=True
            )
            self.background_thread.start()
        return proposal_id

    def _background_thread_run(self):
        time.sleep(vote_delay)

        proposal = max(self.proposals, key=lambda x: x.vote)
        proposal_id = self.proposals.index(proposal)
        self.hooks.on_choose_proposal(proposal)
        narration_result = self.generator.generate_next_story_narration(
            proposal.message
        )
        self.hooks.on_get_narration_result(narration_result, proposal, proposal_id)
        self.proposals = []
        self.background_thread = None


class Bot(commands.Bot, LlmGameHooks):
    max_message_len = 500  # Twitch has a 500 character limit

    def __init__(self, llm_game: LlmGame):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        super().__init__(token=client_id, prefix='!', initial_channels=[channel_name])
        self.game = llm_game
        self.channel: Optional[Channel] = None

    async def event_ready(self):
        """Function that runs when bot connects to server"""
        asyncio.get_running_loop().set_debug(True)
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        self.channel = self.get_channel(channel_name)
        await self.channel.send(f'Story: {self.game.initial_story_message}')

    @commands.command()
    async def action(self, ctx: commands.Context):
        """Trigger for user to perofrm an action within the game"""
        story_action = self._extract_message_text(ctx)
        await self._propose_story_action(story_action, ctx.author.name)

    @commands.command()
    async def say(self, ctx: commands.Context):
        """Trigger for user to say something within the game"""
        story_action = 'You say "' + self._extract_message_text(ctx) + '"'
        await self._propose_story_action(story_action, ctx.author.name)

    @commands.command()
    async def vote(self, ctx):
        await self._vote(ctx)

    @commands.command()
    async def help(self, ctx: commands.Context):
        """Help command"""
        await self._send(
            'Welcome to the Storyteller! The goal of this game is to collaboratively create a story. At each turn, the user says an action and the bot replies with a short continuation of the story outlining the events that happen in the story based on the action the user performed. The user can then vote on the next action to perform. The bot will then continue the story based on the action with the most votes. To perform an action, type "!action <action>". To say something, type "!say <message>". To vote on the next action, type "!vote <number>".'
        )

    # --- MOD COMMANDS ---

    @commands.command()
    async def reset(self, ctx: commands.Context):
        """Resets the game if the user is a mod"""
        if ctx.author.is_mod:
            self.game.restart()
            await self._send('Game has been reset')
        else:
            await self._send(ctx.author.name + ', You are not a mod')

    @commands.command()
    async def modvote(self, ctx: commands.Context):
        if ctx.author.is_mod:
            await self._vote(ctx, weight=99)
        else:
            await self._send(ctx.author.name + ', You are not a mod')

    # --- Other Methods ---

    async def _vote(self, ctx: commands.Context, weight: int = 1):
        vote_option_str = self._extract_message_text(ctx)
        try:
            new_count = self.game.vote(int(vote_option_str))
        except ValueError:
            await self._send(f'Invalid vote option: {vote_option_str}')
        else:
            await self._send(
                f'Vote added for option {vote_option_str}. Current votes: {new_count}'
            )

    @async_to_sync
    async def on_get_narration_result(
        self, narration_result: str, proposal: Proposal, proposal_id: int
    ):
        await self._send_chunked(
            f'Chose action {proposal_id} ({proposal.vote} votes): {proposal.message} | {narration_result}'
        )

    async def _propose_story_action(self, story_action: str, author: str):
        """Continues the story by performing an action, communicating the result to the channel"""
        proposal_id = self.game.add_proposal(story_action, author)
        await self._send(f'Option {proposal_id} added: {story_action}')

    async def _send_chunked(self, text: str):
        while text:
            suffix = '...' if len(text) >= self.max_message_len else ''
            await self._send(text[: self.max_message_len - 3] + suffix)
            print(text[: self.max_message_len - 3] + suffix)
            await asyncio.sleep(2.0)
            text = text[self.max_message_len - 3 :]

    @staticmethod
    def _extract_message_text(ctx: commands.Context) -> str:
        """
        Extract the text part of a user message after the command
        (ie. "bar baz" from the message "!foo bar baz")
        """
        return ctx.message.content.split(' ', 1)[1]

    async def _send(self, message: str):
        await self.channel.send(message)


def main():
    llm_game = LlmGame()
    bot = Bot(llm_game)
    llm_game.hooks = bot
    bot.run()


if __name__ == '__main__':
    main()
