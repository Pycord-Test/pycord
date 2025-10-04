import os
import random
from typing import Sequence, TypedDict

from dotenv import load_dotenv

import discord
from discord import components

load_dotenv()

# ==============================================================================
# CONSTANTS
# ==============================================================================

# Player identifiers
PLAYER_NONE = 0  # Empty cell
PLAYER_X = 1  # X player
PLAYER_O = 2  # O player

# Display symbols for each player
X_EMOJI = "❌"
O_EMOJI = "⭕"
EMPTY_CELL = "\u200b"  # Zero-width space for empty cells

PLAYER_SYMBOLS = {
    PLAYER_NONE: EMPTY_CELL,
    PLAYER_X: X_EMOJI,
    PLAYER_O: O_EMOJI,
}

# Custom ID format: tic_tac_toe:{row}:{col}
# Only stores button coordinates - all game state is in GAME_STATES dict
CUSTOM_ID_PREFIX = "tic_tac_toe"

# ==============================================================================
# TYPE DEFINITIONS
# ==============================================================================

Board = list[list[int]]  # 3x3 grid of player identifiers


class GameState(TypedDict):
    """Represents the complete state of a Tic Tac Toe game.

    NOTE: This is stored in memory and will be lost on bot restart.
    For production use, consider:
    - Redis with TTL (e.g., 1 hour per game)
    - Database with automatic cleanup of old games
    - Any persistent storage with expiration support
    """

    board: Board  # Current board state
    current_turn: int  # Which player's turn (1 or 2)
    player_x_id: int  # Discord user ID of player X
    player_o_id: int  # Discord user ID of player O
    game_over: bool  # Whether the game has ended
    winner: int | None  # Winner (1, 2, or None for tie)


# ==============================================================================
# GAME STATE STORAGE
# ==============================================================================

# WARNING: In-memory storage - data lost on bot restart!
# For production, use Redis with TTL, a database, or another persistent store
# with automatic expiration (e.g., Redis SETEX with 3600 seconds TTL)
GAME_STATES: dict[int, GameState] = {}  # Keyed by message ID


def create_initial_game_state(player_x_id: int, player_o_id: int) -> GameState:
    """Create a new game state with empty board and random first player.

    Args:
        player_x_id: Discord user ID for player X
        player_o_id: Discord user ID for player O

    Returns:
        A new GameState with empty board
    """
    # Randomly decide who goes first
    first_player = random.choice([PLAYER_X, PLAYER_O])

    return GameState(
        board=[[PLAYER_NONE for _ in range(3)] for _ in range(3)],
        current_turn=first_player,
        player_x_id=player_x_id,
        player_o_id=player_o_id,
        game_over=False,
        winner=None,
    )


def get_player_for_user(game_state: GameState, user_id: int) -> int | None:
    """Get which player (X or O) a user is controlling.

    Args:
        game_state: The current game state
        user_id: Discord user ID to check

    Returns:
        PLAYER_X, PLAYER_O, or None if user is not in this game
    """
    if user_id == game_state["player_x_id"]:
        return PLAYER_X
    elif user_id == game_state["player_o_id"]:
        return PLAYER_O
    return None


# ==============================================================================
# CUSTOM ID HELPERS
# ==============================================================================


def create_button_custom_id(row: int, col: int) -> str:
    """Create a custom ID for a Tic Tac Toe button.

    Only stores coordinates - game state is looked up via message ID.

    Args:
        row: Row position (0-2)
        col: Column position (0-2)
    """
    return f"{CUSTOM_ID_PREFIX}:{row}:{col}"


def parse_button_custom_id(custom_id: str) -> tuple[int, int]:
    """Parse a button's custom ID to extract coordinates.

    Returns:
        Tuple of (row, col)
    """
    parts = custom_id.split(":")
    return int(parts[1]), int(parts[2])


# ==============================================================================
# BUTTON CREATION
# ==============================================================================


