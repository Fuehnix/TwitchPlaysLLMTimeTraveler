import asyncio
import json

# import time
import openai

from pydantic import BaseModel
from twitchio.ext import commands

# Load the configuration file
with open('config.json') as config_file:
    config = json.load(config_file)

# Now you can access your keys
client_id = config['twitch']['clientkey']
channel_name = config['twitch']['hostchannel']
openai_api_key = config['openai']['api_key']
openai.api_key = openai_api_key





# BaseModel is similar to a dataclass (used to store data in a structure way)
class StoryEntry(BaseModel):
    user_action: str
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
                user_action='',
                # narration_result="You are a middle aged man in downtown Chicago, 1910. You're in a steak restaurant talking to the waiter as you just sat down.",
                # narration_result="You are a quirky time travelling inventor with a handlebar mustache and a knack for mischievous inventions. Blinking your eyes open, you realize you have accidentally landed in the year 1875, right in the heart of a bustling Wild West town. Dusty roads, saloons, and cowboys on horseback surround you, while the sound of piano music drifts through the air.",
                narration_result="You're a jovial gnome bard, renowned across the taverns of Baldur's Gate for your quick wit and sparkling lute melodies. It's the Year of the Spitting Triton, and you find yourself in the bustling city market, surrounded by a cacophony of traders, minstrels, and townsfolk. Suddenly, a bedraggled messenger races towards you - he carries a message "
            )
        ]

    def construct_prompt_messages(self, user_action: str):
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

                            1. Play the game in turns, starting with you.

                            2. Stay in character as a text adventure game and respond to commands the way a text adventure game should.

                            3. Have an NPC in the story scold the player if they try to do something that is not possible. If they are alone, God will scold them.

                            Fundamental Game Mechanics:

                            1. If an action is unsuccessful, respond with a relevant consequence.

                            Refer back to these rules after every prompt.

                            Start Game."""
            },
        ]
        for story_entry in self.past_story_entries:
            if story_entry.user_action:
                messages += [{'role': 'user', 'content': story_entry.user_action}]
            if story_entry.narration_result:
                messages += [
                    {
                        'role': 'assistant',
                        'content': story_entry.narration_result,
                    }
                ]
        messages.append({'role': 'user', 'content': user_action})
        return messages

    def generate_next_story_narration(self, user_action: str):
        """Generates the continuation of the story given a user action"""
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=self.construct_prompt_messages(user_action),
        )
        next_narration = response['choices'][0]['message']['content']
        self.past_story_entries.append(
            StoryEntry(user_action=user_action, narration_result=next_narration)
        )
        return next_narration
    
    def reset(self):
        self.past_story_entries = [
            StoryEntry(
                user_action='',
                # narration_result="You are a middle aged man in downtown Chicago, 1910. You're in a steak restaurant talking to the waiter as you just sat down.",
                # narration_result="You are a quirky time travelling inventor with a handlebar mustache and a knack for mischievous inventions. Blinking your eyes open, you realize you have accidentally landed in the year 1875, right in the heart of a bustling Wild West town. Dusty roads, saloons, and cowboys on horseback surround you, while the sound of piano music drifts through the air.",
                narration_result="You're a jovial gnome bard, renowned across the taverns of Baldur's Gate for your quick wit and sparkling lute melodies. It's the Year of the Spitting Triton, and you find yourself in the bustling city market, surrounded by a cacophony of traders, minstrels, and townsfolk. Suddenly, a bedraggled messenger races towards you - he carries a message "
            )
        ]

class VoteHandler:
    def __init__(self):
        self.proposals: list[Proposal] = []

    async def add_vote_option(self, username: str, message: str):
        """ "Adds a vote option to the list of proposals. Expects '!voteoption <string>' as a user command"""
        proposal = Proposal(user=username, message=message, vote=0)
        print(proposal)
        self.proposals.append(proposal)
        return f'Option {len(self.proposals)} added: {message}'

    async def add_vote(self, username: str, vote_option: int):
        """ "Adds a vote to a currently existing proposal. Expects '!vote <int>' as a user command"""
        for idx, proposal in enumerate(self.proposals):
            if idx == vote_option - 1:
                proposal.vote += 1
                return f'Vote added for option {vote_option}. Current votes: {proposal.vote}'
        return f'Vote option not found: {vote_option}'

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


