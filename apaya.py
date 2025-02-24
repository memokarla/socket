import streamlit as st
import paramiko
import os
import tempfile

st.set_page_config(layout="wide")
st.title("Remote Server Manager - Secure SSH")

# Fungsi untuk koneksi SSH menggunakan Private Key
def create_ssh_client(host, user, key_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, username=user, key_filename=os.path.expanduser(key_path))
        return ssh
    except Exception as e:
        return str(e)

# Inisialisasi session state
if 'ssh_client' not in st.session_state:
    st.session_state.ssh_client = None
if 'file_list' not in st.session_state:
    st.session_state.file_list = []

# Form koneksi SSH
if st.session_state.ssh_client is None:
    st.subheader("Koneksi ke Server")
    server_ip = st.text_input("Host", value="10.201.0.0")
    username = st.text_input("Username", value="root")
    private_key_path = st.text_input("Private Key Path", value="~/.ssh/id_rsa")
    
    if st.button("Connect to Server"):
        client = create_ssh_client(server_ip, username, private_key_path)
        if isinstance(client, str):
            st.error(f"Koneksi gagal: {client}")
        else:
            st.session_state.ssh_client = client
            st.success("Berhasil terhubung ke server!")
        st.rerun()

# Jika terkoneksi, tampilkan fitur utama
if st.session_state.ssh_client and not isinstance(st.session_state.ssh_client, str):
    ssh_client = st.session_state.ssh_client
    st.success("Connected to Remote Server")

    option = st.radio("Pilih aksi:", ["Jalankan Perintah", "Upload File", "Download / Hapus File", "Disconnect"])

    if option == "Jalankan Perintah":
        st.subheader("Eksekusi Perintah di Server")
        command = st.text_input("Masukkan perintah:", value="df -h")
        if st.button("Jalankan"):
            with st.spinner("Menjalankan perintah..."):
                try:
                    stdin, stdout, stderr = ssh_client.exec_command(command)
                    output = stdout.read().decode()
                    error = stderr.read().decode()
                    if output:
                        st.text_area("Output:", value=output, height=200)
                    if error:
                        st.error(f"Error: {error}")
                except Exception as e:
                    st.error(f"Gagal menjalankan perintah: {e}")

    elif option == "Upload File":
        st.subheader("Upload File ke Server")
        uploaded_file = st.file_uploader("Pilih file untuk diunggah")
        remote_path = st.text_input("Path tujuan di server", value="/home/admin/config/")
        
        if st.button("Upload File") and uploaded_file:
            with st.spinner("Mengunggah file..."):
                try:
                    sftp = ssh_client.open_sftp()
                    temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    sftp.put(temp_path, os.path.join(remote_path, uploaded_file.name))
                    sftp.close()
                    os.remove(temp_path)
                    st.success(f"File {uploaded_file.name} berhasil diunggah ke {remote_path}")
                except Exception as e:
                    st.error(f"Gagal mengunggah file: {e}")

    elif option == "Download / Hapus File":
        st.subheader("Download atau Hapus File dari Server")
        remote_folder_path = st.text_input("Path folder di server", value="/home/admin/config/")
        
        if st.button("List Files"):
            try:
                sftp = ssh_client.open_sftp()
                st.session_state.file_list = sftp.listdir(remote_folder_path)
                sftp.close()
                st.success("Daftar file berhasil dimuat")
            except Exception as e:
                st.error(f"Gagal mengakses folder: {e}")
                st.session_state.file_list = []

        if st.session_state.file_list:
            selected_file = st.selectbox("Pilih file", st.session_state.file_list)
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Download File"):
                    with st.spinner("Mengunduh file..."):
                        try:
                            sftp = ssh_client.open_sftp()
                            remote_file_path = os.path.join(remote_folder_path, selected_file)
                            local_path = os.path.join(tempfile.gettempdir(), selected_file)
                            sftp.get(remote_file_path, local_path)
                            sftp.close()
                            
                            with open(local_path, "rb") as f:
                                st.download_button("Download", f, file_name=selected_file)
                            st.success(f"File {selected_file} berhasil diunduh")
                        except Exception as e:
                            st.error(f"Gagal mengunduh file: {e}")
            
            with col2:
                if st.button("Hapus File"):
                    with st.spinner("Menghapus file..."):
                        try:
                            sftp = ssh_client.open_sftp()
                            sftp.remove(os.path.join(remote_folder_path, selected_file))
                            sftp.close()
                            st.success(f"File {selected_file} berhasil dihapus")
                        except Exception as e:
                            st.error(f"Gagal menghapus file: {e}")
    
    elif option == "Disconnect":
        ssh_client.close()
        st.session_state.ssh_client = None
        st.session_state.file_list = []
        st.success("Disconnected from server")
        st.rerun()
else:
    st.warning("Silakan hubungkan ke server terlebih dahulu.")
