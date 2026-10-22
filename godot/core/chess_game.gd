class_name ChessGame
extends RefCounted
## Offline chess rules. Board indices are rank 8 to rank 1, file a to h.
## Pieces use FEN letters (uppercase = White, lowercase = Black, "" = empty).

const START_FEN := "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
const FILES := "abcdefgh"
const PROMOTIONS := ["q", "r", "b", "n"]

var board: Array[String] = []
var white_to_move := true
var castling_rights := "KQkq"
var en_passant_square := -1
var halfmove_clock := 0
var fullmove_number := 1
var _move_records: Array[Dictionary] = []
var _undo_stack: Array[Dictionary] = []
var _redo_stack: Array[String] = []
var _position_keys: Array[String] = []


func _init(fen: String = START_FEN) -> void:
	if not load_fen(fen):
		load_fen(START_FEN)


func new_game() -> void:
	load_fen(START_FEN)


func load_fen(fen: String) -> bool:
	var fields := fen.strip_edges().split(" ", false)
	if fields.size() != 6:
		return false
	var ranks := fields[0].split("/", false)
	if ranks.size() != 8 or (fields[1] != "w" and fields[1] != "b"):
		return false
	var parsed: Array[String] = []
	for rank in ranks:
		var file_count := 0
		for symbol in rank:
			if symbol.is_valid_int():
				var empty_count := int(symbol)
				if empty_count < 1 or empty_count > 8:
					return false
				for _i in empty_count:
					parsed.append("")
				file_count += empty_count
			elif "pnbrqkPNBRQK".contains(symbol):
				parsed.append(symbol)
				file_count += 1
			else:
				return false
		if file_count != 8:
			return false
	if (
		fields[2] != "-"
		and (
			fields[2].contains("K") and fields[2].count("K") > 1
			or fields[2].contains("Q") and fields[2].count("Q") > 1
			or fields[2].contains("k") and fields[2].count("k") > 1
			or fields[2].contains("q") and fields[2].count("q") > 1
		)
	):
		return false
	var ep := -1 if fields[3] == "-" else square_from_name(fields[3])
	if fields[3] != "-" and ep < 0:
		return false
	if (
		not fields[4].is_valid_int()
		or not fields[5].is_valid_int()
		or int(fields[4]) < 0
		or int(fields[5]) < 1
	):
		return false
	board = parsed
	white_to_move = fields[1] == "w"
	castling_rights = "" if fields[2] == "-" else fields[2]
	en_passant_square = ep
	halfmove_clock = int(fields[4])
	fullmove_number = int(fields[5])
	_move_records.clear()
	_undo_stack.clear()
	_redo_stack.clear()
	_position_keys.clear()
	_position_keys.append(_position_key())
	return true


func to_fen() -> String:
	var rank_text: Array[String] = []
	for rank in 8:
		var text := ""
		var empty_count := 0
		for file in 8:
			var piece: String = board[rank * 8 + file]
			if piece == "":
				empty_count += 1
			else:
				if empty_count > 0:
					text += str(empty_count)
					empty_count = 0
				text += piece
		if empty_count > 0:
			text += str(empty_count)
		rank_text.append(text)
	var ep_text := "-" if en_passant_square < 0 else square_name(en_passant_square)
	return (
		"%s %s %s %s %d %d"
		% [
			"/".join(rank_text),
			"w" if white_to_move else "b",
			"-" if castling_rights.is_empty() else castling_rights,
			ep_text,
			halfmove_clock,
			fullmove_number
		]
	)


func square_name(square: int) -> String:
	if square < 0 or square >= 64:
		return ""
	return FILES.substr(square % 8, 1) + str(8 - int(square / 8))


func square_from_name(name: String) -> int:
	if name.length() != 2:
		return -1
	var file := FILES.find(name.substr(0, 1))
	var rank := name.substr(1, 1)
	if file < 0 or not rank.is_valid_int() or int(rank) < 1 or int(rank) > 8:
		return -1
	return (8 - int(rank)) * 8 + file


