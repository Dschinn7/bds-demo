import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = "zeiterfassung.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS mitarbeiter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vorname TEXT NOT NULL,
            nachname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            rolle TEXT NOT NULL DEFAULT 'user',
            sollstunden_pro_tag REAL NOT NULL DEFAULT 8.0,
            aktiv INTEGER NOT NULL DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS zeitbuchung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mitarbeiter_id INTEGER NOT NULL,
            datum DATE NOT NULL,
            kommen TIME,
            gehen TIME,
            ist_stunden REAL,
            ueberstunden REAL,
            notiz TEXT,
            FOREIGN KEY (mitarbeiter_id) REFERENCES mitarbeiter(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS projekt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projekt_id TEXT UNIQUE NOT NULL,
            bezeichnung TEXT NOT NULL,
            beschreibung TEXT,
            status TEXT NOT NULL DEFAULT 'aktiv',
            start_datum DATE,
            end_datum DATE,
            erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS projekt_mitarbeiter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projekt_id INTEGER NOT NULL,
            mitarbeiter_id INTEGER NOT NULL,
            rolle_im_projekt TEXT DEFAULT 'Mitarbeiter',
            FOREIGN KEY (projekt_id) REFERENCES projekt(id),
            FOREIGN KEY (mitarbeiter_id) REFERENCES mitarbeiter(id),
            UNIQUE(projekt_id, mitarbeiter_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS projekt_zeitbuchung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mitarbeiter_id INTEGER NOT NULL,
            projekt_id INTEGER NOT NULL,
            datum DATE NOT NULL,
            dauer_stunden REAL NOT NULL,
            beschreibung TEXT,
            FOREIGN KEY (mitarbeiter_id) REFERENCES mitarbeiter(id),
            FOREIGN KEY (projekt_id) REFERENCES projekt(id)
        )
    """)

    # Demo-Daten einfügen falls DB leer
    if c.execute("SELECT COUNT(*) FROM mitarbeiter").fetchone()[0] == 0:
        _insert_demo_data(c)

    conn.commit()
    conn.close()


def _insert_demo_data(c):
    # Demo-Mitarbeiter
    c.execute("INSERT INTO mitarbeiter (vorname, nachname, email, rolle, sollstunden_pro_tag) VALUES (?, ?, ?, ?, ?)",
              ("Admin", "BDS", "admin@bds.de", "admin", 8.0))
    c.execute("INSERT INTO mitarbeiter (vorname, nachname, email, rolle, sollstunden_pro_tag) VALUES (?, ?, ?, ?, ?)",
              ("Max", "Mustermann", "max@bds.de", "user", 8.0))
    c.execute("INSERT INTO mitarbeiter (vorname, nachname, email, rolle, sollstunden_pro_tag) VALUES (?, ?, ?, ?, ?)",
              ("Anna", "Schmidt", "anna@bds.de", "user", 6.0))

    # Demo-Projekt
    c.execute("INSERT INTO projekt (projekt_id, bezeichnung, beschreibung, status, start_datum) VALUES (?, ?, ?, ?, ?)",
              ("PRJ-001", "E-PKW Batterie Bergung", "Bergung und Entsorgung beschädigter EV-Batterien", "aktiv", "2026-01-15"))
    c.execute("INSERT INTO projekt (projekt_id, bezeichnung, beschreibung, status, start_datum) VALUES (?, ?, ?, ?, ?)",
              ("PRJ-002", "PV-Speicher Recycling", "Recycling von Heimspeicher-Batterien", "aktiv", "2026-03-01"))

    # Mitarbeiter Projekten zuweisen
    c.execute("INSERT INTO projekt_mitarbeiter (projekt_id, mitarbeiter_id, rolle_im_projekt) VALUES (?, ?, ?)", (1, 2, "Techniker"))
    c.execute("INSERT INTO projekt_mitarbeiter (projekt_id, mitarbeiter_id, rolle_im_projekt) VALUES (?, ?, ?)", (1, 3, "Projektleitung"))
    c.execute("INSERT INTO projekt_mitarbeiter (projekt_id, mitarbeiter_id, rolle_im_projekt) VALUES (?, ?, ?)", (2, 3, "Techniker"))

    # Demo-Zeitbuchungen für die letzten 10 Arbeitstage
    today = date.today()
    for i in range(10):
        d = today - timedelta(days=i)
        if d.weekday() >= 5:  # Wochenende überspringen
            continue
        # Max: 8-17 Uhr
        c.execute("INSERT INTO zeitbuchung (mitarbeiter_id, datum, kommen, gehen, ist_stunden, ueberstunden) VALUES (?, ?, ?, ?, ?, ?)",
                  (2, d.isoformat(), "08:00", "17:00", 9.0, 1.0))
        # Anna: 9-15:30 Uhr
        c.execute("INSERT INTO zeitbuchung (mitarbeiter_id, datum, kommen, gehen, ist_stunden, ueberstunden) VALUES (?, ?, ?, ?, ?, ?)",
                  (3, d.isoformat(), "09:00", "15:30", 6.5, 0.5))

    # Demo Projekt-Zeitbuchungen
    for i in range(5):
        d = today - timedelta(days=i)
        if d.weekday() >= 5:
            continue
        c.execute("INSERT INTO projekt_zeitbuchung (mitarbeiter_id, projekt_id, datum, dauer_stunden, beschreibung) VALUES (?, ?, ?, ?, ?)",
                  (2, 1, d.isoformat(), 4.0, "Batterie-Demontage"))
        c.execute("INSERT INTO projekt_zeitbuchung (mitarbeiter_id, projekt_id, datum, dauer_stunden, beschreibung) VALUES (?, ?, ?, ?, ?)",
                  (3, 1, d.isoformat(), 3.0, "Projektkoordination"))


# --- CRUD Funktionen ---

def get_mitarbeiter(nur_aktive=True):
    conn = get_connection()
    query = "SELECT * FROM mitarbeiter"
    if nur_aktive:
        query += " WHERE aktiv = 1"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_mitarbeiter_by_id(mid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM mitarbeiter WHERE id = ?", (mid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_zeitbuchung(mitarbeiter_id, datum, kommen, gehen, notiz=""):
    conn = get_connection()
    # Ist-Stunden berechnen
    fmt = "%H:%M"
    t_kommen = datetime.strptime(kommen, fmt)
    t_gehen = datetime.strptime(gehen, fmt)
    ist_stunden = round((t_gehen - t_kommen).seconds / 3600, 2)

    # Sollstunden holen
    ma = get_mitarbeiter_by_id(mitarbeiter_id)
    soll = ma["sollstunden_pro_tag"] if ma else 8.0
    ueberstunden = round(ist_stunden - soll, 2)

    conn.execute("""
        INSERT INTO zeitbuchung (mitarbeiter_id, datum, kommen, gehen, ist_stunden, ueberstunden, notiz)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (mitarbeiter_id, datum, kommen, gehen, ist_stunden, ueberstunden, notiz))
    conn.commit()
    conn.close()


