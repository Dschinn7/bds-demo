import streamlit as st
import pandas as pd
from datetime import date
from database import (
    get_projekte, add_projekt, get_projekt_mitarbeiter,
    assign_mitarbeiter_to_projekt, remove_mitarbeiter_from_projekt,
    get_mitarbeiter, add_projekt_zeitbuchung, get_projekt_zeitbuchungen
)


def render(user, is_admin):
    st.markdown('<p class="main-header">📁 Projekte</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Übersicht", "⏱️ Zeit buchen", "➕ Neues Projekt" if is_admin else "ℹ️ Info"])

    projekte = get_projekte()

    # --- Tab 1: Übersicht ---
    with tab1:
        st.subheader("Projektübersicht")
        if projekte:
            for p in projekte:
                with st.expander(f"**{p['projekt_id']}** – {p['bezeichnung']} ({p['status']})"):
                    col1, col2 = st.columns(2)
                    col1.write(f"**Beschreibung:** {p['beschreibung'] or '–'}")
                    col1.write(f"**Start:** {p['start_datum'] or '–'}")
                    col2.write(f"**Ende:** {p['end_datum'] or 'offen'}")
                    col2.write(f"**Status:** {p['status']}")

                    # Zugewiesene Mitarbeiter
                    mitglieder = get_projekt_mitarbeiter(p["id"])
                    if mitglieder:
                        st.write("**Team:**")
                        for m in mitglieder:
                            st.write(f"  - {m['vorname']} {m['nachname']} ({m['rolle_im_projekt']})")
                    else:
                        st.caption("Keine Mitarbeiter zugewiesen.")

                    # Admin: Mitarbeiter zuweisen/entfernen
                    if is_admin:
                        st.divider()
                        alle_ma = get_mitarbeiter()
                        zugewiesene_ids = [m["id"] for m in mitglieder]
                        verfuegbar = [m for m in alle_ma if m["id"] not in zugewiesene_ids]

                        col1, col2 = st.columns(2)
                        with col1:
                            if verfuegbar:
                                new_ma = st.selectbox(
                                    "Mitarbeiter hinzufügen",
                                    verfuegbar,
                                    format_func=lambda m: f"{m['vorname']} {m['nachname']}",
                                    key=f"add_ma_{p['id']}"
                                )
                                rolle = st.text_input("Rolle im Projekt", value="Mitarbeiter", key=f"rolle_{p['id']}")
                                if st.button("➕ Zuweisen", key=f"btn_add_{p['id']}"):
                                    assign_mitarbeiter_to_projekt(p["id"], new_ma["id"], rolle)
                                    st.success("Zugewiesen!")
                                    st.rerun()
                        with col2:
                            if mitglieder:
                                rem_ma = st.selectbox(
                                    "Mitarbeiter entfernen",
                                    mitglieder,
                                    format_func=lambda m: f"{m['vorname']} {m['nachname']}",
                                    key=f"rem_ma_{p['id']}"
                                )
                                if st.button("🗑️ Entfernen", key=f"btn_rem_{p['id']}"):
                                    remove_mitarbeiter_from_projekt(p["id"], rem_ma["id"])
                                    st.success("Entfernt!")
                                    st.rerun()
        else:
            st.info("Noch keine Projekte angelegt.")

    # --- Tab 2: Zeit buchen ---
    with tab2:
        st.subheader("Projektzeit buchen")
        if projekte:
            projekt = st.selectbox(
                "Projekt",
                projekte,
                format_func=lambda p: f"{p['projekt_id']} – {p['bezeichnung']}",
                key="pz_projekt"
            )
            col1, col2 = st.columns(2)
            with col1:
                pz_datum = st.date_input("Datum", value=date.today(), key="pz_datum")
            with col2:
                pz_dauer = st.number_input("Dauer (Stunden)", min_value=0.25, max_value=12.0, value=1.0, step=0.25, key="pz_dauer")
            pz_beschreibung = st.text_input("Tätigkeit", key="pz_besch")

            if st.button("✅ Projektzeit speichern", use_container_width=True):
                add_projekt_zeitbuchung(user["id"], projekt["id"], pz_datum.isoformat(), pz_dauer, pz_beschreibung)
                st.success("Projektzeit gebucht!")
                st.rerun()

            # Eigene Buchungen anzeigen
            st.divider()
            st.write("**Meine letzten Projektbuchungen:**")
            meine_buchungen = get_projekt_zeitbuchungen(mitarbeiter_id=user["id"])
            if meine_buchungen:
                df = pd.DataFrame(meine_buchungen)[["datum", "projekt_name", "dauer_stunden", "beschreibung"]]
                df.columns = ["Datum", "Projekt", "Stunden", "Tätigkeit"]
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)
        else:
            st.info("Keine Projekte vorhanden.")

    # --- Tab 3: Neues Projekt (nur Admin) ---
    with tab3:
        if is_admin:
            st.subheader("Neues Projekt anlegen")
            col1, col2 = st.columns(2)
            with col1:
                new_pid = st.text_input("Projekt-ID (z.B. PRJ-003)")
                new_bez = st.text_input("Bezeichnung")
            with col2:
                new_start = st.date_input("Startdatum", value=date.today(), key="new_start")
                new_status = st.selectbox("Status", ["aktiv", "pausiert", "abgeschlossen"])
            new_beschr = st.text_area("Beschreibung")

            if st.button("💾 Projekt erstellen", use_container_width=True):
                if new_pid and new_bez:
                    try:
                        add_projekt(new_pid, new_bez, new_beschr, new_status, new_start.isoformat())
                        st.success(f"Projekt '{new_bez}' erstellt!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
                else:
                    st.warning("Bitte Projekt-ID und Bezeichnung ausfüllen.")
        else:
            st.info("Hier siehst du die Projekte, denen du zugewiesen bist. Für neue Projekte wende dich an einen Administrator.")
