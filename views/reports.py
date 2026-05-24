import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from database import get_zeitbuchungen, get_mitarbeiter, get_projekt_zeitbuchungen, get_projekte


def render(user, is_admin):
    st.markdown('<p class="main-header">📊 Reports & Diagramme</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📈 Arbeitszeitanalyse", "⏰ Überstunden", "📁 Projektzeiten"])

    # --- Tab 1: Arbeitszeitanalyse ---
    with tab1:
        st.subheader("Arbeitszeitanalyse")

        col1, col2 = st.columns(2)
        with col1:
            von = st.date_input("Von", value=date.today() - timedelta(days=30), key="rep_von")
        with col2:
            bis = st.date_input("Bis", value=date.today(), key="rep_bis")

        mid = user["id"] if not is_admin else None
        if is_admin:
            mitarbeiter = get_mitarbeiter()
            auswahl = st.selectbox("Mitarbeiter filtern", ["Alle"] + [f"{m['vorname']} {m['nachname']}" for m in mitarbeiter], key="rep_ma")
            if auswahl != "Alle":
                idx = [f"{m['vorname']} {m['nachname']}" for m in mitarbeiter].index(auswahl)
                mid = mitarbeiter[idx]["id"]

        buchungen = get_zeitbuchungen(mitarbeiter_id=mid, von=von.isoformat(), bis=bis.isoformat())

        if buchungen:
            df = pd.DataFrame(buchungen)
            df["datum"] = pd.to_datetime(df["datum"])

            # Tägliche Arbeitszeit
            fig = px.bar(
                df, x="datum", y="ist_stunden", color="vorname",
                title="Tägliche Arbeitszeit",
                labels={"ist_stunden": "Stunden", "datum": "Datum", "vorname": "Mitarbeiter"},
                color_discrete_sequence=["#4CAF50", "#66BB6A", "#81C784"]
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e0e0"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Wochenzusammenfassung
            df["kw"] = df["datum"].dt.isocalendar().week
            weekly = df.groupby("kw").agg({"ist_stunden": "sum", "ueberstunden": "sum"}).reset_index()

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Ist-Stunden", x=weekly["kw"], y=weekly["ist_stunden"], marker_color="#4CAF50"))
            fig2.add_trace(go.Bar(name="Überstunden", x=weekly["kw"], y=weekly["ueberstunden"], marker_color="#FF6B6B"))
            fig2.update_layout(
                title="Wochenübersicht",
                barmode="group",
                xaxis_title="Kalenderwoche",
                yaxis_title="Stunden",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e0e0"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Keine Daten im gewählten Zeitraum.")

    # --- Tab 2: Überstunden ---
    with tab2:
        st.subheader("Überstundenentwicklung")

        buchungen_all = get_zeitbuchungen(
            mitarbeiter_id=user["id"] if not is_admin else None,
            von=(date.today() - timedelta(days=90)).isoformat(),
            bis=date.today().isoformat()
        )

        if buchungen_all:
            df = pd.DataFrame(buchungen_all)
            df["datum"] = pd.to_datetime(df["datum"])

            # Kumulierte Überstunden pro Mitarbeiter
            cumulative = []
            for name, group in df.groupby(["vorname", "nachname"]):
                group = group.sort_values("datum")
                group["kum_ueberstunden"] = group["ueberstunden"].cumsum()
                cumulative.append(group)

            df_cum = pd.concat(cumulative)
            df_cum["name"] = df_cum["vorname"] + " " + df_cum["nachname"]

            fig = px.line(
                df_cum, x="datum", y="kum_ueberstunden", color="name",
                title="Kumulierte Überstunden (letzte 90 Tage)",
                labels={"kum_ueberstunden": "Kumulierte Überstunden", "datum": "Datum", "name": "Mitarbeiter"},
                color_discrete_sequence=["#4CAF50", "#FF6B6B", "#FFA726"]
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e0e0"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Überstunden-Tabelle
            ue_summary = df.groupby(["vorname", "nachname"]).agg(
                total_ueberstunden=("ueberstunden", "sum"),
                durchschnitt_pro_tag=("ueberstunden", "mean"),
                arbeitstage=("datum", "count")
            ).reset_index()
            ue_summary.columns = ["Vorname", "Nachname", "Überstunden gesamt", "Ø pro Tag", "Arbeitstage"]

            st.dataframe(ue_summary, use_container_width=True, hide_index=True)
        else:
            st.info("Keine Daten vorhanden.")

    # --- Tab 3: Projektzeiten ---
    with tab3:
        st.subheader("Projektbezogene Zeitauswertung")

        projekt_buchungen = get_projekt_zeitbuchungen(mitarbeiter_id=user["id"] if not is_admin else None)

        if projekt_buchungen:
            df = pd.DataFrame(projekt_buchungen)

            # Stunden pro Projekt (Pie Chart)
            projekt_sum = df.groupby("projekt_name")["dauer_stunden"].sum().reset_index()

            fig = px.pie(
                projekt_sum, values="dauer_stunden", names="projekt_name",
                title="Stundenverteilung nach Projekt",
                color_discrete_sequence=["#4CAF50", "#66BB6A", "#81C784", "#A5D6A7"]
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e0e0"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Stunden pro Mitarbeiter pro Projekt
            ma_projekt = df.groupby(["projekt_name", "vorname"])["dauer_stunden"].sum().reset_index()
            fig2 = px.bar(
                ma_projekt, x="projekt_name", y="dauer_stunden", color="vorname",
                title="Stunden pro Mitarbeiter & Projekt",
                labels={"dauer_stunden": "Stunden", "projekt_name": "Projekt", "vorname": "Mitarbeiter"},
                color_discrete_sequence=["#4CAF50", "#66BB6A", "#81C784"]
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e0e0"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Keine Projekt-Zeitbuchungen vorhanden.")