def get_zeitbuchungen(mitarbeiter_id=None, von=None, bis=None):
    conn = get_connection()
    query = "SELECT z.*, m.vorname, m.nachname FROM zeitbuchung z JOIN mitarbeiter m ON z.mitarbeiter_id = m.id WHERE 1=1"
    params = []
    if mitarbeiter_id:
        query += " AND z.mitarbeiter_id = ?"
        params.append(mitarbeiter_id)
    if von:
        query += " AND z.datum >= ?"
        params.append(von)
    if bis:
        query += " AND z.datum <= ?"
        params.append(bis)
    query += " ORDER BY z.datum DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_zeitbuchung(buchung_id):
    conn = get_connection()
    conn.execute("DELETE FROM zeitbuchung WHERE id = ?", (buchung_id,))
    conn.commit()
    conn.close()


def update_zeitbuchung(buchung_id, kommen, gehen, notiz, mitarbeiter_id):
    conn = get_connection()
    fmt = "%H:%M"
    t_kommen = datetime.strptime(kommen, fmt)
    t_gehen = datetime.strptime(gehen, fmt)
    ist_stunden = round((t_gehen - t_kommen).seconds / 3600, 2)
    ma = get_mitarbeiter_by_id(mitarbeiter_id)
    soll = ma["sollstunden_pro_tag"] if ma else 8.0
    ueberstunden = round(ist_stunden - soll, 2)
    conn.execute("""
        UPDATE zeitbuchung SET kommen=?, gehen=?, ist_stunden=?, ueberstunden=?, notiz=? WHERE id=?
    """, (kommen, gehen, ist_stunden, ueberstunden, notiz, buchung_id))
    conn.commit()
    conn.close()