def create_cell_button(cell_value: int, row: int, col: int, disabled: bool = False) -> components.Button:
    """Create a button representing a single Tic Tac Toe cell.

    Args:
        cell_value: The player occupying this cell (0 = empty, 1 = X, 2 = O)
        row: Row position in the grid (0-2)
        col: Column position in the grid (0-2)
        disabled: Whether the button should be disabled

    Returns:
        A Discord Button component
    """
    custom_id = create_button_custom_id(row, col)

    match cell_value:
        case 0:  # Empty cell - clickable
            return components.Button(
                style=discord.ButtonStyle.primary, label=EMPTY_CELL, custom_id=custom_id, disabled=disabled
            )
        case 1 | 2:  # Occupied cell - always disabled
            return components.Button(
                style=discord.ButtonStyle.primary, emoji=PLAYER_SYMBOLS[cell_value], custom_id=custom_id, disabled=True
            )
        case _:
            raise ValueError(f"Invalid cell value: {cell_value}")


# ==============================================================================
# BOARD STATE MANAGEMENT
# ==============================================================================


def check_winner(board: Board) -> int | None:
    """Check if there's a winner on the board.

    Checks all rows, columns, and diagonals for three in a row.

    Args:
        board: The current game board state

    Returns:
        The winning player (1 or 2), or None if no winner
    """
    # Check rows and columns
    for i in range(3):
        # Check row
        if board[i][0] == board[i][1] == board[i][2] != PLAYER_NONE:
            return board[i][0]
        # Check column
        if board[0][i] == board[1][i] == board[2][i] != PLAYER_NONE:
            return board[0][i]

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != PLAYER_NONE:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != PLAYER_NONE:
        return board[0][2]

    return None


def is_board_full(board: Board) -> bool:
    """Check if the board is completely filled (tie game).

    Args:
        board: The current game board state

    Returns:
        True if no empty cells remain, False otherwise
    """
    for row in board:
        for cell in row:
            if cell == PLAYER_NONE:
                return False
    return True


# ==============================================================================
# UI COMPONENT BUILDERS
# ==============================================================================


def create_game_buttons(board: Board, disable_all: bool = False) -> list[components.ActionRow]:
    """Create the 3x3 grid of buttons for the Tic Tac Toe game.

    Args:
        board: The current board state
        disable_all: Whether to disable all buttons (game over)

    Returns:
        List of ActionRow components, one per row of the game board
    """
    action_rows: list[components.ActionRow] = []

    for row_idx, row in enumerate(board):
        buttons = [
            create_cell_button(cell_value=cell_value, row=row_idx, col=col_idx, disabled=disable_all)
            for col_idx, cell_value in enumerate(row)
        ]
        action_rows.append(components.ActionRow(*buttons))

    return action_rows


def create_game_container(game_buttons: list[components.ActionRow], game_state: GameState) -> components.Container:
    """Create the container for an active game.

    Args:
        game_buttons: The 3x3 grid of game buttons
        game_state: The current game state

    Returns:
        A Container with the game title, turn indicator, and buttons
    """
    current_player_symbol = PLAYER_SYMBOLS[game_state["current_turn"]]

    # Mention the user whose turn it is
    if game_state["current_turn"] == PLAYER_X:
        current_user_id = game_state["player_x_id"]
    else:
        current_user_id = game_state["player_o_id"]

    return components.Container(
        components.TextDisplay("## Tic Tac Toe"),
        components.TextDisplay(f"It is {current_player_symbol}'s turn (<@{current_user_id}>)"),
        *game_buttons,
    )


def create_game_over_container(game_buttons: list[components.ActionRow], game_state: GameState) -> components.Container:
    """Create the container for a finished game.

    Args:
        game_buttons: The final state of the game buttons
        game_state: The final game state

    Returns:
        A Container with the game title, result message, and final board
    """
    if game_state["winner"] is None:
        result_message = "It's a tie! 🤝"
    else:
        winner_symbol = PLAYER_SYMBOLS[game_state["winner"]]
        if game_state["winner"] == PLAYER_X:
            winner_id = game_state["player_x_id"]
        else:
            winner_id = game_state["player_o_id"]
        result_message = f"Player {winner_symbol} (<@{winner_id}>) won! 🎉"

    return components.Container(
        components.TextDisplay("## Tic Tac Toe"),
        components.TextDisplay(result_message),
        *game_buttons,
    )


# ==============================================================================
# BOT SETUP
# ==============================================================================

bot = discord.Bot(intents=discord.Intents.all())

# ==============================================================================
# EVENT HANDLERS
# ==============================================================================


