# Twitch Plays Llm

*A collaborative twitch-based choose-your-own-adventure game*

Twitch Plays Llm a text-based choose-your-own-adventure game (ie. AI dungeon) set within a specific theme. For the time travel theme, the main character is a timem traveler vising a historic time period with the goal of altering some historic event. The game is played collaboratively through twitch chat. Read more about the vision for this project within [this document](https://docs.google.com/document/d/10TJ-P2iRqNIOWyQ5PRzcVnN7VBCprzPSB9CFGy_-eDo/edit).

## Development Setup

This project is a standard Python package and can be installed via `pip`. View below for more specific instructions.

### Windows

1. Set up a virtual environment:
   ```powershell
   python -m venv .venv  # Setup a virtual environment
   .venv\Scripts\activate  # Activate virtual environment
   ```

2. Install the package in editable mode with development dependencies:
   ```powershell
   pip install -e ".[dev]"  # Install the local folder as a Python package
   ```

3. Setup the environment: Copy the `.env.example` file to `.env` and fill out the fields (feel free to ask someone for test credentials).

4. Run the executable:
   ```powershell
   # Make sure to run beforehand: .venv\Scripts\activate
   twitch-plays-llm run # run the executable
   twitch-plays-llm -h  # View the available commands
   ```

### Linux / Mac

1. Set up a virtual environment:
   ```bash
   python3 -m venv .venv  # Setup a virtual environment
   source .venv/bin/activate  # Activate virtual environment
   ```

2. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e '.[dev]'  # Install the local folder as a Python package
   ```

3. Setup the environment: Copy the `.env.example` file to `.env` and fill out the fields (feel free to ask someone for test credentials).

4. Run the executable:
   ```bash
   # Make sure to run beforehand: source .venv/bin/activate
   twitch-plays-llm run # run the executable
   twitch-plays-llm -h  # View the available commands
   ```

### Formatting and linting

To run formatting, run the following:
```bash
# Make sure to activate the virtual environment before running this to access the executables
isort . --profile attrs; blue . --line-length 88
```
