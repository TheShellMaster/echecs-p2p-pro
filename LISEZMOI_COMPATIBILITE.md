# EchecsP2P - Guide de Compatibilité Windows & Linux

Ce jeu a été conçu pour être **100% Cross-Platform** (Windows, Linux, macOS).

## 1. Compilation des exécutables
Si vous souhaitez envoyer le jeu à un ami sans qu'il n'ait à installer Python, vous pouvez générer un fichier exécutable natif (un `.exe` pour Windows ou un binaire pour Linux).

J'ai ajouté deux scripts pour automatiser cela. Dans le dossier du jeu :
* **Sur Linux** : Lancez `./build_linux.sh`
* **Sur Windows** : Double-cliquez sur `build_windows.bat`

Le jeu compilé se trouvera dans le dossier `dist/`.

## 2. Le moteur IA (Stockfish)
Le jeu intègre une détection intelligente de l'IA (Stockfish) :
1. Il cherche d'abord s'il y a un fichier `stockfish.exe` (Windows) ou `stockfish` (Linux) directement dans le dossier du jeu.
2. S'il n'en trouve pas, il cherche dans les variables système (`PATH`).

**Pour vos amis sous Windows :**
Téléchargez simplement Stockfish pour Windows, extrayez le fichier `stockfish.exe` et placez-le dans le même dossier que votre jeu `EchecsP2P.exe`. Le jeu le détectera automatiquement !

## 3. Réseau P2P et Pare-feu (Firewall)
Le jeu utilise le port **UDP 50050** (pour la recherche) et **TCP 50051** (pour jouer).

**Règle d'or sur Windows :**
La première fois qu'un joueur va cliquer sur "Héberger", le Pare-feu Windows (Windows Defender) va afficher une fenêtre d'alerte. 
👉 Il est **impératif** que le joueur clique sur **Autoriser l'accès** (sur les réseaux privés), sinon le jeu ne pourra pas annoncer sa présence sur le réseau local.

*(Aucune configuration n'est requise sur la plupart des distributions Linux standards).*
