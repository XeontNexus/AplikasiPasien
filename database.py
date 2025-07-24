import sqlite3

def create_db():
    # Koneksi ke database
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Membuat tabel jika belum ada
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nama TEXT,
                        umur INTEGER,
                        jenis_kelamin TEXT,
                        alamat TEXT,
                        no_rm TEXT,
                        no_bpjs TEXT
                    )''')
    
    conn.commit()
    conn.close()

# Panggil fungsi untuk membuat database dan tabel
create_db()