# --- Projekt-Funktionen ---

def get_projekte():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM projekt ORDER BY erstellt_am DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_projekt(projekt_id, bezeichnung, beschreibung, status, start_datum, end_datum=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO projekt (projekt_id, bezeichnung, beschreibung, status, start_datum, end_datum)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (projekt_id, bezeichnung, beschreibung, status, start_datum, end_datum))
    conn.commit()
    conn.close()


def get_projekt_mitarbeiter(projekt_db_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.*, pm.rolle_im_projekt FROM projekt_mitarbeiter pm
        JOIN mitarbeiter m ON pm.mitarbeiter_id = m.id
        WHERE pm.projekt_id = ?
    """, (projekt_db_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def assign_mitarbeiter_to_projekt(projekt_db_id, mitarbeiter_id, rolle="Mitarbeiter"):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO projekt_mitarbeiter (projekt_id, mitarbeiter_id, rolle_im_projekt) VALUES (?, ?, ?)",
                     (projekt_db_id, mitarbeiter_id, rolle))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Bereits zugewiesen
    conn.close()


def remove_mitarbeiter_from_projekt(projekt_db_id, mitarbeiter_id):
    conn = get_connection()
    conn.execute("DELETE FROM projekt_mitarbeiter WHERE projekt_id = ? AND mitarbeiter_id = ?",
                 (projekt_db_id, mitarbeiter_id))
    conn.commit()
    conn.close()


def add_projekt_zeitbuchung(mitarbeiter_id, projekt_id, datum, dauer, beschreibung=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO projekt_zeitbuchung (mitarbeiter_id, projekt_id, datum, dauer_stunden, beschreibung)
        VALUES (?, ?, ?, ?, ?)
    """, (mitarbeiter_id, projekt_id, datum, dauer, beschreibung))
    conn.commit()
    conn.close()


def get_projekt_zeitbuchungen(projekt_id=None, mitarbeiter_id=None):
    conn = get_connection()
    query = """SELECT pz.*, m.vorname, m.nachname, p.bezeichnung as projekt_name
               FROM projekt_zeitbuchung pz
               JOIN mitarbeiter m ON pz.mitarbeiter_id = m.id
               JOIN projekt p ON pz.projekt_id = p.id WHERE 1=1"""
    params = []
    if projekt_id:
        query += " AND pz.projekt_id = ?"
        params.append(projekt_id)
    if mitarbeiter_id:
        query += " AND pz.mitarbeiter_id = ?"
        params.append(mitarbeiter_id)
    query += " ORDER BY pz.datum DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_mitarbeiter(vorname, nachname, email, rolle="user", sollstunden=8.0):
    conn = get_connection()
    conn.execute("INSERT INTO mitarbeiter (vorname, nachname, email, rolle, sollstunden_pro_tag) VALUES (?, ?, ?, ?, ?)",
                 (vorname, nachname, email, rolle, sollstunden))
    conn.commit()
    conn.close()


def update_mitarbeiter(mid, vorname, nachname, email, rolle, sollstunden, aktiv):
    conn = get_connection()
    conn.execute("""UPDATE mitarbeiter SET vorname=?, nachname=?, email=?, rolle=?, sollstunden_pro_tag=?, aktiv=? WHERE id=?""",
                 (vorname, nachname, email, rolle, sollstunden, aktiv, mid))
    conn.commit()
    conn.close()
