# Reprise · DevDock v1

État au 29 octobre 2026. Projet reconstruit à partir du cahier des charges ; aucun ancien prototype supposé disponible.

## Fonctionnel

- Application native PySide6 : cartes, barre latérale, recherche nom/chemin, favoris et filtre des aperçus en cours.
- Ajout et modification avec parcours de dossier ; validation du nom, du dossier, des doublons et de l'URL GitHub.
- Bibliothèque JSON dans les données utilisateur, indépendante de l'installation ; écritures atomiques et conservation de l'état précédent en cas d'échec.
- Fichier corrompu conservé, copie de secours tentée, erreur explicite et écritures bloquées jusqu'à réparation.
- Ouverture des dossiers et liens par les applications système.
- Serveurs HTTP statiques réels sur `127.0.0.1`, ports automatiques, plusieurs projets simultanés, ouverture de l'adresse et arrêt individuel/global.
- Retrait confirmé de l'entrée sans suppression des fichiers.
- Exemple copié dans les données utilisateur au premier lancement.
- Thème noir, blanc et argent ; identité its lizhy · Loghan.
- Lanceur BAT, fichier PyInstaller et workflow Windows inclus.

## Vérifications effectuées sous Linux

Python 3.12.14, PySide6 6.8.3, PyInstaller 6.12.0.

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v` : **16 tests réussis**, dont **6 tests de la vraie interface Qt**.

Les contrôles couvrent sauvegarde/relecture, modification, favoris, recherche, validation des entrées, doublons, panne de remplacement atomique, JSON invalide et octets non UTF-8, version inconnue, identifiants dupliqués, dossier disparu, erreurs de lancement, deux serveurs HTTP réels simultanés, arrêt individuel/global, retrait sans perte de fichiers, dialogues Qt, affichage des erreurs, filtre en cours, réactivité de la boucle Qt et fermeture de la fenêtre avec aperçus actifs.

L'interface a également été rendue et sa capture inspectée. Le paquet **Linux** a été construit avec le fichier `DevDock.spec`, puis démarré hors écran dans un dossier de données temporaire : création de la bibliothèque et copie de l'exemple vérifiées. Ce paquet Linux est une vérification du packaging, pas un exécutable Windows.

## Windows : reste à vérifier

Aucun exécutable Windows n'a été construit ou exécuté sur cette machine Linux. Le BAT, Explorer, l'affichage sur un vrai bureau Windows, SmartScreen et la fermeture interactive du binaire Windows restent à valider.

Le workflow `.github/workflows/windows.yml` utilise un runner Windows et Python 3.12 : tests réels, construction, démarrage hors écran du paquet, vérification de l'exemple et création de l'artefact `DevDock-Windows` contenant le ZIP. Le test de démarrage CI ne remplace pas une session interactive Windows. Le binaire n'est pas signé.

## Dépôt et publication

Le dépôt `loghanmrsn/DevDock` existe déjà. Avant publication, `main` pointe vers `f1155708b6d0c767a4bb451a6216f45dc56530c4` et contient un fichier `Readme` vide, conservé. Le commit `ff369e8` de l'ancien contexte n'était pas présent ; cette version ne s'appuie pas dessus.

La lecture Git distante fonctionne. L'accès à `https://api.github.com/repos/loghanmrsn/DevDock` par `gh api` est refusé dans l'environnement actuel ; le domaine API ne figure pas dans sa politique réseau. Sans accès à l'API, le suivi et la vérification de GitHub Actions ne peuvent pas être confirmés ici. Ne jamais transmettre de token dans le chat.

Le résultat de la tentative de publication Git est consigné ci-dessous avant livraison.

## Prochaines étapes

1. Vérifier le résultat de publication ci-dessous. Si nécessaire, publier les sources avec `git push origin HEAD:main` depuis la racine du projet, sans forcer ni remplacer l'historique distant.
2. Autoriser `api.github.com` dans les paramètres réseau si le suivi Actions doit se faire depuis cet environnement ; utiliser l'authentification GitHub déjà fournie.
3. Consulter l'onglet Actions du dépôt, workflow **DevDock Windows**, puis récupérer l'artefact **DevDock-Windows** s'il réussit. Corriger les échecs à partir des journaux réels.
4. Sur Windows, extraire tout le dossier, lancer le BAT puis le binaire, essayer deux aperçus, favoris, sauvegarde/relecture et fermeture complète. Vérifier aussi les chemins accentués et avec espaces.
5. Éventuellement, ajouter des adaptateurs npm/Python/Godot. **Ces fonctionnalités ne sont pas présentes en v1.**

Ne pas modifier Portfolio, SecurePass ou le README du profil pour reprendre DevDock.
