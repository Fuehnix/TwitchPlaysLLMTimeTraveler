from twitchio.ext import commands
import openai
import json
import asyncio
from pydantic import BaseModel


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


class StoryGenerator:
    def __init__(self) -> None:
        # TODO: Dynamically generate initial prompt
        self.past_story_entries = [
            StoryEntry(
                user_action="",
                narration_result="You are a middle aged man in downtown Chicago, 1910. You're in a steak restaurant talking to the waiter as you just sat down."
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
            {"role": "system", "content": "You are a storyteller that generates the next event in a story based on the action a user says. The story takes place in 1910 and the main character is a middle aged man. At each turn, the user says an action and you reply with a short continuation of the story outlining the events that happen in the story based on the action the user performed."},
        ]
        for story_entry in self.past_story_entries:
            if story_entry.user_action:
                messages += [{"role": "user", "content": story_entry.user_action}]
            if story_entry.narration_result:
                messages += [{"role": "assistant", "content": story_entry.narration_result}]
        messages.append(
            {"role": "user", "content": user_action}
        )
        return messages

    def generate_next_story_narration(self, user_action: str):
        """Generates the continuation of the story given a user action"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.construct_prompt_messages(user_action)
        )
        next_narration = response['choices'][0]['message']['content']
        self.past_story_entries.append(
            StoryEntry(user_action=user_action, narration_result=next_narration)
        )
        return next_narration


class Bot(commands.Bot):
    max_message_len = 500  # Twitch has a 500 character limit

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        super().__init__(token=client_id, prefix='!', initial_channels=[channel_name])
        self.generator = StoryGenerator()

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
        user_action = "You say \"" + self._extract_message_text(ctx) + "\""
        await self._perform_action(user_action, ctx)

    async def _perform_action(self, user_action: str, ctx: commands.Context):
        """Continues the story by performing an action, communicating the result to the channel"""
        await ctx.send('Generating continuation of story...')
        narration_result = self.generator.generate_next_story_narration(user_action)
        while narration_result:
            suffix = '...' if len(narration_result) >= self.max_message_len else ''
            await ctx.send(narration_result[:self.max_message_len - 3] + suffix)
            await asyncio.sleep(2)
            narration_result = narration_result[self.max_message_len - 3:]

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
