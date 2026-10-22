class_name ChessAI
extends RefCounted
## Intelligence artificielle pour jeu d'échecs, intégrant Stockfish local et Minimax de secours,
## ainsi qu'un système d'apprentissage (coach pédagogique et conseils tactiques).

const UCIEngineScript = preload("res://core/uci_engine.gd")
const ChessRules = preload("res://core/chess_game.gd")

const PIECE_NAMES_FR := {
	"p": "Pion", "n": "Cavalier", "b": "Fou", "r": "Tour", "q": "Dame", "k": "Roi"
}

const PIECE_VALUE := {
	"p": 100, "n": 320, "b": 335, "r": 500, "q": 900, "k": 20000
}

var _uci: RefCounted
var _rng := RandomNumberGenerator.new()

func _init() -> void:
	_rng.randomize()
	_uci = UCIEngineScript.new()

func is_stockfish_active() -> bool:
	return is_instance_valid(_uci) and _uci.is_available()

func get_engine_name() -> String:
	return "Stockfish (Local)" if is_stockfish_active() else "Moteur Intégré (Minimax)"

## Calcule le meilleur coup selon le niveau choisi (1 à 4)
func get_best_move(game: ChessGame, level := 2) -> String:
	var legal := game.legal_moves()
	if legal.is_empty():
		return ""
	
	# Niveau 1 : Débutant (parfois joue un coup simple ou aléatoire pour simuler un apprenti)
	if level == 1 and _rng.randf() < 0.28:
		var random_move: Dictionary = legal[_rng.randi() % legal.size()]
		return game.move_to_uci(random_move)
	
	if is_stockfish_active():
		var skill_map := {1: 1, 2: 6, 3: 13, 4: 20}
		var time_map := {1: 150, 2: 250, 3: 400, 4: 700}
		_uci.set_skill_level(skill_map.get(level, 6))
		var uci: String = _uci.get_best_move(game.get_uci_history(), time_map.get(level, 250))
		if not uci.is_empty():
			# Vérifie la légalité
			for m in legal:
				if game.move_to_uci(m) == uci or game.move_to_uci(m).begins_with(uci.substr(0, 4)):
					return uci
	
	# Moteur interne Minimax alpha-bêta si Stockfish n'est pas utilisé
	var depth := 1 if level == 1 else (2 if level <= 2 else 3)
	return _minimax_root(game, depth)

## Fournit un indice (meilleur coup conseillé + explication)
func get_hint(game: ChessGame) -> Dictionary:
	var legal := game.legal_moves()
	if legal.is_empty():
		return {}
	
	var best_uci := ""
	if is_stockfish_active():
		_uci.set_skill_level(15)
		best_uci = _uci.get_best_move(game.get_uci_history(), 350)
	if best_uci.is_empty():
		best_uci = _minimax_root(game, 2)
	
	if best_uci.is_empty() and not legal.is_empty():
		best_uci = game.move_to_uci(legal[0])
		
	var from_sq := game.square_from_name(best_uci.substr(0, 2))
	var to_sq := game.square_from_name(best_uci.substr(2, 2))
	var piece := game.board[from_sq]
	var target := game.board[to_sq]
	var piece_name: String = PIECE_NAMES_FR.get(piece.to_lower(), "Pièce")
	
	var reason := ""
	if not target.is_empty():
		var target_name: String = PIECE_NAMES_FR.get(target.to_lower(), "pièce")
		reason = "Capture avantageuse : %s prend le %s en %s." % [piece_name, target_name, best_uci.substr(2, 2)]
	elif best_uci in ["e2e4", "d2d4", "e7e5", "d7d5"]:
		reason = "Occupez le centre avec votre pion pour ouvrir le jeu."
	elif best_uci in ["g1f3", "b1c3", "g8f6", "b8c6"]:
		reason = "Développez votre cavalier vers le centre."
	elif best_uci in ["e1g1", "e1c1", "e8g8", "e8c8"]:
		reason = "Mettez votre Roi à l'abri par le roque."
	else:
		reason = "Améliorez le placement de votre %s vers %s." % [piece_name, best_uci.substr(2, 2)]
		
	return {
		"uci": best_uci,
		"from": from_sq,
		"to": to_sq,
		"explanation": reason
	}

