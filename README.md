# BDS Zeiterfassung

Zeiterfassungssystem für die Battery Damage Service GmbH – entwickelt mit Streamlit und SQLite.

## Features

- ⏱️ **Zeiterfassung** – Kommen/Gehen-Zeiten erfassen und verwalten
- 📁 **Projektverwaltung** – Projekte anlegen, Mitarbeiter zuweisen, Projektzeiten buchen
- 📊 **Reports & Diagramme** – Arbeitszeitanalyse, Überstundenentwicklung, Projektauswertungen
- ⚙️ **Administration** – Mitarbeiter verwalten (Admin-Rolle)

## Lokale Ausführung

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment auf Streamlit Community Cloud

1. Repository auf GitHub pushen
2. Auf [share.streamlit.io](https://share.streamlit.io) anmelden
3. App deployen mit `app.py` als Einstiegspunkt

## Demo-Zugänge

| Name | Rolle |
|------|-------|
| Admin BDS | Administrator |
| Max Mustermann | User |
| Anna Schmidt | User |

## Tech-Stack

- Python 3.11+
- Streamlit
- SQLite
- Pandas
- Plotly