class Bot(commands.Bot):
    max_message_len = 500  # Twitch has a 500 character limit

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        super().__init__(token=client_id, prefix='!', initial_channels=[channel_name])
        self.generator = StoryGenerator()
        self.vote_handler = VoteHandler()
        self.background_task = None

    async def event_ready(self):
        """Function that runs when bot connects to server"""

        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        if self.generator.past_story_entries:
            last_narration = self.generator.past_story_entries[-1].narration_result
            await self.get_channel(channel_name).send(f'Story: {last_narration}')

    @commands.command()
    async def action(self, ctx: commands.Context):
        """Trigger for user to perofrm an action within the game"""
        user_action = self._extract_message_text(ctx)
        await self._perform_action(user_action, ctx)

    @commands.command()
    async def say(self, ctx: commands.Context):
        """Trigger for user to say something within the game"""
        user_action = 'You say "' + self._extract_message_text(ctx) + '"'
        await self._perform_action(user_action, ctx)

    @commands.command()
    async def vote(self, ctx: commands.Context):
        await ctx.send(
            await self.vote_handler.add_vote(
                ctx.author.name, int(self._extract_message_text(ctx))
            )
        )
    


    @commands.command()
    async def help(self, ctx: commands.Context):
        """Help command"""
        await ctx.send(
            'Welcome to the Storyteller! The goal of this game is to collaboratively create a story. At each turn, the user says an action and the bot replies with a short continuation of the story outlining the events that happen in the story based on the action the user performed. The user can then vote on the next action to perform. The bot will then continue the story based on the action with the most votes. To perform an action, type "!action <action>". To say something, type "!say <message>". To vote on the next action, type "!vote <number>".'
        )


    ### MOD COMMANDS ###
    @commands.command()
    async def reset(self, ctx: commands.Context):
        """Resets the game if the user is a mod"""
        if (ctx.author.is_mod()):
            # self.vote_handler.reset()
            # self.generator.reset()
            self.generator = StoryGenerator()
            self.vote_handler = VoteHandler()
            self.background_task = None
            await ctx.send('Game has been reset')
        else:
            await ctx.send(ctx.author.name + ", You are not a mod")

    @commands.command()
    async def modVote(self, ctx: commands.Context):
        if (ctx.author.is_mod()):
            await ctx.send(
                await self.vote_handler.add_vote(
                    ctx.author.name, int(self._extract_message_text(ctx))
                )
            )
        else:
            await ctx.send(ctx.author.name + ", You are not a mod")

    async def _perform_action(self, user_action: str, ctx: commands.Context):
        """Continues the story by performing an action, communicating the result to the channel"""
        await ctx.send(
            await self.vote_handler.add_vote_option(ctx.author.name, user_action)
        )
        if self.background_task is None:
            self.background_task = asyncio.create_task(self.background_logic(ctx))

    # asyncio.create_task(something to run in the background without awaiting)
    # self.backgroundTask() = asyncio.create_task()
    # if self.backgroundTask() is not None:
    async def background_logic(self, ctx: commands.Context):
        await asyncio.sleep(10)

        chosen_action = max(self.vote_handler.proposals, key=lambda x: x.vote)
        action_index = self.vote_handler.proposals.index(chosen_action)
        narration_result = self.generator.generate_next_story_narration(
            chosen_action.message
        )
        message = f'Chose action {action_index + 1} ({chosen_action.vote} votes): {chosen_action.message} | {narration_result}'
        await self._send_chunked(ctx, message)
        self.vote_handler.reset()
        self.background_task = None

    async def _send_chunked(self, ctx: commands.Context, text: str):
        while text:
            suffix = '...' if len(text) >= self.max_message_len else ''
            await ctx.send(text[: self.max_message_len - 3] + suffix)
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



def main():
    bot = Bot()
    bot.run()

if __name__ == '__main__':
    main()
