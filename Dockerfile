FROM python:3.12-slim

# Legen Sie das Arbeitsverzeichnis im Container fest
WORKDIR /app

# Kopieren Sie die Abhängigkeitsdatei und installieren Sie die Abhängigkeiten
# Erstellen Sie zuerst eine requirements.txt Datei: pip freeze > requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieren Sie den Rest des Anwendungscodes in das Arbeitsverzeichnis
COPY . .

# Definieren Sie die Umgebungsvariable für die Zeebe-Adresse (kann im K8s-Deployment überschrieben werden)
ENV ZEEBE_ADDRESS="zeebe-gateway.default.svc.cluster.local:26500"
# Definieren Sie die Umgebungsvariable für die Proofing Service URL
ENV PROOFING_SERVICE_API_URL="http://proofing-service.default.svc.cluster.local:8000/api/proofing"
ENV LOG_LEVEL="INFO"
ENV ACTIVITIES_OUTPUT_PATH="/app/activities.json"
ENV REQUEST_TIMEOUT="30"

# Befehl zum Ausführen der Anwendung
CMD ["python", "main.py"]