# Login Database Web — Flask + SQLite

## Menjalankan di komputer sendiri
1. Install Python 3.
2. Buka terminal di folder ini.
3. Jalankan:
   ```bash
   python -m venv .venv
   ```
4. Aktifkan virtual environment:
   - Windows CMD: `.venv\Scripts\activate`
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
5. Install library:
   ```bash
   pip install -r requirements.txt
   ```
6. Jalankan:
   ```bash
   python app.py
   ```
7. Buka `http://127.0.0.1:5000`.

Akun awal demo: `admin` / `12345`. Ubah password admin sebelum dipakai secara publik.

## Hosting di Render
1. Upload seluruh isi folder ini ke repository GitHub baru.
2. Di Render pilih **New + → Web Service**, lalu hubungkan repository.
3. Isi:
   - Runtime/Language: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Instance: Free (untuk demo tugas)
4. Tambahkan Environment Variables:
   - `SECRET_KEY` = string acak yang panjang
   - `ADMIN_USERNAME` = username admin yang kamu pilih
   - `ADMIN_PASSWORD` = password admin yang kuat
5. Klik **Create Web Service** dan tunggu deployment selesai. Buka URL `onrender.com` yang diberikan.

## Catatan penting SQLite di Render
Filesystem instance gratis Render bersifat sementara. File `users.db` bisa hilang saat restart/redeploy/spin-down, jadi akun yang dibuat bisa ter-reset. Cocok untuk demo tugas, bukan data penting. Untuk penyimpanan permanen, gunakan database terkelola seperti PostgreSQL atau layanan ber-disk persisten. Jangan menyimpan data sensitif sungguhan di demo ini.
