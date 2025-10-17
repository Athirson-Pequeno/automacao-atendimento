import streamlit as st

def aplicar_estilo_sidebar():
    st.markdown("""
    <style>
    /* Títulos */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ecf0f1;
    }

    /* Links do menu */
    [data-testid="stSidebarNav"] ul {
        padding-left: 0;
    }

    [data-testid="stSidebarNav"] li {
        list-style: none;
        margin: 5px 0;
        border-radius: 8px;
        transition: background 0.3s;
    }

    [data-testid="stSidebarNav"] li a {
        color: #ecf0f1 !important;
        text-decoration: none;
        padding: 8px 12px;
        display: block;
        border-radius: 8px;
    }

    [data-testid="stSidebarNav"] li a:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    """, unsafe_allow_html=True)
