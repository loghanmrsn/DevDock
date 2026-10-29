# DevDock · its lizhy · Loghan

**Moins chercher. Plus créer.**

Une application de bureau Python 3.12 + PySide6 pour retrouver ses projets, ouvrir leurs dossiers et lancer des aperçus web statiques. Noir, blanc et argent, sans compte ni service distant pour la bibliothèque. Direction visuelle inspirée du [portfolio](https://loghanmrsn.github.io/Portfolio/).

## Installer et lancer sur Windows

1. Installer **Python 3.12 64 bits** depuis python.org, avec le lanceur `py`.
2. Extraire **tout** le ZIP des sources dans un dossier accessible en écriture.
3. Double-cliquer sur `Lancer-DevDock.bat`.

Le lanceur crée `.venv` à côté des sources, vérifie Python 3.12, installe `requirements.txt`, puis démarre l'application. Internet est nécessaire pour télécharger PySide6 au premier lancement et pour vérifier les dépendances lors des lancements suivants. En cas d'échec, la console reste ouverte avec l'erreur. Pour lancer sans nouvelle vérification réseau :

```bat
.venv\Scripts\python.exe app.py
```

Ne pas déplacer un environnement `.venv` entre machines. Si un ancien `.venv` utilise une autre version Python, le supprimer puis relancer le BAT ; les données utilisateur ne sont pas dans ce dossier.

### Version empaquetée

Le workflow GitHub Actions `DevDock Windows` construit une archive **DevDock-Windows.zip** contenant un dossier `DevDock` avec `DevDock.exe` et `_internal` (bibliothèques, Qt, thème et exemple). Extraire **tout le dossier**, puis lancer `DevDock.exe`. Python n'est pas nécessaire pour cette version. Ne pas déplacer l'exécutable seul.

L'exécutable n'est pas signé. Windows peut présenter un avertissement SmartScreen. Aucune validation Windows ou archive Windows réussie n'est annoncée tant que le workflow n'a pas effectivement terminé ; voir `REPRISE.md` pour l'état vérifié.

## Utiliser DevDock

- **Ajouter un projet** : saisir le nom, sélectionner un dossier existant, puis éventuellement indiquer `https://github.com/proprietaire/depot`. Les dossiers en double sont refusés, y compris les chemins équivalents après résolution.
- **Modifier** : changer les mêmes champs. Arrêter un aperçu actif avant de modifier le projet.
- **☆ / ★** : enregistrer ou retirer un favori. La recherche porte sur le nom et le chemin, sans distinction de casse.
- **Tous les projets / Favoris / En cours** : « En cours » correspond aux aperçus actuellement lancés par cette instance de DevDock.
- **Dossier / GitHub** : ouvrir dans l'explorateur de fichiers ou le navigateur système. L'URL GitHub est facultative ; seuls les liens HTTPS vers la racine d'un dépôt sont acceptés.
- **Démarrer l'aperçu** : disponible si `index.html` se trouve à la racine du dossier. Chaque serveur choisit un port libre sur `127.0.0.1`. Plusieurs projets peuvent tourner simultanément.
- **Voir l'aperçu** : ouvrir l'adresse affichée. Actualiser le navigateur après une modification des fichiers ; pas de rechargement automatique.
- **Arrêter l'aperçu** : libérer son port. Tous les serveurs sont arrêtés à la fermeture normale de DevDock. Ils ne sont pas restaurés au prochain lancement.
- **Retirer** : après confirmation, arrêter l'aperçu associé et retirer uniquement l'entrée JSON. Aucun fichier du projet n'est supprimé.

Au premier lancement, le petit site `example/` est copié dans les données utilisateur et ajouté comme **Premier aperçu**. Il est modifiable sans toucher à l'installation. Une bibliothèque volontairement vidée ne sera pas repeuplée au lancement suivant.

## Données et erreurs

Sous Windows : `%LOCALAPPDATA%\DevDock\library.json`, normalement `C:\Users\<vous>\AppData\Local\DevDock\library.json`. Le projet exemple est dans le sous-dossier `example`. Les chemins des autres projets restent leurs emplacements d'origine.

La sauvegarde écrit un fichier temporaire dans le même dossier, le synchronise puis remplace le JSON. Si le remplacement échoue, l'ancienne bibliothèque et l'état en mémoire sont conservés. Les erreurs de sauvegarde, d'ouverture et de lancement sont affichées dans l'interface.

Si le JSON est corrompu, DevDock conserve l'original et essaie de créer une copie `library.json.corrupt-<identifiant>.bak`. Un message indique le problème et le chemin de la copie, ou l'échec de celle-ci. L'application bloque les écritures. Fermer DevDock, corriger le JSON ou déplacer l'original ailleurs pour repartir avec une nouvelle bibliothèque, puis relancer. Ne pas supprimer ses projets pour réparer la bibliothèque.

La bibliothèque contient uniquement noms, chemins locaux, URL GitHub et favoris. Aucun compte, télémétrie ou synchronisation. Les clics GitHub ouvrent naturellement un site externe. Utiliser une seule instance de DevDock pour une bibliothèque : la fusion des écritures entre instances n'est pas prise en charge.

## Limites réelles de la v1

- Aperçus **HTML/CSS/JavaScript statiques uniquement**. Aucun lancement npm, Python, Godot, backend, compilation ou installation de dépendances des projets.
- Les fichiers du dossier sélectionné sont servis en HTTP local, accessibles aux processus locaux. Choisir uniquement un dossier web approprié ; pas un dossier de secrets. Les liens symboliques vers l'extérieur du projet sont refusés. Il n'y a ni authentification ni HTTPS sur ces serveurs locaux.
- Les dossiers déplacés ou les disques déconnectés restent dans la bibliothèque ; il faut corriger leur chemin. Ils ne peuvent pas être prévisualisés tant qu'ils sont absents.
- Pas d'import automatique des dépôts GitHub, de clone ou d'opérations Git.
- Qt et le noyau sont testés sous Linux ; Explorer, le BAT, le rendu natif Windows, SmartScreen et le binaire Windows nécessitent leur validation sur Windows.

## Développer et tester

```sh
python3.12 -m venv .venv
# Linux
.venv/bin/python -m pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python app.py
```

Sous Windows :

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
set QT_QPA_PLATFORM=offscreen
.venv\Scripts\python.exe -m unittest discover -s tests -v
set QT_QPA_PLATFORM=
.venv\Scripts\python.exe app.py
```

Les tests utilisent de vrais widgets Qt, des dossiers temporaires et deux vrais serveurs HTTP. Ils ne modifient pas votre bibliothèque. Sous Linux, `XDG_DATA_HOME/DevDock` (ou `~/.local/share/DevDock`) remplace le dossier Windows.

### Construire pour Windows

**Sur Windows**, depuis la racine du dépôt :

```bat
.venv\Scripts\python.exe -m pip install PyInstaller==6.12.0
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean DevDock.spec
```

Résultat : `dist\DevDock\DevDock.exe` et ses dépendances. PyInstaller ne produit pas un exécutable Windows à partir de Linux.

Le workflow `.github/workflows/windows.yml` est déclenché sur les push vers `main`, les pull requests et manuellement. Il utilise Python 3.12 sur `windows-latest`, exécute les tests, construit avec le fichier `.spec`, vérifie un démarrage hors écran avec création de la bibliothèque exemple, puis publie l'artefact `DevDock-Windows`. Ce contrôle automatique de démarrage ne remplace pas un essai interactif sur un vrai bureau Windows.

## Organisation

- `core.py` : bibliothèque, validation, persistance et adaptateur d'aperçu statique.
- `app.py` : interface Qt ; opérations de serveur en arrière-plan.
- `theme.qss` : thème monochrome.
- `tests/` : tests fonctionnels du noyau et de l'interface.
- `example/` : premier projet autonome.
- `DevDock.spec` : ressources et configuration PyInstaller.
- `REPRISE.md` : bilan vérifié et étapes restantes.

L'adaptateur `PreviewManager` est séparé de Qt pour permettre l'ajout futur d'autres lanceurs, avec validation et cycle de vie propres. Aucun de ces lanceurs futurs n'est actif dans cette version.
