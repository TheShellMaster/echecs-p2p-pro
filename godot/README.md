# Nouveau client Échecs

Le nouveau client du jeu est construit avec Godot 4. Le répertoire `core/` contient le cœur de règles hors ligne; `ui/` contient l'accueil et l'écran de partie. Le client Python/Pygame à la racine reste conservé comme version héritée jusqu'à ce que les fonctions phares soient portées et que chaque export ait été vérifié sur son appareil.

## Principes

- Jouer contre l'IA sans compte et sans Internet.
- Jouer à deux sur le même appareil ou découvrir une partie à proximité.
- Interface lumineuse, tactile, lisible, avec des animations courtes et interrompables.
- Aucune dépendance à un service cloud pour les règles, l'IA ou la sauvegarde.
- Portage incrémental : ne pas retirer une fonction historique avant sa parité dans le nouveau client.

## État

La scène d'accueil et le cœur des règles sont en cours d'intégration. Ils ne constituent pas encore une version de jeu livrable. Stockfish, les salons réseau, la reprise de partie, les variantes de rendu et les exports mobiles restent à intégrer et à valider.
