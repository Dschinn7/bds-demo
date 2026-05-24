import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import add_zeitbuchung, get_zeitbuchungen, delete_zeitbuchung, update_zeitbuchung


def render(user, is_admin):
    st.markdown('<p class="main-header">⏱️ Zeiterfassung</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📝 Neue Buchung", "📋 Meine Buchungen"])

    with tab1:
        st.subheader("Kommen & Gehen erfassen")
        col1, col2, col3 = st.columns(3)

        with col1:
            buchung_datum = st.date_input("Datum", value=date.today())
        with col2:
            kommen = st.time_input("Kommen", value=datetime.strptime("08:00", "%H:%M").time())
        with col3:
            gehen = st.time_input("Gehen", value=datetime.strptime("17:00", "%H:%M").time())

        notiz = st.text_input("Notiz (optional)")

        if st.button("✅ Buchung speichern", use_container_width=True):
            if gehen <= kommen:
                st.error("Die Gehen-Zeit muss nach der Kommen-Zeit liegen.")
            else:
                add_zeitbuchung(
                    mitarbeiter_id=user["id"],
                    datum=buchung_datum.isoformat(),
                    kommen=kommen.strftime("%H:%M"),
                    gehen=gehen.strftime("%H:%M"),
                    notiz=notiz
                )
                st.success("Buchung erfolgreich gespeichert!")
                st.rerun()

    with tab2:
        st.subheader("Buchungsübersicht")

        col1, col2 = st.columns(2)
        with col1:
            von = st.date_input("Von", value=date.today().replace(day=1), key="filter_von")
        with col2:
            bis = st.date_input("Bis", value=date.today(), key="filter_bis")

        buchungen = get_zeitbuchungen(
            mitarbeiter_id=user["id"] if not is_admin else None,
            von=von.isoformat(),
            bis=bis.isoformat()
        )

        if buchungen:
            df = pd.DataFrame(buchungen)
            display_cols = ["datum", "vorname", "nachname", "kommen", "gehen", "ist_stunden", "ueberstunden", "notiz"]
            if not is_admin:
                display_cols = ["datum", "kommen", "gehen", "ist_stunden", "ueberstunden", "notiz"]

            st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "datum": "Datum",
                    "vorname": "Vorname",
                    "nachname": "Nachname",
                    "kommen": "Kommen",
                    "gehen": "Gehen",
                    "ist_stunden": st.column_config.NumberColumn("Ist (h)", format="%.1f"),
                    "ueberstunden": st.column_config.NumberColumn("Überstunden", format="%.1f"),
                    "notiz": "Notiz"
                }
            )

            # Zusammenfassung
            total_ist = sum(b["ist_stunden"] for b in buchungen if b["ist_stunden"])
            total_ue = sum(b["ueberstunden"] for b in buchungen if b["ueberstunden"])

            col1, col2, col3 = st.columns(3)
            col1.metric("Gesamtstunden", f"{total_ist:.1f} h")
            col2.metric("Überstunden", f"{total_ue:+.1f} h")
            col3.metric("Buchungen", len(buchungen))

            # Bearbeitung/Löschen
            if is_admin:
                st.divider()
                st.subheader("Buchung bearbeiten/löschen")
                buchung_ids = [f"ID {b['id']} - {b['vorname']} {b['nachname']} - {b['datum']}" for b in buchungen]
                selected = st.selectbox("Buchung auswählen", buchung_ids)
                if selected:
                    idx = buchung_ids.index(selected)
                    b = buchungen[idx]
                    col1, col2 = st.columns(2)
                    with col1:
                        new_kommen = st.text_input("Kommen", value=b["kommen"], key="edit_k")
                    with col2:
                        new_gehen = st.text_input("Gehen", value=b["gehen"], key="edit_g")
                    new_notiz = st.text_input("Notiz", value=b["notiz"] or "", key="edit_n")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Aktualisieren"):
                            update_zeitbuchung(b["id"], new_kommen, new_gehen, new_notiz, b["mitarbeiter_id"])
                            st.success("Aktualisiert!")
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Löschen", type="secondary"):
                            delete_zeitbuchung(b["id"])
                            st.success("Gelöscht!")
                            st.rerun()
        else:
            st.info("Keine Buchungen im gewählten Zeitraum.")
