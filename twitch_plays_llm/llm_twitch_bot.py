import asyncio

from typing import Optional

from twitchio.channel import Channel
from twitchio.ext import commands

from .config import config
from .llm_game import LlmGame, LlmGameHooks
from .models import Proposal


"""
point system task list:
channel.chatters() returns a list of chatters in the channel
-   regularly increment points for chatters (method)
-   move points from being a variable to a persistant database somewhere
"""


class LlmTwitchBot(commands.Bot, LlmGameHooks):
    max_message_len = 500  # Twitch has a 500 character limit

    def __init__(self, llm_game: LlmGame):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        super().__init__(
            token=config.twitch_bot_client_id,
            prefix='!',
            initial_channels=[config.twitch_channel_name],
        )
        self.game = llm_game
        self.channel: Optional[Channel] = None
        self.viewer_points = {}

    async def event_ready(self):
        """Function that runs when bot connects to server"""
        asyncio.get_running_loop().set_debug(True)
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        self.channel = self.get_channel(config.twitch_channel_name)
        await self._send_chunked(f'Story: {self.game.initial_story_message}')

    @commands.command()
    async def action(self, ctx: commands.Context):
        """Trigger for user to perform an action within the game"""
        story_action = self._extract_message_text(ctx)
        user = ctx.author.name
        if user not in self.viewer_points:
            self.viewer_points[user] = 500
        if self.viewer_points[user] > config.action_cost: #first action is free, or if they have enough points
            self.viewer_points[user] -= config.action_cost
            await self._propose_story_action(story_action, user)
        else:
            await self._send(f'{user} does not have enough points to perform an action. Try voting for someone else!')


    @commands.command()
    async def points(self, ctx: commands.Context):
        """Add command to check points (command)"""
        user_id = ctx.author.name
        if user_id in self.viewer_points:
            await self._send(f'{user_id} has {self.viewer_points[user_id]} points')
        else:
            await self._send(f'{user_id} has 0 points')
        

    @commands.command()
    async def say(self, ctx: commands.Context):
        """Trigger for user to say something within the game"""
        story_action = 'You say "' + self._extract_message_text(ctx) + '"'
        await self._propose_story_action(story_action, ctx.author.name)

    @commands.command()
    async def vote(self, ctx):
        await self._vote(ctx)

    @commands.command()
    async def leaderboard(self, ctx: commands.Context):
        leaderboard = [(user, points) for user, points in self.viewer_points.items()]
        leaderboard.sort(key=lambda x: x[1], reverse=True)  # Sort the leaderboard by points in descending order
        top_5 = leaderboard[:5]  # Get the top 5 users

        leaderboard_text = "Top 5 Users:\n"
        for i, (user, points) in enumerate(top_5, start=1):
            leaderboard_text += f" {i}. {user}: {points} | \n"

        await ctx.send(leaderboard_text)

    @commands.command()
    async def help(self, ctx: commands.Context):
        """Help command"""
        await self._send(
            """
            Commands:
            !action <action> - Perform an action within the game
            !say <message> - Say something within the game
            !vote <user> - Vote for a user to perform an action
            !leaderboard - Show the leaderboard
            !points - Check your points
            !help - Show this message"""
        )
    
    # --- MOD COMMANDS ---

    @commands.command()
    async def reset(self, ctx: commands.Context):
        """Resets the game if the user is a mod"""
        if not ctx.author.is_mod:
            await self._send(ctx.author.name + ', You are not a mod')
            return

        self.game.restart()
        await self._send_chunked(f'Game has been reset | {self.game.initial_story_message}')

    @commands.command()
    async def modvote(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            await self._send(ctx.author.name + ', You are not a mod')
            return
        await self._vote(ctx, weight=99)

    @commands.command()
    async def endvote(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            await self._send(ctx.author.name + ', You are not a mod')
            return
        self.game.end_vote()

    @commands.command()
    async def givepoints(self, ctx: commands.Context):
        """Give points to a user"""
        #!givepoints <user> <points>
        if not ctx.author.is_mod:
            await self._send(ctx.author.name + ', You are not a mod')
            return
        else:
            try:
                #debug later
                message_split = ctx.message.content.split()
                user = ''.join(filter(str.isalnum, message_split[1]))  # Remove non-alphanumeric characters
                points = message_split[2]
                self.viewer_points[user] += int(points)
                await self._send(f'{user} was given {points} points ')
            except KeyError:
                await self._send(f'{user} does not exist')
            except TypeError:
                await self._send(f'Invalid input')

    # --- Other Methods ---

    async def _vote(self, ctx: commands.Context, weight: int = 1):
        """Trigger for user to vote on the next action"""
        vote_option_str = self._extract_message_text(ctx)
        user = ctx.author.name
        try:
            proposal = self.game.vote(int(vote_option_str))
            new_count = proposal.vote
            proposer = proposal.user
            if user != proposer:
                if user in self.viewer_points:
                    self.viewer_points[user] += config.vote_points
                else:
                    self.viewer_points[user] = config.vote_points
            if proposer in self.viewer_points:
                self.viewer_points[proposer] += config.points_earned_per_vote
            else:
                self.viewer_points[proposer] = config.points_earned_per_vote
        except ValueError:
            await self._send(f'Invalid vote option: {vote_option_str}')
        else:
            await self._send(f'Vote added for option {vote_option_str}. Current votes: {new_count}')

    async def on_get_narration_result(
        self, narration_result: str, proposal: Proposal, proposal_id: int
    ):
        if proposal.user in self.viewer_points:
            self.viewer_points[proposal.user] += config.vote_points
        else:
            self.viewer_points[proposal.user] = config.vote_points
        await self._send_chunked(
            f'Chose action {proposal_id} ({proposal.vote} votes): {proposal.message} | {narration_result}'
        )
        for user, points in self.viewer_points.items():
            self.viewer_points[user] += config.vote_accumulation

    async def _propose_story_action(self, story_action: str, author: str):
        """Continues the story by performing an action, communicating the result to the channel"""
        proposal_id = await self.game.add_proposal(story_action, author)
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
