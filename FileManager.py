import streamlit as st
import paramiko
import os
import tempfile
from pathlib import Path
import time
import io
from PIL import Image
import base64

st.set_page_config(
    page_title="SSH File Manager",
    page_icon="🖥️",
    layout="wide"
)

# Fungsi untuk membuat koneksi SSH dengan private key
def create_ssh_client(host, user, key_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Expand path untuk mendukung tilde (~)
        expanded_path = os.path.expanduser(key_path)
        
        if not os.path.exists(expanded_path):
            return f"File private key tidak ditemukan: {expanded_path}"
        
        ssh.connect(
            hostname=host,
            username=user,
            key_filename=expanded_path,
            timeout=10
        )
        return ssh
    except Exception as e:
        return str(e)

# Fungsi untuk mendapatkan daftar file
def get_file_list(ssh_client, path):
    try:
        sftp = ssh_client.open_sftp()
        files = sftp.listdir(path)
        file_info = []
        
        for file in files:
            try:
                full_path = os.path.join(path, file).replace('\\', '/')
                stat = sftp.stat(full_path)
                is_dir = True if stat.st_mode & 0o40000 else False
                size = stat.st_size
                mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                
                # Deteksi tipe file
                file_type = "other"
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    file_type = "image"
                elif ext in ['.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx', '.xls']:
                    file_type = "document"
                elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                    file_type = "video"
                
                file_info.append({
                    'name': file,
                    'path': full_path,
                    'size': size,
                    'modified': mtime,
                    'is_dir': is_dir,
                    'type': file_type,
                    'extension': ext
                })
            except:
                # Skip files with permission issues
                pass
                
        sftp.close()
        return file_info
    except Exception as e:
        return str(e)

# Fungsi untuk mengambil thumbnail gambar
def get_image_thumbnail(ssh_client, file_path, max_size=1024*1024):
    try:
        sftp = ssh_client.open_sftp()
        
        # Cek ukuran file sebelum mengambil
        stats = sftp.stat(file_path)
        if stats.st_size > max_size:
            return None, "File terlalu besar untuk preview"
        
        # Ambil file untuk preview
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            sftp.getfo(file_path, tmp)
            tmp_path = tmp.name
        
        # Buka dan resize gambar untuk thumbnail
        img = Image.open(tmp_path)
        img.thumbnail((200, 200))
        
        # Konversi ke base64 untuk ditampilkan
        buffered = io.BytesIO()
        img.save(buffered, format=img.format if img.format else "JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Bersihkan file temporary
        os.unlink(tmp_path)
        sftp.close()
        
        return img_str, None
    except Exception as e:
        return None, str(e)

# Fungsi untuk menghapus file
def delete_remote_file(ssh_client, file_path):
    try:
        sftp = ssh_client.open_sftp()
        sftp.remove(file_path)
        sftp.close()
        return True, None
    except Exception as e:
        return False, str(e)

# Inisialisasi session state
if 'ssh_client' not in st.session_state:
    st.session_state.ssh_client = None
if 'current_path' not in st.session_state:
    st.session_state.current_path = "/home"
if 'history' not in st.session_state:
    st.session_state.history = []
if 'delete_confirmation' not in st.session_state:
    st.session_state.delete_confirmation = {}

# Tampilkan panduan SSH-keygen
def show_ssh_keygen_guide():
    st.markdown("""
    ## Panduan Menghasilkan SSH Key
    
    Untuk menghasilkan SSH key, Anda dapat mengikuti langkah-langkah berikut:
    
    ### Di Windows (menggunakan Git Bash atau PowerShell):
    1. Buka Git Bash atau PowerShell
    2. Jalankan perintah: `ssh-keygen -t rsa -b 4096`
    3. Ikuti petunjuk yang muncul
    4. Key akan disimpan di `C:\\Users\\YourUsername\\.ssh\\id_rsa`
    
    #### Menyalin public key ke server: Jika menggunakan Git Bash
    ```
    cat ~/.ssh/id_rsa.pub | ssh username@server_ip "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
    ```
    #### Atau bisa menggunakan ssh-copy-id dari Git Bash
    ```
    ssh-copy-id username@server_ip
    ```
    """)

# Form koneksi SSH
def show_connection_form():
    st.title("SSH File Manager")
    
    with st.expander("Panduan SSH-keygen", expanded=False):
        show_ssh_keygen_guide()
    
    st.subheader("Koneksi ke Server")
    col1, col2 = st.columns(2)
    
    with col1:
        server_ip = st.text_input("Host", placeholder="192.168.1.1")
        username = st.text_input("Username", placeholder="root")
    
    with col2:
        private_key_path = st.text_input("Path ke Private Key", 
                                        value="~/.ssh/id_rsa", 
                                        help="Lokasi file private key SSH")
        initial_path = st.text_input("Path Awal", 
                                    value="/home", 
                                    help="Direktori awal saat terhubung")
    
    if st.button("Hubungkan ke Server", use_container_width=True):
        with st.spinner("Menghubungkan ke server..."):
            client = create_ssh_client(server_ip, username, private_key_path)
            
            if isinstance(client, str):
                st.error(f"Koneksi gagal: {client}")
            else:
                st.session_state.ssh_client = client
                st.session_state.current_path = initial_path
                st.session_state.history = [initial_path]
                st.success("Berhasil terhubung ke server!")
                st.rerun()

# Menampilkan fitur utama setelah terhubung
def show_main_interface():
    st.title("SSH File Manager")
    
    # Navigasi dan path
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col1:
        if st.button("⬅️ Kembali") and len(st.session_state.history) > 1:
            st.session_state.history.pop()  # Hapus path terakhir
            st.session_state.current_path = st.session_state.history[-1]  # Set ke path sebelumnya
            st.rerun()
    
    with col2:
        current_path = st.text_input("Path Saat Ini", 
                                    value=st.session_state.current_path,
                                    key="path_input")
        if current_path != st.session_state.current_path:
            st.session_state.current_path = current_path
            st.session_state.history.append(current_path)
            st.rerun()
    
    with col3:
        if st.button("Refresh 🔄", use_container_width=True):
            st.rerun()
    
    # Tab untuk fitur utama
    tab1, tab2, tab3 = st.tabs(["File Manager", "Terminal", "Disconnect"])
    
    with tab1:
        show_file_manager()
    
    with tab2:
        show_terminal()
    
    with tab3:
        show_disconnect()

# Tab File Manager
def show_file_manager():
    st.subheader("File Manager")
    
    # Upload multiple files
    with st.expander("Upload Files", expanded=False):
        uploaded_files = st.file_uploader("Pilih file untuk diunggah", 
                                          accept_multiple_files=True,
                                          help="File akan diunggah ke path saat ini")
        
        if uploaded_files:
            if st.button("Upload Files", use_container_width=True):
                with st.spinner("Mengunggah file..."):
                    try:
                        sftp = st.session_state.ssh_client.open_sftp()
                        
                        for uploaded_file in uploaded_files:
                            temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                            
                            # Simpan ke file sementara
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Upload ke server
                            remote_path = os.path.join(st.session_state.current_path, uploaded_file.name).replace('\\', '/')
                            sftp.put(temp_path, remote_path)
                            
                            # Hapus file sementara
                            os.remove(temp_path)
                        
                        sftp.close()
                        st.success(f"{len(uploaded_files)} file berhasil diunggah!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal mengunggah file: {e}")
    
    # Daftar file
    st.subheader("Daftar File")
    
    # Dapatkan daftar file dari server
    files = get_file_list(st.session_state.ssh_client, st.session_state.current_path)
    
    if isinstance(files, str):
        st.error(f"Gagal mendapatkan daftar file: {files}")
        return
    
    # Tampilkan daftar file dalam tabel
    if files:
        # Urutkan: folder terlebih dahulu, kemudian file
        files = sorted(files, key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        # Buat kolom untuk setiap file
        col_size = 3  # Jumlah kolom per baris
        rows = [files[i:i+col_size] for i in range(0, len(files), col_size)]
        
        for row in rows:
            cols = st.columns(col_size)
            
            for i, file in enumerate(row):
                if i < len(cols):
                    with cols[i]:
                        with st.container():
                            # Tentukan ikon berdasarkan tipe file
                            if file['is_dir']:
                                icon = "📁"
                            elif file['type'] == "image":
                                icon = "🖼️"
                            elif file['type'] == "document":
                                icon = "📄"
                            elif file['type'] == "video":
                                icon = "🎬"
                            else:
                                icon = "📎"
                            
                            st.markdown(f"**{icon} {file['name']}**")
                            
                            # Tampilkan preview gambar jika tipe file adalah gambar
                            if file['type'] == "image":
                                img_b64, error = get_image_thumbnail(st.session_state.ssh_client, file['path'])
                                if img_b64:
                                    st.markdown(f"""
                                    <div style="text-align: center;">
                                        <img src="data:image/jpeg;base64,{img_b64}" style="max-width: 100%; max-height: 150px; margin: 10px 0;">
                                    </div>
                                    """, unsafe_allow_html=True)
                                elif error:
                                    st.caption(f"Preview tidak tersedia: {error}")
                            
                            # Info file
                            file_size = f"{file['size'] / 1024:.1f} KB" if not file['is_dir'] else ""
                            st.caption(f"Modified: {file['modified']}")
                            if file_size:
                                st.caption(f"Size: {file_size}")
                            
                            # Jika direktori, tambahkan tombol navigasi
                            if file['is_dir']:
                                if st.button("Buka", key=f"open_{file['name']}"):
                                    new_path = os.path.join(st.session_state.current_path, file['name']).replace('\\', '/')
                                    st.session_state.current_path = new_path
                                    st.session_state.history.append(new_path)
                                    st.rerun()
                            else:
                                # Untuk file, tambahkan tombol download dan hapus
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    if st.button("⬇️ Download", key=f"download_{file['name']}"):
                                        with st.spinner("Mengunduh file..."):
                                            try:
                                                sftp = st.session_state.ssh_client.open_sftp()
                                                local_path = os.path.join(tempfile.gettempdir(), file['name'])
                                                sftp.get(file['path'], local_path)
                                                
                                                # Baca file dan berikan download button
                                                with open(local_path, "rb") as f:
                                                    file_bytes = f.read()
                                                    st.download_button(
                                                        label=f"Download {file['name']}",
                                                        data=file_bytes,
                                                        file_name=file['name'],
                                                        mime="application/octet-stream"
                                                    )
                                                
                                                sftp.close()
                                            except Exception as e:
                                                st.error(f"Gagal mengunduh file: {e}")
                                
                                with col2:
                                    # Tombol hapus yang lebih besar
                                    file_key = f"delete_{file['name']}"
                                    
                                    # Cek apakah file ini sudah dalam konfirmasi hapus
                                    if file_key in st.session_state.delete_confirmation and st.session_state.delete_confirmation[file_key]:
                                        # Tampilkan konfirmasi tanpa nested columns
                                        st.warning(f"Yakin hapus {file['name']}?")
                                        
                                        # Tombol konfirmasi Ya
                                        if st.button("✓ Ya", key=f"confirm_yes_{file['name']}", use_container_width=True):
                                            with st.spinner("Menghapus file..."):
                                                success, error = delete_remote_file(st.session_state.ssh_client, file['path'])
                                                if success:
                                                    st.success(f"File {file['name']} berhasil dihapus!")
                                                    # Reset status konfirmasi
                                                    st.session_state.delete_confirmation[file_key] = False
                                                    st.rerun()
                                                else:
                                                    st.error(f"Gagal menghapus file: {error}")
                                        
                                        # Tombol konfirmasi Tidak
                                        if st.button("✗ Tidak", key=f"confirm_no_{file['name']}", use_container_width=True):
                                            # Reset status konfirmasi
                                            st.session_state.delete_confirmation[file_key] = False
                                            st.rerun()
                                    else:
                                        # Tombol hapus yang lebih besar dan mencolok
                                        if st.button("🗑️ Hapus", key=file_key, use_container_width=True):
                                            # Aktifkan mode konfirmasi untuk file ini
                                            st.session_state.delete_confirmation[file_key] = True
                                            st.rerun()
                            
                            # Garis pemisah antar file
                            st.markdown("---")
    else:
        st.info("Direktori kosong")

# Tab Terminal
def show_terminal():
    st.subheader("Terminal SSH")
    
    with st.form("terminal_form"):
        command = st.text_input("Masukkan perintah shell:", placeholder="contoh: ls -la")
        submitted = st.form_submit_button("Jalankan Perintah", use_container_width=True)
        
        if submitted and command:
            with st.spinner("Menjalankan perintah..."):
                try:
                    stdin, stdout, stderr = st.session_state.ssh_client.exec_command(command, timeout=30)
                    output = stdout.read().decode()
                    error = stderr.read().decode()
                    
                    if output:
                        st.code(output, language="bash")
                    
                    if error:
                        st.error(error)
                        
                except Exception as e:
                    st.error(f"Gagal menjalankan perintah: {e}")

# Tab Disconnect
def show_disconnect():
    st.subheader("Putuskan Koneksi")
    
    st.warning("Apakah Anda yakin ingin memutuskan koneksi dari server?")
    
    if st.button("Putuskan Koneksi", use_container_width=True):
        try:
            st.session_state.ssh_client.close()
        except:
            pass
        
        # Reset session state
        st.session_state.ssh_client = None
        st.session_state.current_path = "/home"
        st.session_state.history = []
        st.session_state.delete_confirmation = {}
        
        st.success("Berhasil memutuskan koneksi dari server!")
        st.rerun()

# Tampilan utama aplikasi
def main():
    if st.session_state.ssh_client is None:
        show_connection_form()
    else:
        show_main_interface()

if __name__ == "__main__":
    main()