func legal_moves(from_square: int = -1) -> Array:
	var legal: Array = []
	for move in _pseudo_moves():
		if from_square >= 0 and move.from != from_square:
			continue
		var before := _snapshot()
		_apply(move)
		var king_square := _king_square(not white_to_move)
		var safe := king_square >= 0 and not _is_attacked(king_square, white_to_move)
		_restore(before)
		if safe:
			legal.append(move)
	return legal


func play_uci(uci: String) -> bool:
	if (
		game_status()
		in [
			"checkmate",
			"stalemate",
			"draw_seventy_five_move",
			"draw_fivefold_repetition",
			"draw_insufficient_material"
		]
	):
		return false
	var normalized := uci.strip_edges().to_lower()
	if normalized.length() != 4 and normalized.length() != 5:
		return false
	var from_square := square_from_name(normalized.substr(0, 2))
	var to_square := square_from_name(normalized.substr(2, 2))
	if from_square < 0 or to_square < 0:
		return false
	for move in legal_moves(from_square):
		var move_promotion: String = move.get("promotion", "")
		if (
			move.to == to_square
			and move_promotion == (normalized.substr(4, 1) if normalized.length() == 5 else "")
		):
			var before := _snapshot()
			var san := _san_for_move(move)
			_apply(move)
			if legal_moves().is_empty() and is_in_check(white_to_move):
				san += "#"
			elif is_in_check(white_to_move):
				san += "+"
			_undo_stack.append({"before": before, "uci": normalized, "san": san})
			_move_records.append({"uci": normalized, "san": san})
			_redo_stack.clear()
			_position_keys.append(_position_key())
			return true
	return false


func undo() -> bool:
	if _undo_stack.is_empty():
		return false
	var record: Dictionary = _undo_stack.pop_back()
	_restore(record.before)
	_move_records.pop_back()
	_position_keys.pop_back()
	_redo_stack.append(record.uci)
	return true


func redo() -> bool:
	if _redo_stack.is_empty():
		return false
	var pending := _redo_stack.duplicate()
	var uci: String = pending.pop_back()
	_redo_stack = pending
	if not play_uci(uci):
		pending.append(uci)
		_redo_stack = pending
		return false
	_redo_stack = pending
	return true


func get_san_history() -> PackedStringArray:
	var result := PackedStringArray()
	for record in _move_records:
		result.append(record.san)
	return result


func get_uci_history() -> PackedStringArray:
	var result := PackedStringArray()
	for record in _move_records:
		result.append(record.uci)
	return result


func move_to_uci(move: Dictionary) -> String:
	return square_name(move.from) + square_name(move.to) + str(move.get("promotion", ""))


func is_attacked(square: int, by_white: bool) -> bool:
	return _is_attacked(square, by_white)


func is_in_check(white: bool = white_to_move) -> bool:
	var king_square := _king_square(white)
	return king_square >= 0 and _is_attacked(king_square, not white)


func game_status() -> String:
	var moves := legal_moves()
	if moves.is_empty():
		if is_in_check(white_to_move):
			return "checkmate"  # Side to move has lost.
		return "stalemate"
	if halfmove_clock >= 150:
		return "draw_seventy_five_move"
	if _current_repetition_count() >= 5:
		return "draw_fivefold_repetition"
	if is_insufficient_material():
		return "draw_insufficient_material"
	return "check" if is_in_check(white_to_move) else "active"


func draw_claims() -> Array[String]:
	var claims: Array[String] = []
	if (
		legal_moves().is_empty()
		or halfmove_clock >= 150
		or _current_repetition_count() >= 5
		or is_insufficient_material()
	):
		return claims
	if halfmove_clock >= 100:
		claims.append("fifty_move_rule")
	if _current_repetition_count() >= 3:
		claims.append("threefold_repetition")
	return claims


