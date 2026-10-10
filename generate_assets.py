import chess
import chess.svg
import cairosvg
import os

os.makedirs('/home/theshellpc/Bureau/echec_complet/assets', exist_ok=True)

# Generate individual pieces
pieces = [
    (chess.WHITE, chess.KING, 'wK'), (chess.WHITE, chess.QUEEN, 'wQ'),
    (chess.WHITE, chess.ROOK, 'wR'), (chess.WHITE, chess.BISHOP, 'wB'),
    (chess.WHITE, chess.KNIGHT, 'wN'), (chess.WHITE, chess.PAWN, 'wP'),
    (chess.BLACK, chess.KING, 'bK'), (chess.BLACK, chess.QUEEN, 'bQ'),
    (chess.BLACK, chess.ROOK, 'bR'), (chess.BLACK, chess.BISHOP, 'bB'),
    (chess.BLACK, chess.KNIGHT, 'bN'), (chess.BLACK, chess.PAWN, 'bP'),
]

for color, piece_type, name in pieces:
    svg_data = chess.svg.piece(chess.Piece(piece_type, color), size=120)
    out_path = f"/home/theshellpc/Bureau/echec_complet/assets/{name}.png"
    cairosvg.svg2png(bytestring=svg_data.encode('utf-8'), write_to=out_path)
    print(f"Generated {name}.png")
