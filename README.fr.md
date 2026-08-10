# Docker Pinned Package Checker

<ins>[Français](README.fr.md)</ins>
<ins>[English](README.en.md)</ins>

## À propos

Action GitHub qui vérifie que les versions de paquets **épinglées** (`apt-get install pkg=version`, `apk add pkg=version`, ...) dans un `Dockerfile` sont toujours à jour par rapport au dépôt officiel de la distribution de l'image de base.

Ce check a pour but de prévenir un build d'image docker qui échouera à cause de packages qui ne sont plus disponibles dans l'index des packets de la distribution utilisé par l'image et évite de lancer le build avant que ceux-ci ne soient mis à jour. Faisant ainsi gagner le temps perdu à attendre la construction de l'image pour qu'elle échoue à l'étape RUN (`RUN apt-get install pkg=version`, `RUN apk add pkg=version`)

## Description détaillée

Pour chaque `Dockerfile` fourni, l'action :

1. **Parse le Dockerfile** ligne par ligne (en fusionnant les instructions coupées par `\`) et identifie chaque étape de build (`FROM ... AS ...`) ainsi que ses instructions `RUN`.
2. **Repère les paquets épinglés** dans les instructions `RUN` contenant `apt-get install` ou `apk add` avec une syntaxe `paquet=version`.
3. **Détermine la distribution et la version de l'image de base** de l'étape concernée :
   - résolution des tags basés sur une variable `ARG` (`FROM debian:${VERSION}`) ;
   - résolution des tags basés sur un digest (`@sha256:...`) ;
   - si l'image de base n'est pas nativement reconnue (Alpine / Ubuntu / Debian), l'action utilise [`syft`](https://github.com/anchore/syft) pour scanner l'image et en déduire la distribution et la version réelles.
4. **Télécharge l'index officiel des paquets** correspondant à la distribution/version détectée
5. **Compare** chaque version épinglée dans le `Dockerfile` à la version actuellement disponible dans le dépôt officiel.
6. **Rapporte le résultat** :
   - un message `***** WARNING !!...` est affiché dans les logs pour chaque paquet obsolète, avec la ligne du `Dockerfile` concernée et l'ancienne/nouvelle version ;
   - le job **échoue** (code de sortie non nul) si au moins un paquet épinglé est obsolète, et **réussit** sinon.

### Distributions et gestionnaires de paquets supportés a l'heure d'aujourd'hui

| Distribution | Gestionnaire de paquets | Détection directe |
|---|---|---|
| Debian       | `apt`                   | ✅ |
| Ubuntu       | `apt`                   | ✅ |
| Alpine       | `apk`                   | ✅ |
| Autre        | `apt` ou `apk`          | ✅ via scan `syft` de l'image |

## Prérequis

- Le dépôt doit être checkout **avant** cette action (via [`actions/checkout`](https://github.com/actions/checkout)), car l'action lit le `Dockerfile` depuis `$GITHUB_WORKSPACE`.
- Un runner Linux avec `bash` et `sudo` disponibles (ex. `ubuntu-latest`), car l'action installe `syft` via un script shell.
- Un accès réseau sortant vers : `pypi.org` (dépendances Python), `get.anchore.io` (installation de `syft`), ainsi que `deb.debian.org`, `security.debian.org`, `archive.ubuntu.com` et `dl-cdn.alpinelinux.org` (téléchargement des index de paquets).

## Entrées

### Obligatoires

| Nom | Description |
|---|---|
| `dockerfile` | Chemin, relatif à la racine du dépôt (`$GITHUB_WORKSPACE`), du `Dockerfile` à analyser. |

## Secrets utilisés

Aucun secret n'est requis par l'action.

> ⚠️ Si le `Dockerfile` référence une image de base hébergée sur un registre privé, le runner doit déjà être authentifié (par exemple via [`docker/login-action`](https://github.com/docker/login-action)) **avant** l'exécution de cette action, celle-ci ne gérant pas elle-même l'authentification aux registres.

## Variables d'environnement utilisées

| Variable | Origine | Rôle |
|---|---|---|
| `GITHUB_WORKSPACE` | Fournie automatiquement par le runner GitHub Actions | Utilisée pour construire le chemin absolu du `Dockerfile` à partir de l'entrée `dockerfile`. |
| `GITHUB_ACTION_PATH` | Fournie automatiquement par le runner GitHub Actions | Utilisée pour localiser les fichiers internes de l'action (`requirements.txt`, `main.py`, le template `schema-latest.go` utilisé par `syft`). |
| `RUNNER_OS` | Fournie automatiquement par le runner GitHub Actions | Utilisée pour déterminer l'emplacement du binaire `syft` sur le runner. |
| `DOCKERFILE` | Définie par l'action à partir de l'entrée `dockerfile` | Exposée à l'étape `Run the check` ; le chemin effectif utilisé par le script est cependant construit et transmis en argument de ligne de commande. |

## Exemple d'utilisation

```yaml
name: Check pinned Docker packages

on:
  pull_request:
    paths:
      - "**/Dockerfile"

jobs:
  docker-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Check pinned package versions
        uses: <owner>/<repo>@v1
        with:
          dockerfile: Dockerfile
```

> Remplacez `<owner>/<repo>@v1` par le chemin et la version réels de cette action une fois publiée.

### Exemple multi-Dockerfile

```yaml
jobs:
  docker-check:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        dockerfile:
          - Dockerfile
          - docker/worker/Dockerfile
    steps:
      - uses: actions/checkout@v7

      - name: Check pinned package versions (${{ matrix.dockerfile }})
        uses: <owner>/<repo>@v1
        with:
          dockerfile: ${{ matrix.dockerfile }}
```
