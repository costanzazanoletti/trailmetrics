# Usa un'immagine Python leggera
FROM python:3.10-slim

# Imposta la working directory dentro il container
WORKDIR /app

# Copia i file di progetto
COPY . .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt


# Comando per avviare Flask
CMD ["python", "app.py"]