@bot.component_listener(lambda custom_id: custom_id.startswith(CUSTOM_ID_PREFIX))
async def handle_tic_tac_toe_move(interaction: discord.ComponentInteraction[components.PartialButton]):
    """Handle a player clicking a Tic Tac Toe cell.

    This function:
    1. Looks up the game state from the message ID
    2. Validates that it's the correct user's turn
    3. Parses which cell was clicked
    4. Updates the board with the new move
    5. Checks for a winner or tie
    6. Updates both the message and stored game state
    """
    assert interaction.custom_id is not None
    assert interaction.message is not None
    assert interaction.user is not None

    message_id = interaction.message.id

    # Retrieve game state from storage
    if message_id not in GAME_STATES:
        await interaction.respond(
            "❌ Game state not found! This game may have expired or the bot was restarted.", ephemeral=True
        )
        return

    game_state = GAME_STATES[message_id]

    # Validate the user is in this game
    user_player = get_player_for_user(game_state, interaction.user.id)
    if user_player is None:
        await interaction.respond("❌ You're not a player in this game!", ephemeral=True)
        return

    # Validate it's this user's turn
    if user_player != game_state["current_turn"]:
        await interaction.respond("❌ It's not your turn!", ephemeral=True)
        return

    # Parse the clicked cell coordinates
    row, col = parse_button_custom_id(interaction.custom_id)

    # Apply the move to the board
    game_state["board"][row][col] = game_state["current_turn"]

    # Check game end conditions
    winner = check_winner(game_state["board"])
    is_tie = is_board_full(game_state["board"])
    game_over = winner is not None or is_tie

    # Update game state
    if game_over:
        game_state["game_over"] = True
        game_state["winner"] = winner
    else:
        # Switch turns
        game_state["current_turn"] = PLAYER_O if game_state["current_turn"] == PLAYER_X else PLAYER_X

    # Create updated button grid
    updated_buttons = create_game_buttons(board=game_state["board"], disable_all=game_over)

    # Update the message with new game state
    if game_over:
        await interaction.edit(
            components=[create_game_over_container(updated_buttons, game_state)],
        )
        del GAME_STATES[message_id]  # The message can't be interacted with anymore because all buttons are disabled
    else:
        await interaction.edit(
            components=[create_game_container(updated_buttons, game_state)],
        )


# ==============================================================================
# SLASH COMMANDS
# ==============================================================================


@bot.slash_command()
async def tic_tac_toe(ctx: discord.ApplicationContext, opponent: discord.User):
    """Start a new Tic Tac Toe game against another user.

    Args:
        opponent: The user you want to play against
    """
    # Validate opponent is not the same user
    if opponent.id == ctx.user.id:
        await ctx.respond("❌ You can't play against yourself!", ephemeral=True)
        return

    # Validate opponent is not a bot
    if opponent.bot:
        await ctx.respond("❌ You can't play against a bot!", ephemeral=True)
        return

    # Randomly assign X and O to the two players
    players = [ctx.user.id, opponent.id]
    random.shuffle(players)
    player_x_id, player_o_id = players

    # Create initial game state
    game_state = create_initial_game_state(player_x_id, player_o_id)

    # Create initial UI
    initial_buttons = create_game_buttons(board=game_state["board"])

    # Send the game message
    message = await ctx.respond(
        components=[create_game_container(initial_buttons, game_state)],
    )

    # Get the message object to store the game state
    # Note: ctx.respond() returns an Interaction, we need to get the actual message
    actual_message = await message.original_response()

    # Store the game state keyed by message ID
    # In production: Use Redis with SETEX for automatic expiration
    # Example: redis.setex(f"game:{actual_message.id}", 3600, json.dumps(game_state))
    GAME_STATES[actual_message.id] = game_state

    # Announce who goes first
    first_player_symbol = PLAYER_SYMBOLS[game_state["current_turn"]]
    if game_state["current_turn"] == PLAYER_X:
        first_player_id = player_x_id
    else:
        first_player_id = player_o_id

    await ctx.send(
        f"🎮 Game started! {first_player_symbol} (<@{first_player_id}>) goes first!",
    )


# ==============================================================================
# BOT STARTUP
# ==============================================================================


# Optional: Add a cleanup task for old games if not using Redis TTL
@bot.event
async def on_ready():
    print(f"Bot ready! Logged in as {bot.user}")


bot.run(os.getenv("TOKEN_2"))
