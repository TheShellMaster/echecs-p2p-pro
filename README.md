# 👑 Échecs P2P Pro (v2.1.0)

<p align="center">
  <img src="assets/logo.png" alt="Échecs P2P Pro Logo" width="160" height="160">
</p>

<p align="center">
  <strong>Jeu d'échecs moderne, multijoueur en réseau local (P2P sans saisie d'IP), et moteur IA Stockfish 19 intégré.</strong>
</p>

<p align="center">
  <a href="#fonctionnalités"><img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12"></a>
  <a href="#fonctionnalités"><img src="https://img.shields.io/badge/Pygame-2.6.1-green.svg" alt="Pygame"></a>
  <a href="#fonctionnalités"><img src="https://img.shields.io/badge/Engine-Stockfish%2019-orange.svg" alt="Stockfish 19"></a>
  <a href="#licence"><img src="https://img.shields.io/badge/License-MIT-purple.svg" alt="MIT License"></a>
</p>

---

## ✨ Points Forts & Fonctionnalités

* 🌐 **Multijoueur P2P LAN sans configuration d'IP** : Auto-découverte des hôtes sur le réseau local via broadcast UDP. Créez un salon personnalisé d'un clic, vos amis le rejoignent instantanément.
* 🤖 **Moteur IA Stockfish 19 & Rythme Immersif** :
  * 4 niveaux de difficulté (Débutant 800 Elo, Intermédiaire 1500 Elo, Avancé 2200 Elo, Grand Maître Monstre 3600+ Elo).
  * Temporisation de réflexion humaine (1.5s à 3s) avec détection et surbrillance des menaces tactiques.
  * Moteur Python de secours intégré (Minimax avec élagage Alpha-Bêta) garantissant zéro panne.
* 🎨 **Interface Lumineuse Grand Public (Style Material 3 / Duolingo)** :
  * Fond clair épuré, cartes blanches flottantes, ombres douces et boutons tactiles 3D à effet d'enfoncement physique.
  * 4 thèmes d'échiquier : *Bois Noble*, *Émeraude Tournoi*, *Néo Sombre*, *Marbre & Onyx*.
* 🎬 **Moteur d'Animations Slow-Motion** :
  * Soulèvement de la pièce sélectionnée avec zoom 1.15x et ombre portée dynamique.
  * Glissement fluide ralenti (280ms avec courbe de décélération cubic).
  * Rebond élastique (*spring bounce*) à l'atterrissage sur la case cible.
  * Ondes de choc visuelles à l'impact (captures / échecs) et pluie de confettis dorés au mat.
* 🏹 **Outils Tactiques au Clic Droit** :
  * Maintien du clic droit + glisser pour tracer des flèches vectorielles d'attaque (style Chess.com/Lichess).
  * Clic droit simple pour marquer une case d'un cercle coloré.
* 📊 **Barre d'Évaluation en Temps Réel (Eval Bar)** : Jauge dynamique Stockfish affichant en direct l'avantage de la position.
* ⏱️ **Pendule Digitale & Historique SAN** : Horloges configurables (Illimité, 3 min Blitz, 5 min, 10 min) avec alerte sous les 30s.
* 💬 **Chat Textuel en Direct** : Messagerie instantanée intégrée lors des parties P2P en réseau.
* 📱 **Fenêtre 100% Responsive** : Redimensionnement en direct (`pygame.RESIZABLE`) et support du plein écran (`F11`).

---

## 🚀 Installation & Lancement

### 1. Prérequis
* Python 3.12 ou supérieur

### 2. Cloner et Lancer
```bash
git clone https://github.com/TheShellMaster/echecs-p2p-pro.git
cd echecs-p2p-pro
pip install -r requirements.txt
python3.12 main.py
```

### 3. Exécutables & Installeurs Autonomes
Des paquets officiels sont disponibles dans le dossier `distribution/` et sur la page **Releases** :
* **Windows** : `Setup-EchecsP2P-v2.exe` (Véritable installeur avec raccourcis et désinstalleur)
* **Linux (Debian / Ubuntu / Mint)** : `echecs-p2p_2.1.0_amd64.deb`
* **Linux (Toutes distributions)** : `EchecsP2P-Linux-Portable.tar.gz` avec script `installer.sh`
* **macOS** : `EchecsP2P.app` bundle

---

## ⌨️ Raccourcis Clavier

| Touche | Action |
| :--- | :--- |
| `F` | Inverser la perspective de l'échiquier (Flip) |
| `M` | Couper / Activer les effets sonores (Mute) |
| `F11` | Basculer en mode Plein Écran |
| `←` / `→` | Naviguer dans l'historique des coups (Replay) |
| `Clic Droit` | Tracer une flèche ou entourer une case |
| `Clic Gauche` | Sélectionner / Jouer / Effacer les annotations |

---

## 📜 Licence

Distribué sous licence **MIT**. Libre d'utilisation, de modification et de distribution.
