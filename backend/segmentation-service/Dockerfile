# Usa un'immagine Python leggera
FROM python:3.10-slim

# Imposta la working directory dentro il container
WORKDIR /app

# Copia i file di progetto
COPY . .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta 5001 per Flask
EXPOSE 5001

# Comando per avviare Flask
CMD ["python", "app.py"]
