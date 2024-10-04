FROM python:3.12-slim

WORKDIR /app

# Copier en local pour l'instant (Repo privé)
COPY app/backend app/backend
COPY back_api.py .
COPY requirements.txt .

RUN pip3 install -r requirements.txt

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=5s --retries=5 CMD curl --include --request GET http://localhost:8000/healthcheck || exit 1

CMD ["fastapi", "run", "back_api.py", "--port", "8000"]
