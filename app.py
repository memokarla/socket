import streamlit as st
import paramiko
import json
import os
import bcrypt
import tempfile

# Konfigurasi server
SERVER_IP = "10.201.1.229" # try try try
USERNAME = "root"
PASSWORD = "123"
BASE_REMOTE_DIR = "/home/user/uploads"
USER_FILE = "users.json"

# Fungsi untuk koneksi SSH
def create_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=USERNAME, password=PASSWORD)
    return ssh

# Fungsi register user
def register_user(username, password):
    users = load_users()
    if username in users:
        return False  # Username sudah ada
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[username] = hashed_password
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)
    return True

# Fungsi login user
def login_user(username, password):
    users = load_users()
    if username in users and bcrypt.checkpw(password.encode(), users[username].encode()):
        return True
    return False

# Load daftar user dari file JSON
def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

# Fungsi upload file
def upload_file(uploaded_file, user):
    remote_dir = f"{BASE_REMOTE_DIR}/{user}"
    ssh = create_ssh_client()
    sftp = ssh.open_sftp()
    try:
        sftp.mkdir(remote_dir)
    except:
        pass
    remote_path = f"{remote_dir}/{uploaded_file.name}"
    
    if uploaded_file.name in sftp.listdir(remote_dir):
        sftp.close()
        ssh.close()
        return f"File '{uploaded_file.name}' sudah ada di server."
    
    temp_dir = tempfile.gettempdir()
    local_path = os.path.join(temp_dir, uploaded_file.name)
    
    with open(local_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    sftp.put(local_path, remote_path)
    os.remove(local_path)
    
    sftp.close()
    ssh.close()
    return f"File '{uploaded_file.name}' berhasil diunggah ke server."

# Fungsi list file
def list_files(user):
    remote_dir = f"{BASE_REMOTE_DIR}/{user}"
    ssh = create_ssh_client()
    sftp = ssh.open_sftp()
    try:
        files = sftp.listdir(remote_dir)
    except:
        files = []
    sftp.close()
    ssh.close()
    return files

# Fungsi download file
def download_file(user, filename):
    remote_path = f"{BASE_REMOTE_DIR}/{user}/{filename}"
    temp_dir = tempfile.gettempdir()
    local_path = os.path.join(temp_dir, filename)
    ssh = create_ssh_client()
    sftp = ssh.open_sftp()
    sftp.get(remote_path, local_path)
    sftp.close()
    ssh.close()
    return local_path

# Fungsi hapus file
def delete_file(user, filename):
    remote_path = f"{BASE_REMOTE_DIR}/{user}/{filename}"
    ssh = create_ssh_client()
    sftp = ssh.open_sftp()
    sftp.remove(remote_path)
    sftp.close()
    ssh.close()
    return f"File '{filename}' berhasil dihapus."

# UI Streamlit
st.set_page_config(layout="wide")
st.title("File Manager - Server Remote")

if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "files" not in st.session_state:
    st.session_state.files = []

if not st.session_state.logged_in:
    col_login = st.columns([1]) 
    with col_login[0]:
        # st.subheader("Opsi")
        option = st.radio("Pilih opsi:", ["Login", "Register"], index=0)
        if option == "Register":
            st.subheader("Register")
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            if st.button("Daftar"):
                if register_user(new_user, new_pass):
                    st.success("Registrasi berhasil! Silakan login.")
                else:
                    st.error("Username sudah terdaftar.")
        else:
            st.subheader("Login")
            user = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Masuk"):
                if login_user(user, password):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.page = "file_manager"
                    st.session_state.files = list_files(user)
                    st.rerun()
                else:
                    st.error("Username atau password salah.")
else:
    st.subheader("File Manager")
    uploaded_file = st.file_uploader("Upload File ke Server")
    if uploaded_file is not None:
        message = upload_file(uploaded_file, st.session_state.username)
        st.session_state.files = list_files(st.session_state.username)
        st.success(message)
        st.rerun()
    
    st.subheader("Daftar File di Server")
    files = st.session_state.files
    if files:
        selected_file = st.selectbox("Pilih file:", files)
        col1, col2, spacer, col3 = st.columns([1, 1, 5, 1])
        with col1:
            file_path = download_file(st.session_state.username, selected_file)
            with open(file_path, "rb") as f:
                st.download_button("Download", f, file_name=selected_file, use_container_width=True)
        with col2:
            if st.button("Hapus", use_container_width=True):
                st.success(delete_file(st.session_state.username, selected_file))
                st.session_state.files = list_files(st.session_state.username)
                st.rerun()
        with col3:
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.page = "login"
                st.rerun()
