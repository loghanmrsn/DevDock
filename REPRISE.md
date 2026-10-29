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

## Windows : validation automatique réussie

Le workflow [40852783624](https://github.com/loghanmrsn/DevDock/actions/runs/40852783624), au commit `68c0c16`, a terminé avec **Success** le 29 octobre 2026.

- Les **16 tests** passent sur `windows-latest` avec Python 3.12 et la vraie interface Qt hors écran.
- PyInstaller a construit `DevDock.exe` et toutes ses dépendances.
- Le contrôle CI a lancé cet exécutable pendant 8 secondes dans un dossier de données temporaire et vérifié la bibliothèque et le projet exemple.
- L'artefact **DevDock-Windows**, environ 47,5 Mo, a été publié. Il contient `DevDock-Windows.zip` ; extraire tout le dossier `DevDock`, et non uniquement l'exécutable.

Le premier passage Windows avait révélé un problème dans une assertion de test : un chemin temporaire non résolu était comparé au chemin canonique enregistré. Les dossiers temporaires des tests sont désormais résolus avant comparaison ; la vérification de confinement de l'exemple reste active. Les tests Linux repassent après cette correction.

**Reste à vérifier manuellement sur Windows :** le BAT, l'ouverture réelle d'Explorer et du navigateur, le rendu sur écran et DPI Windows, les avertissements SmartScreen et une session interactive du binaire avec fermeture normale. Le démarrage hors écran et les tests automatisés réussis ne remplacent pas ces essais. Le binaire n'est pas signé.

## Dépôt et publication

Le dépôt public [loghanmrsn/DevDock](https://github.com/loghanmrsn/DevDock) existe. Les sources et le workflow ont été publiés sur `main` par un push normal, sans réécriture de l'historique. Le commit initial `f1155708b6d0c767a4bb451a6216f45dc56530c4` a été préservé dans l'historique. Une suppression distante du `Readme` vide (`9f5f52a`) a été intégrée par avance rapide, sans le rétablir. Le commit `ff369e8` de l'ancien contexte n'était pas présent ; cette version ne s'appuie pas dessus.

La lecture et l'écriture Git fonctionnent. L'API `api.github.com` est refusée dans cet environnement ; les pages publiques GitHub Actions ont permis de suivre les exécutions. Le workflow publie les résultats des tests dans son résumé et les échecs dans ses annotations pour permettre le diagnostic. Aucun secret n'a été demandé ni inclus dans les livrables.

Le ZIP source est composé uniquement des fichiers suivis du projet, sans `.git`, `.venv`, caches, données personnelles ou secrets. Une extraction indépendante de ce ZIP a passé les **16 tests sous Linux** avec les dépendances déjà installées. Les retours de ligne du BAT dans le ZIP sont adaptés à Windows.

## Prochaines étapes

1. Récupérer l'artefact **DevDock-Windows** depuis le [workflow réussi](https://github.com/loghanmrsn/DevDock/actions/runs/40852783624). GitHub peut demander une connexion pour télécharger les artefacts, même si le dépôt est public.
2. Sur Windows, extraire tout le dossier, lancer le BAT puis le binaire, essayer deux aperçus, favoris, sauvegarde/relecture et fermeture complète. Vérifier aussi les chemins accentués et avec espaces.
3. Consulter les journaux et annotations des futurs workflows si un nouveau changement échoue. Pour utiliser `gh` depuis cet environnement, l'accès à `api.github.com` doit être autorisé dans les paramètres réseau ; ne pas transmettre de token dans le chat.
4. Éventuellement, ajouter des adaptateurs npm/Python/Godot. **Ces fonctionnalités ne sont pas présentes en v1.**

Ne pas modifier Portfolio, SecurePass ou le README du profil pour reprendre DevDock.
