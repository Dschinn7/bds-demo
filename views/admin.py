import streamlit as st
import pandas as pd
from database import get_mitarbeiter, add_mitarbeiter, update_mitarbeiter, get_zeitbuchungen


def render(user):
    st.markdown('<p class="main-header">⚙️ Administration</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👥 Mitarbeiterverwaltung", "➕ Neuer Mitarbeiter"])

    # --- Tab 1: Mitarbeiter verwalten ---
    with tab1:
        st.subheader("Mitarbeiter verwalten")
        mitarbeiter = get_mitarbeiter(nur_aktive=False)

        if mitarbeiter:
            df = pd.DataFrame(mitarbeiter)
            st.dataframe(
                df[["id", "vorname", "nachname", "email", "rolle", "sollstunden_pro_tag", "aktiv"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "vorname": "Vorname",
                    "nachname": "Nachname",
                    "email": "E-Mail",
                    "rolle": "Rolle",
                    "sollstunden_pro_tag": st.column_config.NumberColumn("Soll h/Tag", format="%.1f"),
                    "aktiv": st.column_config.CheckboxColumn("Aktiv")
                }
            )

            st.divider()
            st.subheader("Mitarbeiter bearbeiten")
            selected = st.selectbox(
                "Mitarbeiter auswählen",
                mitarbeiter,
                format_func=lambda m: f"{m['vorname']} {m['nachname']} (ID: {m['id']})"
            )

            if selected:
                col1, col2 = st.columns(2)
                with col1:
                    ed_vorname = st.text_input("Vorname", value=selected["vorname"], key="ed_vn")
                    ed_nachname = st.text_input("Nachname", value=selected["nachname"], key="ed_nn")
                    ed_email = st.text_input("E-Mail", value=selected["email"], key="ed_em")
                with col2:
                    ed_rolle = st.selectbox("Rolle", ["user", "admin"], index=0 if selected["rolle"] == "user" else 1, key="ed_ro")
                    ed_soll = st.number_input("Sollstunden/Tag", value=selected["sollstunden_pro_tag"], min_value=1.0, max_value=12.0, step=0.5, key="ed_sh")
                    ed_aktiv = st.checkbox("Aktiv", value=bool(selected["aktiv"]), key="ed_ak")

                if st.button("💾 Änderungen speichern", use_container_width=True):
                    update_mitarbeiter(selected["id"], ed_vorname, ed_nachname, ed_email, ed_rolle, ed_soll, 1 if ed_aktiv else 0)
                    st.success("Mitarbeiter aktualisiert!")
                    st.rerun()

    # --- Tab 2: Neuer Mitarbeiter ---
    with tab2:
        st.subheader("Neuen Mitarbeiter anlegen")
        col1, col2 = st.columns(2)
        with col1:
            new_vn = st.text_input("Vorname", key="new_vn")
            new_nn = st.text_input("Nachname", key="new_nn")
        with col2:
            new_email = st.text_input("E-Mail", key="new_email")
            new_rolle = st.selectbox("Rolle", ["user", "admin"], key="new_rolle")
            new_soll = st.number_input("Sollstunden/Tag", value=8.0, min_value=1.0, max_value=12.0, step=0.5, key="new_soll")

        if st.button("➕ Mitarbeiter anlegen", use_container_width=True):
            if new_vn and new_nn and new_email:
                try:
                    add_mitarbeiter(new_vn, new_nn, new_email, new_rolle, new_soll)
                    st.success(f"{new_vn} {new_nn} wurde angelegt!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler: {e}")
            else:
                st.warning("Bitte alle Pflichtfelder ausfüllen.")
