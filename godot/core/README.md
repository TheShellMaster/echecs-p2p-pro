# Chess rules core

`ChessGame` is a local, dependency-free Godot 4 rules model. It does not own UI,
networking, clocks, or AI.

```gdscript
var game := ChessGame.new() # Starting position, or pass a FEN string.
var moves: Array = game.legal_moves() # Dictionaries: from/to indices, optional flags.
game.play_uci("e2e4")
var san: PackedStringArray = game.get_san_history()
game.undo()
game.redo()
var state: Dictionary = game.game_state()
```

Board indices are `a8 = 0` through `h1 = 63`; piece letters follow FEN, with
uppercase for White. The status strings are `active`, `check`, `checkmate`,
`stalemate`, `draw_insufficient_material`, `draw_seventy_five_move`, and
`draw_fivefold_repetition`. Fifty-move and threefold draws are claimable, so
they are listed in `game_state()["draw_claims"]` rather than ending the game.

The included smoke verifier can be run from the Godot project directory:

```sh
godot --headless --path . --script res://core/verify_chess_game.gd
```

The insufficient-material check detects king versus king, king plus one minor
piece versus king, and bishop-only positions where every bishop is on the same
square color. It deliberately avoids declaring other minor-piece positions a
draw without a proof that mate is impossible.
