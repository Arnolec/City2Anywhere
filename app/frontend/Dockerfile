FROM python:3.12-slim

WORKDIR /app

# Copier en local pour l'instant (Repo privé)
COPY . app

RUN pip3 install -r app/requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "./app/webApp.py", "--server.port=8501", "--server.address=0.0.0.0"]

