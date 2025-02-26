# Otomasi Pengelolaan File Berbasis Web

Otomasi Pengelolaan File Berbasis Web adalah aplikasi berbasis Streamlit yang memungkinkan pengguna untuk mengelola file di server melalui SSH dengan autentikasi RSA.

## Fitur
- Menyediakan keamanan ssh pada server
- Menghubungkan ke server dan menampilkan daftar file
- Mengelola file dengan operasi dasar (unggah, unduh, hapus)

## Persyaratan
Pastikan Anda memiliki:
- Python 3.x terinstal
- Dependensi berikut terinstal:
  ```bash
  pip install streamlit paramiko
  ```

## Cara Menggunakan

### 1. Generate RSA Key
1. Jalankan perintah berikut pada windows untuk menghasilkan pasangan kunci RSA:
   ```bash
   ssh-keygen -t rsa -b 4096
   ```
2. File kunci pribadi akan dibuat di `~/.ssh/id_rsa`, dan kunci publik di `~/.ssh/id_rsa.pub`.

### 2. Mengunggah Kunci Publik ke Server
1. Gunakan perintah berikut untuk menyalin kunci publik ke server:
   ```bash
   cat ~/.ssh/id_rsa.pub | ssh username@server_ip "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
   ```
2. Pastikan server menerima koneksi SSH menggunakan kunci ini.

### 3. Menjalankan Aplikasi
1. Jalankan aplikasi Streamlit dengan perintah berikut:
   ```bash
   streamlit run FileManager.py
   ```
2. Masukkan IP server, username, dan path kunci RSA untuk memulai koneksi.

### 4. Mengelola File di Server
- **Menampilkan daftar file**: Aplikasi akan menampilkan daftar file di direktori tujuan.
- **Mengunggah file**: Pilih file dari lokal dan unggah ke server.
- **Mengunduh file**: Pilih file dari server dan unduh ke lokal.
- **Menghapus file**: Hapus file tertentu di server.

## Troubleshooting
Jika mengalami kendala:
- Pastikan SSH berjalan di server: `sudo systemctl status ssh`
- Pastikan kunci RSA memiliki izin yang benar: `chmod 600 ~/.ssh/id_rsa`
- Periksa konfigurasi SSH di `/etc/ssh/sshd_config`

## Kontribusi
Jika ingin berkontribusi, silakan buat pull request atau ajukan issue pada repository ini.

[![Contributors](https://contrib.rocks/image?repo=memokarla/socket&max=10)](https://github.com/memokarla/socket/graphs/contributors)