func game_state() -> Dictionary:
	var status := game_status()
	return {
		"status": status,
		"side_to_move": "white" if white_to_move else "black",
		"in_check": is_in_check(white_to_move),
		"legal_move_count": legal_moves().size(),
		"draw_claims": draw_claims(),
		"fen": to_fen(),
	}


func is_insufficient_material() -> bool:
	var pieces: Array[String] = []
	for piece in board:
		if piece != "" and piece.to_lower() != "k":
			pieces.append(piece)
	if pieces.is_empty():
		return true
	if pieces.size() == 1 and pieces[0].to_lower() in ["b", "n"]:
		return true
	var bishops_only := true
	var bishop_square_color := -1
	for square in 64:
		var piece: String = board[square]
		if piece == "":
			continue
		var kind := piece.to_lower()
		if kind == "k":
			continue
		if kind != "b":
			bishops_only = false
			break
		var color := (int(square / 8) + square % 8) % 2
		if bishop_square_color == -1:
			bishop_square_color = color
		elif bishop_square_color != color:
			return false
	return bishops_only


func _pseudo_moves() -> Array:
	var result: Array = []
	for source in 64:
		var piece: String = board[source]
		if piece == "" or _is_white(piece) != white_to_move:
			continue
		var kind := piece.to_lower()
		var row := int(source / 8)
		var file := source % 8
		if kind == "p":
			var direction := -1 if white_to_move else 1
			var start_row := 6 if white_to_move else 1
			var next_row := row + direction
			if _inside(next_row, file) and board[next_row * 8 + file] == "":
				_add_pawn_move(result, source, next_row * 8 + file)
				var twice_row := row + 2 * direction
				if row == start_row and board[twice_row * 8 + file] == "":
					result.append({"from": source, "to": twice_row * 8 + file})
			for delta_file in [-1, 1]:
				var target_file = file + delta_file
				if not _inside(next_row, target_file):
					continue
				var target = next_row * 8 + target_file
				if (
					board[target] != ""
					and board[target].to_lower() != "k"
					and _is_white(board[target]) != white_to_move
				):
					_add_pawn_move(result, source, target)
				elif target == en_passant_square:
					result.append({"from": source, "to": target, "en_passant": true})
		elif kind == "n":
			for offset in [
				Vector2i(2, 1),
				Vector2i(2, -1),
				Vector2i(-2, 1),
				Vector2i(-2, -1),
				Vector2i(1, 2),
				Vector2i(1, -2),
				Vector2i(-1, 2),
				Vector2i(-1, -2)
			]:
				_add_step(result, source, row + offset.x, file + offset.y)
		elif kind == "k":
			for dr in [-1, 0, 1]:
				for df in [-1, 0, 1]:
					if dr != 0 or df != 0:
						_add_step(result, source, row + dr, file + df)
			_add_castles(result, source)
		else:
			var directions: Array = []
			if kind == "b" or kind == "q":
				directions.append_array(
					[Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1)]
				)
			if kind == "r" or kind == "q":
				directions.append_array(
					[Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
				)
			for direction in directions:
				var target_row = row + direction.x
				var target_file = file + direction.y
				while _inside(target_row, target_file):
					var target = target_row * 8 + target_file
					if board[target] == "":
						result.append({"from": source, "to": target})
					else:
						if (
							board[target].to_lower() != "k"
							and _is_white(board[target]) != white_to_move
						):
							result.append({"from": source, "to": target})
						break
					target_row += direction.x
					target_file += direction.y
	return result


func _san_for_move(move: Dictionary) -> String:
	if move.get("castle", false):
		return "O-O" if move.to % 8 == 6 else "O-O-O"
	var source: int = move.from
	var target: int = move.to
	var piece: String = board[source]
	var kind := piece.to_lower()
	var is_capture = board[target] != "" or move.get("en_passant", false)
	var san := ""
	if kind == "p":
		if is_capture:
			san += FILES.substr(source % 8, 1)
	else:
		san += kind.to_upper()
		var ambiguous: Array[int] = []
		for alternative in legal_moves():
			if alternative.from == source or alternative.to != target:
				continue
			if board[alternative.from].to_lower() == kind:
				ambiguous.append(alternative.from)
		if not ambiguous.is_empty():
			var same_file := false
			var same_rank := false
			for square in ambiguous:
				same_file = same_file or square % 8 == source % 8
				same_rank = same_rank or int(square / 8) == int(source / 8)
			if not same_file:
				san += FILES.substr(source % 8, 1)
			elif not same_rank:
				san += str(8 - int(source / 8))
			else:
				san += FILES.substr(source % 8, 1) + str(8 - int(source / 8))
	if is_capture:
		san += "x"
	san += square_name(target)
	var promotion: String = move.get("promotion", "")
	if not promotion.is_empty():
		san += "=" + promotion.to_upper()
	return san


func _position_key() -> String:
	var fields := to_fen().split(" ")
	var en_passant := "-"
	if en_passant_square >= 0:
		for move in legal_moves():
			if move.get("en_passant", false):
				en_passant = square_name(en_passant_square)
				break
	return "%s %s %s %s" % [fields[0], fields[1], fields[2], en_passant]


func _current_repetition_count() -> int:
	if _position_keys.is_empty():
		return 0
	var current: String = _position_keys.back()
	var count := 0
	for key in _position_keys:
		if key == current:
			count += 1
	return count


func _add_pawn_move(result: Array, source: int, target: int) -> void:
	var last_row := 0 if white_to_move else 7
	if int(target / 8) == last_row:
		for promotion in PROMOTIONS:
			result.append({"from": source, "to": target, "promotion": promotion})
	else:
		result.append({"from": source, "to": target})


func _add_step(result: Array, source: int, row: int, file: int) -> void:
	if not _inside(row, file):
		return
	var target := row * 8 + file
	if (
		board[target] == ""
		or board[target].to_lower() != "k" and _is_white(board[target]) != white_to_move
	):
		result.append({"from": source, "to": target})


func _add_castles(result: Array, king_square: int) -> void:
	var row := 7 if white_to_move else 0
	if king_square != row * 8 + 4 or is_in_check(white_to_move):
		return
	var enemy := not white_to_move
	var king_right := "K" if white_to_move else "k"
	var queen_right := "Q" if white_to_move else "q"
	if (
		castling_rights.contains(king_right)
		and board[row * 8 + 7] == ("R" if white_to_move else "r")
		and board[row * 8 + 5] == ""
		and board[row * 8 + 6] == ""
		and not _is_attacked(row * 8 + 5, enemy)
		and not _is_attacked(row * 8 + 6, enemy)
	):
		result.append({"from": king_square, "to": row * 8 + 6, "castle": true})
	if (
		castling_rights.contains(queen_right)
		and board[row * 8] == ("R" if white_to_move else "r")
		and board[row * 8 + 1] == ""
		and board[row * 8 + 2] == ""
		and board[row * 8 + 3] == ""
		and not _is_attacked(row * 8 + 3, enemy)
		and not _is_attacked(row * 8 + 2, enemy)
	):
		result.append({"from": king_square, "to": row * 8 + 2, "castle": true})


func _apply(move: Dictionary) -> void:
	var source: int = move.from
	var target: int = move.to
	var piece: String = board[source]
	var moving_pawn := piece.to_lower() == "p"
	var captured_square := target
	if move.get("en_passant", false):
		captured_square = target + (8 if white_to_move else -8)
	var captured: String = board[captured_square]
	board[source] = ""
	board[captured_square] = ""
	if move.get("castle", false):
		var row := int(source / 8)
		if target % 8 == 6:
			board[row * 8 + 5] = board[row * 8 + 7]
			board[row * 8 + 7] = ""
		else:
			board[row * 8 + 3] = board[row * 8]
			board[row * 8] = ""
	var promotion: String = move.get("promotion", "")
	if not promotion.is_empty():
		piece = promotion.to_upper() if white_to_move else promotion
	board[target] = piece
	if piece.to_lower() == "k":
		castling_rights = (
			castling_rights.replace("K", "").replace("Q", "")
			if white_to_move
			else castling_rights.replace("k", "").replace("q", "")
		)
	if source == 63 or target == 63:
		castling_rights = castling_rights.replace("K", "")
	if source == 56 or target == 56:
		castling_rights = castling_rights.replace("Q", "")
	if source == 7 or target == 7:
		castling_rights = castling_rights.replace("k", "")
	if source == 0 or target == 0:
		castling_rights = castling_rights.replace("q", "")
	en_passant_square = -1
	if moving_pawn and abs(target - source) == 16:
		en_passant_square = int((source + target) / 2)
	halfmove_clock = 0 if moving_pawn or captured != "" else halfmove_clock + 1
	if not white_to_move:
		fullmove_number += 1
	white_to_move = not white_to_move


func _is_attacked(square: int, by_white: bool) -> bool:
	var row := int(square / 8)
	var file := square % 8
	var pawn_source_row := row + (1 if by_white else -1)
	for df in [-1, 1]:
		var pawn_file = file + df
		if _inside(pawn_source_row, pawn_file):
			var pawn: String = board[pawn_source_row * 8 + pawn_file]
			if pawn == ("P" if by_white else "p"):
				return true
	for offset in [
		Vector2i(2, 1),
		Vector2i(2, -1),
		Vector2i(-2, 1),
		Vector2i(-2, -1),
		Vector2i(1, 2),
		Vector2i(1, -2),
		Vector2i(-1, 2),
		Vector2i(-1, -2)
	]:
		var r = row + offset.x
		var f = file + offset.y
		if _inside(r, f) and board[r * 8 + f] == ("N" if by_white else "n"):
			return true
	for dr in [-1, 0, 1]:
		for df in [-1, 0, 1]:
			if dr == 0 and df == 0:
				continue
			var r = row + dr
			var f = file + df
			if _inside(r, f) and board[r * 8 + f] == ("K" if by_white else "k"):
				return true
	for direction in [
		Vector2i(1, 0),
		Vector2i(-1, 0),
		Vector2i(0, 1),
		Vector2i(0, -1),
		Vector2i(1, 1),
		Vector2i(1, -1),
		Vector2i(-1, 1),
		Vector2i(-1, -1)
	]:
		var r = row + direction.x
		var f = file + direction.y
		var distance := 1
		while _inside(r, f):
			var piece: String = board[r * 8 + f]
			if piece != "":
				if _is_white(piece) == by_white:
					var kind := piece.to_lower()
					if (
						kind == "q"
						or (
							distance == 1
							and (
								kind == "k"
								or (direction.x == 0 or direction.y == 0) and kind == "r"
								or direction.x != 0 and direction.y != 0 and kind == "b"
							)
						)
					):
						return true
				break
			r += direction.x
			f += direction.y
			distance += 1
	return false


func _king_square(white: bool) -> int:
	var king := "K" if white else "k"
	return board.find(king)


func _is_white(piece: String) -> bool:
	return piece == piece.to_upper()


func _inside(row: int, file: int) -> bool:
	return row >= 0 and row < 8 and file >= 0 and file < 8


func _snapshot() -> Dictionary:
	return {
		"board": board.duplicate(),
		"white": white_to_move,
		"rights": castling_rights,
		"ep": en_passant_square,
		"half": halfmove_clock,
		"full": fullmove_number
	}


func _restore(state: Dictionary) -> void:
	board = state.board
	white_to_move = state.white
	castling_rights = state.rights
	en_passant_square = state.ep
	halfmove_clock = state.half
	fullmove_number = state.full
