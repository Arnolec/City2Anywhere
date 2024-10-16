# City2Anywhere

![Page de couverture du projet](https://www.dropbox.com/scl/fi/l7izgqf515mgbrtn0ntwv/Photo_Projet.png?rlkey=bhbydiiwt771er93elyd0ym4u&st=h72esse9&raw=1)

## Introduction
**City2Anywhere** est une application innovante en cours de développement qui aide les utilisateurs à explorer facilement des destinations et à planifier des trajets à partir d'une ville de départ. Conçue avec une architecture conteneurisée, elle propose une expérience fluide et interactive, avec une communication optimisée entre le backend et le frontend.

## Installation
### Prérequis
- Python (avec les dépendances du fichier `requirements.txt`)
- Docker (optionnel)

### Lancer le projet
**Sans Docker :**
```bash
fastapi run back_api.py
streamlit run app/frontend/webApp.py
```

**Avec Docker :**
```bash
docker build -t back_api .
docker build -t web_app app/frontend
docker run back_api
docker run web_app
```
