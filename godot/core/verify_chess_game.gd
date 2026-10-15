extends SceneTree

const Game = preload("res://core/chess_game.gd")
var failures := 0


func _initialize() -> void:
	var game = Game.new()
	_check(game.legal_moves().size() == 20, "initial legal move count")
	_check(game.play_uci("e2e4") and game.play_uci("e7e5") and game.play_uci("g1f3"), "UCI moves")
	_check(
		game.to_fen().begins_with("rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"),
		"FEN after opening moves"
	)
	_check(game.get_san_history() == PackedStringArray(["e4", "e5", "Nf3"]), "SAN move history")
	_check(
		(
			game.undo()
			and game.get_san_history().size() == 2
			and game.redo()
			and game.get_san_history().size() == 3
		),
		"undo and redo history"
	)

	game.load_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
	_check(_has_move(game, "e1g1") and _has_move(game, "e1c1"), "both castling moves")
	_check(
		game.play_uci("e1g1") and game.board[61] == "R" and game.board[63] == "",
		"kingside castling"
	)
	_check(game.get_san_history() == PackedStringArray(["O-O"]), "castling SAN")

	game.load_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
	_check(_has_move(game, "e5d6") and game.play_uci("e5d6"), "en passant move")
	_check(game.board[27] == "" and game.board[19] == "P", "en passant capture")
	_check(game.get_san_history() == PackedStringArray(["exd6"]), "en passant SAN")

	game.load_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
	_check(_has_move(game, "a7a8q") and _has_move(game, "a7a8n"), "promotion choices")
	_check(game.play_uci("a7a8n") and game.board[0] == "N", "underpromotion")
	_check(game.get_san_history() == PackedStringArray(["a8=N"]), "promotion SAN")

	game.load_fen(Game.START_FEN)
	for uci in ["f2f3", "e7e5", "g2g4", "d8h4"]:
		_check(game.play_uci(uci), "Fool's mate move " + uci)
	_check(game.game_status() == "checkmate", "checkmate detection")
	_check(game.get_san_history().back() == "Qh4#", "checkmate SAN")
	game.load_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
	_check(game.game_status() == "stalemate", "stalemate detection")
	_check(game.draw_claims().is_empty(), "no draw claim after stalemate")

	game.load_fen("4k3/8/8/8/8/8/8/4K1B1 w - - 0 1")
	_check(game.game_status() == "draw_insufficient_material", "insufficient material")

	game.load_fen("4k3/8/8/8/8/8/8/R3K3 w - - 99 1")
	_check(game.play_uci("a1a2") and "fifty_move_rule" in game.draw_claims(), "50-move draw claim")
	game.load_fen("4k3/8/8/8/8/8/8/R3K3 w - - 149 1")
	_check(
		game.play_uci("a1a2") and game.game_status() == "draw_seventy_five_move",
		"automatic 75-move draw"
	)
	_check(not game.play_uci("a2a3"), "automatic draw ends play")

	game.load_fen(Game.START_FEN)
	var cycle := ["g1f3", "g8f6", "f3g1", "f6g8"]
	for _i in 2:
		for uci in cycle:
			_check(game.play_uci(uci), "threefold repetition move " + uci)
	_check("threefold_repetition" in game.draw_claims(), "threefold repetition claim")
	for _i in 2:
		for uci in cycle:
			_check(game.play_uci(uci), "fivefold repetition move " + uci)
	_check(game.game_status() == "draw_fivefold_repetition", "automatic fivefold repetition")

	if failures == 0:
		print("ChessGame verification passed")
		quit(0)
	else:
		push_error("ChessGame verification: %d failure(s)" % failures)
		quit(1)


func _has_move(game, uci: String) -> bool:
	for move in game.legal_moves():
		if game.move_to_uci(move) == uci:
			return true
	return false


func _check(condition: bool, label: String) -> void:
	if not condition:
		failures += 1
		push_error("Failed: " + label)
