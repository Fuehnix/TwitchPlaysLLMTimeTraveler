# Twitch Plays Llm

*A collaborative twitch-based choose-your-own-adventure game*

Twitch Plays Llm a text-based choose-your-own-adventure game (ie. AI dungeon) set within a specific theme. For the time travel theme, the main character is a timem traveler vising a historic time period with the goal of altering some historic event. The game is played collaboratively through twitch chat. Read more about the vision for this project within [this document](https://docs.google.com/document/d/10TJ-P2iRqNIOWyQ5PRzcVnN7VBCprzPSB9CFGy_-eDo/edit).

## Development Setup

This project is a standard Python package and can be installed like this:

```bash
python3 -m venv .venv/  # Setup a virtual environment
source .venv/bin/activate  # Activate virtual environment
pip install -e .  # Install the local folder as a Python package
```

Run the executable:
```bash
# Make sure to run before hand: .venv/bin/activate
twitch-plays-llm -h  # View the available commands
```

