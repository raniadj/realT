import requests
import json
import time
import os
import smtplib
import logging
import schedule
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config.smtp_config as smtp_config
import config.api_config as api_config

LAST_OFFER_UPDATE_FILE = "last_update.json"

# Configuration du logging
logging.basicConfig(
    filename="realt_monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def log_and_print(message, level="info"):
    print(message)
    getattr(logging, level)(message)

def get_latest_property():
    retries = 3
    session = requests.Session()
    for attempt in range(retries):
        try:
            response = session.get(api_config.URL, headers=api_config.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                log_and_print(f"Erreur {response.status_code} - {response.reason} (Tentative {attempt+1}/{retries})", "error")
        except requests.exceptions.RequestException as e:
            log_and_print(f"Erreur réseau : {e} (Tentative {attempt+1}/{retries})", "error")
        time.sleep(5)
    return None

def load_last_update():
    if os.path.exists(LAST_OFFER_UPDATE_FILE):
        with open(LAST_OFFER_UPDATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_last_update(data):
    filtered_data = {
        "fullName": data.get("fullName"),
        "symbol": data.get("symbol"),
        "tokenPrice": data.get("tokenPrice"),
        "marketplaceLink": data.get("marketplaceLink"),
    }
    with open(LAST_OFFER_UPDATE_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, indent=4, ensure_ascii=False)

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_config.EMAIL_SENDER
        msg["To"] = ", ".join(smtp_config.EMAIL_RECEIVERS)
        msg["Subject"] = subject

        html_body = f"""
        <html>
            <body>
                <h2>Nouvelle vente détectée sur RealT !</h2>
                <p>🏠 <b>Nouvelle offre mise en ligne :</b></p>
                <ul>
                    <li><b>Nom :</b> {body['fullName']}</li>
                    <li><b>Token :</b> {body['symbol']}</li>
                    <li><b>Prix du Token (USD) :</b> {body['tokenPrice']}</li>
                    <li><b><a href="{body['marketplaceLink']}">Voir sur la marketplace</a></b></li>
                </ul>
                <p>Consultez la nouvelle vente dès maintenant !</p>
            </body>
        </html>
        """

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL(smtp_config.SMTP_SERVER, smtp_config.SMTP_PORT) as server:
            server.login(smtp_config.EMAIL_SENDER, smtp_config.EMAIL_PASSWORD)
            server.sendmail(smtp_config.EMAIL_SENDER, smtp_config.EMAIL_RECEIVERS, msg.as_string())

        log_and_print(f"Email envoyé à {', '.join(smtp_config.EMAIL_RECEIVERS)}", "info")

    except Exception as e:
        log_and_print(f"Erreur lors de l'envoi de l'email : {e}", "error")

def check_for_updates():
    latest_property = get_latest_property()
    if latest_property:
        last_saved = load_last_update()
        if last_saved is None or latest_property.get("tokenPrice") != last_saved.get("tokenPrice"):
            log_and_print("\nNOUVELLE OFFRE DÉTECTÉE", "info")
            email_subject = "Nouvelle vente détectée sur RealT !"
            send_email(email_subject, latest_property)
            save_last_update(latest_property)
    else:
        log_and_print("Impossible de récupérer les données, nouvelle tentative dans 5 minutes...", "warning")

def main():
    log_and_print("Surveillance des nouvelles ventes en cours...")
    schedule.every(5).minutes.do(check_for_updates)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
