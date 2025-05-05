import streamlit as st
import os
from PIL import Image

def get_asset_path(filename):
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', filename)    

sigap_logo_path = get_asset_path('sigap.png')
bangun_icon_path = get_asset_path('bangun.png')

if os.path.exists(sigap_logo_path):
    st.set_page_config(
        page_title="SIGAP - About",
        page_icon=Image.open(sigap_logo_path),
        layout="wide"
    )
else:
    st.set_page_config(
        page_title="SIGAP - About",
        page_icon=Image.open(sigap_logo_path),
        layout="wide"
    )

custom_css = """
    <style>
    html, body, [class*="css"] {
        font-family: inherit !important;
    }
    
    h1, h2, h3, h4, h5, h6,
    p, div, span, label,
    button, .stButton>button {
        font-family: inherit !important;
        font-weight: inherit !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive styles */
    @media (max-width: 640px) {
        .stImage > img {
            max-width: 200px !important;
            margin: 0 auto !important;
            display: block !important;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        .login-container {
            padding: 20px !important;
        }
        
        .stButton button {
            padding: 8px 12px !important;
        }
    }
    
    /* Login form styling */
    .stButton button {
        background-color: #b3127a !important;
        color: white !important;
        font-weight: 500 !important;
        border: none !important;
        padding: 10px 15px !important;
        border-radius: 5px !important;
        transition: all 0.3s !important;
    }
    
    .stButton button:hover {
        background-color: #e620a3 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }
    
    .stTextInput > div > div > input {
        border-radius: 5px !important;
        border: 1px solid #ddd !important;
        padding: 10px 15px !important;
    }
    
    /* Background gradient */
    body {
        background: linear-gradient(135deg, #ffffff, #ffd0ec, #ff77cd, #ff30b8);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    
    /* Logout button styling */
    .logout-btn {
        background-color: #f44336 !important;
        color: white !important;
        font-weight: 500 !important;
        border: none !important;
        padding: 8px 12px !important;
        border-radius: 5px !important;
        transition: all 0.3s !important;
        margin-top: 10px;
    }
    
    .logout-btn:hover {
        background-color: #d32f2f !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }
    </style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state.get("logged_in", False):
    st.success(f"Anda sudah login sebagai {st.session_state.get('username', 'Admin')}")
    if st.button("Lanjut ke Dashboard", type="primary"):
        st.switch_page("pages/Dashboard.py")
    st.stop()

st.markdown("<div style='padding-top: 2rem;'></div>", unsafe_allow_html=True)

st.markdown("""
<div class="login-container" style='background-color: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
    <h1 style='text-align: center; color: #b3127a; margin-bottom: 20px; font-family: "Poppins", sans-serif;'>Login Admin</h1>
    <p style='text-align: center; margin-bottom: 30px; color: #666; font-family: "Poppins", sans-serif;'>
        Silakan masuk untuk mengakses sistem SIGAP
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    creds = {"username": "admin", "password": "sigap123"}
    
    username = st.text_input("Username", placeholder="Masukkan username")
    password = st.text_input("Password", type="password", placeholder="Masukkan password")
    
    login_btn = st.button("Login", type="primary", use_container_width=True)
    
    if login_btn:
        if username == creds["username"] and password == creds["password"]:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("Login berhasil!")
            st.switch_page("pages/Dashboard.py")
        else:
            st.error("Username atau password salah.")

with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>Admin Panel</h2>", unsafe_allow_html=True)
    
    if st.session_state.get("logged_in", False):
        st.success(f"Logged in as {st.session_state.get('username', 'Admin')}")
        
        if st.button("Dashboard", type="primary", use_container_width=True):
            st.switch_page("pages/Dashboard.py")
        
        if st.button("Logout", key="logout_btn", use_container_width=True):
            st.session_state["logged_in"] = False
            if "username" in st.session_state:
                del st.session_state["username"]
            
            st.success("Berhasil logout!")
            st.rerun()
    else:
        st.info("Silakan login untuk mengakses dashboard dan fitur administrasi.")