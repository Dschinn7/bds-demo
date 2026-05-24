import streamlit as st
from database import init_db

# DB initialisieren
init_db()

st.set_page_config(
    page_title="BDS Zeiterfassung",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS passend zum BDS-Design
st.markdown("""
<style>
    .stApp {
        font-family: 'Segoe UI', sans-serif;
    }
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #4CAF50;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #a0a0a0;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #16213e;
        border-radius: 10px;
        padding: 1.2rem;
        border-left: 4px solid #4CAF50;
    }
    div[data-testid="stSidebar"] {
        background-color: #0f3460;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
    }
    .stButton > button:hover {
        background-color: #45a049;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Session State für Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if not st.session_state.logged_in:
    st.markdown('<p class="main-header">🔋 Battery Damage Service</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Zeiterfassungssystem</p>', unsafe_allow_html=True)

    st.subheader("Anmeldung")

    from database import get_mitarbeiter
    mitarbeiter = get_mitarbeiter()

    if mitarbeiter:
        auswahl = st.selectbox(
            "Mitarbeiter auswählen",
            options=mitarbeiter,
            format_func=lambda m: f"{m['vorname']} {m['nachname']} ({m['rolle']})"
        )
        if st.button("Anmelden", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.user = auswahl
            st.rerun()
    else:
        st.error("Keine Mitarbeiter in der Datenbank gefunden.")
else:
    user = st.session_state.user
    is_admin = user["rolle"] == "admin"

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 🔋 BDS Zeiterfassung")
        st.markdown(f"**{user['vorname']} {user['nachname']}**")
        st.caption(f"Rolle: {'Administrator' if is_admin else 'Mitarbeiter'}")
        st.divider()

        seiten = ["⏱️ Zeiterfassung", "📊 Reports & Diagramme", "📁 Projekte"]
        if is_admin:
            seiten.append("⚙️ Administration")

        seite = st.radio("Navigation", seiten, label_visibility="collapsed")

        st.divider()
        if st.button("🚪 Abmelden", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    # Seiten laden
    if seite == "⏱️ Zeiterfassung":
        from views import zeiterfassung
        zeiterfassung.render(user, is_admin)
    elif seite == "📊 Reports & Diagramme":
        from views import reports
        reports.render(user, is_admin)
    elif seite == "📁 Projekte":
        from views import projekte
        projekte.render(user, is_admin)
    elif seite == "⚙️ Administration":
        from views import admin
        admin.render(user)
