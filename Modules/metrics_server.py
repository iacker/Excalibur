from flask import Flask
from prometheus_client import make_wsgi_app, Gauge, REGISTRY
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
import json

app = Flask(__name__)

# Définition de la gauge Prometheus
ports_open_gauge = Gauge('nmap_ports_open', 'Number of open ports', ['target'])

# Fonction pour charger et traiter le fichier JSON généré par Excalibur
def load_json_results():
    # Chemin vers le fichier JSON généré par Excalibur
    json_file_path = 'nmap_report.json'
    try:
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
            # Assurez-vous d'adapter le traitement en fonction de la structure de votre JSON
            for result in data['nmaprun']['host']:
                target = result['address']['@addr']
                ports_open = sum(1 for port in result['ports']['port'] if port['state']['@state'] == 'open')
                ports_open_gauge.labels(target=target).set(ports_open)
    except FileNotFoundError:
        print(f"Le fichier {json_file_path} n'a pas été trouvé.")

# Route pour mettre à jour les métriques manuellement via une requête HTTP
@app.route('/update_metrics')
def update_metrics():
    load_json_results()
    return "Métriques mises à jour."

# Configuration du middleware Prometheus pour exposer les métriques
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

if __name__ == '__main__':
    # Démarrez le serveur Flask avec le middleware Prometheus
    run_simple('localhost', 5000, app.wsgi_app)
