import urllib.request
import os

pieces = {
    'wK': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Chess_klt45.svg/120px-Chess_klt45.svg.png',
    'wQ': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Chess_qlt45.svg/120px-Chess_qlt45.svg.png',
    'wR': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Chess_rlt45.svg/120px-Chess_rlt45.svg.png',
    'wB': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Chess_blt45.svg/120px-Chess_blt45.svg.png',
    'wN': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Chess_nlt45.svg/120px-Chess_nlt45.svg.png',
    'wP': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Chess_plt45.svg/120px-Chess_plt45.svg.png',
    'bK': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Chess_kdt45.svg/120px-Chess_kdt45.svg.png',
    'bQ': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Chess_qdt45.svg/120px-Chess_qdt45.svg.png',
    'bR': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Chess_rdt45.svg/120px-Chess_rdt45.svg.png',
    'bB': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Chess_bdt45.svg/120px-Chess_bdt45.svg.png',
    'bN': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Chess_ndt45.svg/120px-Chess_ndt45.svg.png',
    'bP': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Chess_pdt45.svg/120px-Chess_pdt45.svg.png',
}

for name, url in pieces.items():
    path = os.path.join('/home/theshellpc/Bureau/echec_complet/assets', f"{name}.png")
    print(f"Downloading {name}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(path, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
        if not data.startswith(b'\x89PNG'):
            print(f"ERROR: {name} is not a valid PNG file!")
        else:
            print(f"SUCCESS: {name} saved.")
