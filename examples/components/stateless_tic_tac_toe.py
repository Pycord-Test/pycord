import os
from typing import Sequence

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

# Custom ID format: tic_tac_toe:{current_player}:{row}:{col}:{next_player}
# - current_player: who occupies this cell (0 = empty, 1 = X, 2 = O)
# - row, col: grid position (0-2)
# - next_player: whose turn it is next (1 or 2)
CUSTOM_ID_PREFIX = "tic_tac_toe"

# ==============================================================================
# TYPE DEFINITIONS
# ==============================================================================

Board = list[list[int]]  # 3x3 grid of player identifiers

# ==============================================================================
# CUSTOM ID HELPERS
# ==============================================================================


def create_button_custom_id(current_player: int, row: int, col: int, next_player: int) -> str:
    """Create a custom ID for a Tic Tac Toe button.

    Args:
        current_player: The player occupying this cell (0 = empty)
        row: Row position (0-2)
        col: Column position (0-2)
        next_player: The player whose turn is next (1 or 2)
    """
    return f"{CUSTOM_ID_PREFIX}:{current_player}:{row}:{col}:{next_player}"


def parse_button_custom_id(custom_id: str) -> tuple[int, int, int, int]:
    """Parse a button's custom ID to extract game state.

    Returns:
        Tuple of (current_player, row, col, next_player)
    """
    parts = custom_id.split(":")
    return (
        int(parts[1]),  # current_player
        int(parts[2]),  # row
        int(parts[3]),  # col
        int(parts[4]),  # next_player
    )


# ==============================================================================
# BUTTON CREATION
# ==============================================================================


def create_cell_button(
    current_player: int, row: int, col: int, next_player: int, disabled: bool = False
) -> components.Button:
    """Create a button representing a single Tic Tac Toe cell.

    Args:
        current_player: The player occupying this cell (0 = empty)
        row: Row position in the grid (0-2)
        col: Column position in the grid (0-2)
        next_player: The player whose turn is next
        disabled: Whether the button should be disabled

    Returns:
        A Discord Button component
    """
    custom_id = create_button_custom_id(current_player, row, col, next_player)

    match current_player:
        case 0:  # Empty cell - clickable
            return components.Button(
                style=discord.ButtonStyle.primary, label=EMPTY_CELL, custom_id=custom_id, disabled=disabled
            )
        case 1 | 2:  # Occupied cell - always disabled
            return components.Button(
                style=discord.ButtonStyle.secondary,
                emoji=PLAYER_SYMBOLS[current_player],
                custom_id=custom_id,
                disabled=True,
            )
        case _:
            raise ValueError(f"Invalid player identifier: {current_player}")


# ==============================================================================
# BOARD STATE MANAGEMENT
# ==============================================================================


def extract_board_from_components(action_rows: Sequence[components.ActionRow]) -> Board:
    """Extract the current board state from Discord action rows.

    The board state is encoded in the custom_id of each button. This function
    reconstructs the 3x3 game board from the button components.

    Args:
        action_rows: The ActionRow components containing the game buttons

    Returns:
        A 3x3 board represented as a list of lists
    """
    board: list[list[int]] = []

    for action_row in action_rows:
        row: list[int] = []
        for button in action_row.components:
            # Extract the current player value from the button's custom_id
            current_player, _, _, _ = parse_button_custom_id(button.custom_id)  # pyright: ignore [reportOptionalMemberAccess]
            row.append(current_player)
        board.append(row)

    return board


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


def create_game_buttons(
    board: Board | None = None, next_player: int = PLAYER_X, disable_all: bool = False
) -> list[components.ActionRow]:
    """Create the 3x3 grid of buttons for the Tic Tac Toe game.

    Args:
        board: The current board state (None for a new game)
        next_player: The player whose turn is next
        disable_all: Whether to disable all buttons (game over)

    Returns:
        List of ActionRow components, one per row of the game board
    """
    if board is None:
        # Initialize empty 3x3 board
        board = [[PLAYER_NONE for _ in range(3)] for _ in range(3)]

    action_rows: list[components.ActionRow] = []

    for row_idx, row in enumerate(board):
        buttons = [
            create_cell_button(
                current_player=cell_value, row=row_idx, col=col_idx, next_player=next_player, disabled=disable_all
            )
            for col_idx, cell_value in enumerate(row)
        ]
        action_rows.append(components.ActionRow(*buttons))

    return action_rows


def create_game_container(game_buttons: list[components.ActionRow], next_player: int) -> components.Container:
    """Create the container for an active game.

    Args:
        game_buttons: The 3x3 grid of game buttons
        next_player: The player whose turn it is

    Returns:
        A Container with the game title, turn indicator, and buttons
    """
    return components.Container(
        components.TextDisplay("## Tic Tac Toe"),
        components.TextDisplay(f"**It is {PLAYER_SYMBOLS[next_player]}'s turn**"),
        *game_buttons,
    )


def create_game_over_container(game_buttons: list[components.ActionRow], winner: int) -> components.Container:
    """Create the container for a finished game.

    Args:
        game_buttons: The final state of the game buttons
        winner: The winning player (0 for tie, 1 or 2 for winners)

    Returns:
        A Container with the game title, result message, and final board
    """
    if winner == PLAYER_NONE:
        result_message = "**It's a tie!**"
    else:
        result_message = f"**Player {PLAYER_SYMBOLS[winner]} won!**"

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
    1. Extracts the current board state from the message components
    2. Parses which cell was clicked and which player clicked it
    3. Updates the board with the new move
    4. Checks for a winner or tie
    5. Updates the message with the new game state
    """
    assert interaction.custom_id is not None
    assert interaction.message is not None

    # Extract board state from the existing message
    # Components structure: [Container -> TextDisplay, TextDisplay, ActionRow, ActionRow, ActionRow]
    game_action_rows = interaction.message.components[0].components[2:5]
    board = extract_board_from_components(game_action_rows)

    # Parse the clicked button's custom_id to get move details
    _, row, col, current_player = parse_button_custom_id(interaction.custom_id)

    # Determine next player (alternate between X and O)
    next_player = PLAYER_O if current_player == PLAYER_X else PLAYER_X

    # Apply the move to the board
    board[row][col] = current_player

    # Check game end conditions
    winner = check_winner(board)
    is_tie = is_board_full(board)
    game_over = winner is not None or is_tie

    # Create updated button grid
    updated_buttons = create_game_buttons(board=board, next_player=next_player, disable_all=game_over)

    # Update the message with new game state
    if game_over:
        final_winner = winner if winner is not None else PLAYER_NONE
        await interaction.edit(
            components=[create_game_over_container(updated_buttons, final_winner)],
        )
    else:
        await interaction.edit(
            components=[create_game_container(updated_buttons, next_player)],
        )


# ==============================================================================
# SLASH COMMANDS
# ==============================================================================


@bot.slash_command()
async def tic_tac_toe(ctx: discord.ApplicationContext):
    """Start a new Tic Tac Toe game."""
    initial_buttons = create_game_buttons(next_player=PLAYER_X)
    await ctx.respond(
        components=[create_game_container(initial_buttons, next_player=PLAYER_X)],
    )


# ==============================================================================
# BOT STARTUP
# ==============================================================================


@bot.event
async def on_ready():
    print(f"Bot ready! Logged in as {bot.user}")


bot.run(os.getenv("TOKEN"))
