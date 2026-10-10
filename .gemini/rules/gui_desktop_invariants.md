---
name: gui_desktop_invariants
description: Règles de rigueur et invariantes pour le développement d'applications graphiques et jeux desktop (zéro prompt console, assets autonomes, résolution absolue des chemins, dégradation gracieuse).
---

# Invariants de Développement GUI & Jeux Desktop

Ces règles doivent être appliquées sans exception dès lors qu'une application de bureau, un jeu vidéo ou une interface utilisateur graphique est développée :

1. **Zéro Console en GUI** :
   - Ne jamais faire appel à `input()` ou demander d'action textuelle dans un terminal pour piloter une application graphique.
   - Les réglages, menus, confirmations, saisies textuelles (chat, nom de joueur/serveur) et sélections doivent obligatoirement être implémentés sous forme de composants ou modales graphiques dans l'application.

2. **Assets Locaux & Intégrité Garantie** :
   - Aucun composant visuel critique ne doit dépendre d'un téléchargement HTTP brut non vérifié lors du démarrage de l'application.
   - Les assets doivent être vérifiés (en-tête de fichier, validation d'extension) ou générés localement (par exemple vectorisation SVG vers PNG) avant exécution.

3. **Résolution Absolue des Chemins de Ressources** :
   - Ne jamais utiliser `os.path.abspath(".")` ou des chemins relatifs au répertoire de travail courant (CWD) pour charger des images, sons ou données.
   - Toujours utiliser une fonction `resource_path()` basée sur l'emplacement du fichier source (`os.path.dirname(os.path.abspath(__file__))`) ou sur le dossier temporaire PyInstaller (`sys._MEIPASS`).

4. **Dégradation Gracieuse (Graceful Fallback)** :
   - Les moteurs ou binaires tiers (comme les moteurs d'échecs UCI, Stockfish, codecs externes) ne doivent jamais bloquer l'application s'ils ne sont pas trouvés.
   - Fournir systématiquement un moteur de secours interne (fallback) opérationnel.

5. **Déploiement et Accessibilité Immédiate** :
   - Mettre à disposition un raccourci de lancement directement utilisable (fichier `.desktop` sous Linux avec droits d'exécution, script batch/raccourci sous Windows).
   - Toujours vérifier le bon fonctionnement de l'exécutable compilé avant de finaliser la tâche.