## Analyse pédagogique complète de la position pour le mode Apprentissage
func get_coach_evaluation(game: ChessGame, is_white_player: bool) -> Dictionary:
	var white_material := 0
	var black_material := 0
	var player_under_attack: Array[String] = []
	
	for sq in 64:
		var p := game.board[sq]
		if p.is_empty():
			continue
		var val: int = PIECE_VALUE.get(p.to_lower(), 0)
		var is_w := p == p.to_upper()
		if is_w:
			white_material += val
		else:
			black_material += val
			
		# Vérifie si une pièce du joueur est attaquée par l'adversaire
		if is_w == is_white_player and p.to_lower() != "k":
			if game._is_attacked(sq, not is_white_player):
				var name: String = PIECE_NAMES_FR.get(p.to_lower(), "Pièce")
				player_under_attack.append("%s en %s" % [name, game.square_name(sq)])
	
	var mat_diff := (white_material - black_material) if is_white_player else (black_material - white_material)
	var mat_pawns := int(mat_diff / 100.0)
	
	var balance_text := "Égalité matérielle."
	if mat_pawns > 0:
		balance_text = "Avantage matériel : +%d pion(s)." % mat_pawns
	elif mat_pawns < 0:
		balance_text = "Retard matériel : %d pion(s)." % mat_pawns
		
	var advice_list: Array[String] = []
	if not player_under_attack.is_empty():
		advice_list.append("Attention : " + ", ".join(player_under_attack) + " sous pression !")
	else:
		advice_list.append("Vos pièces sont bien protégées.")
		
	# Conseil tactique général
	if game.fullmove_number <= 7:
		advice_list.append("Phase d'ouverture : sortez vos cavaliers et fous, contrôlez le centre.")
	elif game.fullmove_number <= 25:
		advice_list.append("Milieu de jeu : cherchez les colonnes ouvertes et coordonnez vos pièces.")
	else:
		advice_list.append("Finale : activez votre Roi et avancez vos pions passés.")
		
	return {
		"balance": balance_text,
		"advice": advice_list,
		"attacked": player_under_attack
	}

# --- Minimax alpha-bêta interne de secours ------------------------------------------

func _minimax_root(position: ChessGame, depth: int) -> String:
	var moves := position.legal_moves()
	if moves.is_empty():
		return ""
	moves.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			return _move_score(position, a) > _move_score(position, b)
	)
	var maximizing := position.white_to_move
	var best_score := -INF if maximizing else INF
	var best_uci := ""
	var alpha := -INF
	var beta := INF
	
	for move in moves:
		var child := ChessRules.new(position.to_fen())
		var uci: String = position.move_to_uci(move)
		if not child.play_uci(uci):
			continue
		var score := _minimax(child, depth - 1, alpha, beta)
		if (maximizing and score > best_score) or (not maximizing and score < best_score):
			best_score = score
			best_uci = uci
		if maximizing:
			alpha = maxf(alpha, best_score)
		else:
			beta = minf(beta, best_score)
	return best_uci

func _minimax(position: ChessGame, depth: int, alpha_in: float, beta_in: float) -> float:
	if depth <= 0:
		return _eval_position(position)
	var moves := position.legal_moves()
	if moves.is_empty():
		if position.is_in_check(position.white_to_move):
			return 100000.0 if not position.white_to_move else -100000.0
		return 0.0
	moves.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			return _move_score(position, a) > _move_score(position, b)
	)
	var maximizing := position.white_to_move
	var alpha := alpha_in
	var beta := beta_in
	var best := -INF if maximizing else INF
	for move in moves:
		var child := ChessRules.new(position.to_fen())
		if not child.play_uci(position.move_to_uci(move)):
			continue
		var score := _minimax(child, depth - 1, alpha, beta)
		best = maxf(best, score) if maximizing else minf(best, score)
		if maximizing:
			alpha = maxf(alpha, best)
		else:
			beta = minf(beta, best)
		if beta <= alpha:
			break
	return best

func _eval_position(position: ChessGame) -> float:
	var score := 0.0
	for square in 64:
		var piece: String = position.board[square]
		if piece.is_empty():
			continue
		var white := piece == piece.to_upper()
		var value: int = PIECE_VALUE[piece.to_lower()]
		var row := int(square / 8)
		var file := square % 8
		var center_bonus: int = 7 - (absi(3 - file) + absi(3 - row))
		var positional: int = center_bonus * (3 if piece.to_lower() != "k" else 1)
		score += value + positional if white else -(value + positional)
	return score

func _move_score(position: ChessGame, move: Dictionary) -> int:
	var target: String = position.board[move.to]
	var score := 0
	if not target.is_empty():
		score += (
			int(PIECE_VALUE[target.to_lower()]) * 10
			- int(PIECE_VALUE[position.board[move.from].to_lower()])
		)
	if not String(move.get("promotion", "")).is_empty():
		score += 8000
	return score
