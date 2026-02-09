import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import time
import os
from dotenv import load_dotenv
import json
from discord_webhook import DiscordWebhook, DiscordEmbed

load_dotenv()

# --- KONFIGURATION ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECEIVER = os.getenv("RECEIVER")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
URL = os.getenv("URL")
DATA_FILE = "previous_data.json"
# ---------------------

def send_mail(content):
    msg = EmailMessage()
    msg.set_content(content, subtype='html')
    msg["Subject"] = f"Monster Deal am {time.strftime('%d.%m.%Y')}"
    msg["From"] = EMAIL_USER
    msg["To"] = RECEIVER

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"E-Mail gesendet")
    except Exception as e:
        print(f"Mail-Fehler: {e}")

def send_discord_deal(price, market):
    webhook = DiscordWebhook(url=WEBHOOK_URL)
    
    embed = DiscordEmbed(
        title="Neuer Monster Energy Deal gefunden!",
        color="32cd32"
    )
    
    embed.add_embed_field(name="Preis", value=f"**{price}**", inline=True)
    embed.add_embed_field(name="Händler", value=market, inline=True)
    embed.set_footer(text="Made by Elias")
    embed.set_timestamp()

    webhook.add_embed(embed)
    response = webhook.execute()

    if response.status_code == 200:
        print("Discord Webhook erfolgreich gesendet!")
    else:
        print(f"Fehler beim Senden des Discord Webhooks: {response.status_code} - {response.text}")


headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(URL, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', class_='table-auto')

    rows = []
    for tr in table.tbody.find_all('tr'):
        tds = tr.find_all('td')
        cells = [td.get_text(strip=True) for i, td in enumerate(tds) if i != 5 and i != 0 and i != 1]
        rows.append(cells)

    try:
        with open(DATA_FILE, 'r') as f:
            previous_rows = json.load(f)
    except FileNotFoundError:
        previous_rows = None

    if previous_rows != rows:
        html = """<html><head><style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        </style></head><body>
        <h2>Monster Energy Deals</h2>
        <table>
        <tr><th>Markt</th><th>Preis</th><th>Details</th></tr>"""
        
        for row in rows:
            html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        
        html += "</table></body></html>"
        
        send_mail(html)
        send_discord_deal(rows[0][1], rows[0][0])

        with open(DATA_FILE, 'w') as f:
            json.dump(rows, f)
    else:
        print("Keine Änderungen, keine Benachrichtigung gesendet.")

else:
    print(f"Fehler beim Laden der Seite: {response.status_code}")