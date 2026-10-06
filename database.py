"""
Modul Database - Sistem Manajemen Pasien BPJS
Menyediakan operasi CRUD dan utilitas basis data SQLite
"""

import sqlite3
import os
from datetime import datetime

DB_FILE = 'data.db'
BACKUP_DIR = 'backups'


def get_connection():
    """Membuka koneksi ke SQLite dengan timeout aman."""
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    """Membuat tabel users jika belum ada."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nama TEXT NOT NULL,
                        umur INTEGER NOT NULL,
                        jenis_kelamin TEXT NOT NULL,
                        alamat TEXT NOT NULL,
                        no_rm TEXT UNIQUE NOT NULL,
                        no_bpjs TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    conn.commit()
    conn.close()


def is_data_exists(no_rm, no_bpjs, exclude_id=None):
    """
    Mengecek apakah nomor RM atau nomor BPJS sudah ada.
    Dapat mengecualikan ID tertentu saat proses update.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_id:
        cursor.execute(
            "SELECT id, no_rm, no_bpjs FROM users WHERE (no_rm = ? OR no_bpjs = ?) AND id != ?",
            (no_rm, no_bpjs, exclude_id)
        )
    else:
        cursor.execute(
            "SELECT id, no_rm, no_bpjs FROM users WHERE no_rm = ? OR no_bpjs = ?",
            (no_rm, no_bpjs)
        )
    existing = cursor.fetchone()
    conn.close()

    if existing:
        if existing['no_rm'] == no_rm:
            return "No. RM sudah terdaftar pada pasien lain!"
        if existing['no_bpjs'] == no_bpjs:
            return "No. BPJS sudah terdaftar pada pasien lain!"
    return None


def get_all_patients(cari=None, sort_mode="waktu_desc"):
    """Mengambil daftar pasien dengan filter pencarian dan pengurutan."""
    conn = get_connection()
    cursor = conn.cursor()

    order_clauses = {
        "nama_asc": "ORDER BY nama COLLATE NOCASE ASC",
        "nama_desc": "ORDER BY nama COLLATE NOCASE DESC",
        "waktu_asc": "ORDER BY id ASC",
        "waktu_desc": "ORDER BY id DESC",
    }
    order_by = order_clauses.get(sort_mode, "ORDER BY id DESC")

    if cari and cari.strip():
        term = f"%{cari.strip()}%"
        query = f"""
            SELECT id, nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs
            FROM users
            WHERE nama LIKE ? OR no_rm LIKE ? OR no_bpjs LIKE ? OR alamat LIKE ?
            {order_by}
        """
        cursor.execute(query, (term, term, term, term))
    else:
        query = f"""
            SELECT id, nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs
            FROM users
            {order_by}
        """
        cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_patient_by_id(patient_id):
    """Mengambil detail satu pasien berdasarkan ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs FROM users WHERE id = ?",
        (patient_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def tambah_pasien(nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs):
    """Menambahkan data pasien baru ke database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO users (nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (nama.strip(), umur, jenis_kelamin, alamat.strip(), no_rm.strip(), no_bpjs.strip())
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_pasien(patient_id, nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs):
    """Memperbarui data pasien yang sudah ada."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE users 
           SET nama = ?, umur = ?, jenis_kelamin = ?, alamat = ?, no_rm = ?, no_bpjs = ?
           WHERE id = ?""",
        (nama.strip(), umur, jenis_kelamin, alamat.strip(), no_rm.strip(), no_bpjs.strip(), patient_id)
    )
    conn.commit()
    conn.close()


def hapus_pasien(patient_id):
    """Menghapus data pasien dan menyimpan cadangan data terhapus."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (patient_id,))
    patient = cursor.fetchone()

    if patient:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        deleted_file = os.path.join(BACKUP_DIR, 'deleted_data.txt')
        with open(deleted_file, 'a', encoding='utf-8') as f:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(
                f"[{now_str}] ID: {patient['id']}, Nama: {patient['nama']}, Umur: {patient['umur']}, "
                f"JK: {patient['jenis_kelamin']}, Alamat: {patient['alamat']}, "
                f"RM: {patient['no_rm']}, BPJS: {patient['no_bpjs']}\n"
            )

        cursor.execute("DELETE FROM users WHERE id = ?", (patient_id,))
        conn.commit()

    conn.close()
    return patient is not None


def get_statistics():
    """Mengembalikan statistik ringkas jumlah pasien."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE jenis_kelamin = 'Laki-laki'")
    pria = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE jenis_kelamin = 'Perempuan'")
    wanita = cursor.fetchone()[0]

    conn.close()
    return {"total": total, "pria": pria, "wanita": wanita}


def backup_database():
    """Mengekspor seluruh data pasien ke file teks cadangan."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs FROM users ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f'backup_data_{timestamp}.txt')
    standard_backup = os.path.join(BACKUP_DIR, 'backup_data.txt')

    content = []
    content.append("=" * 70)
    content.append(f"BACKUP DATA PASIEN BPJS - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    content.append(f"Total Data: {len(rows)} Pasien")
    content.append("=" * 70)
    content.append(f"{'No':<4} | {'No RM':<12} | {'No BPJS':<15} | {'Nama':<22} | {'JK':<10} | {'Umur':<5} | Alamat")
    content.append("-" * 70)

    for idx, r in enumerate(rows, 1):
        content.append(
            f"{idx:<4} | {r['no_rm']:<12} | {r['no_bpjs']:<15} | {r['nama']:<22} | {r['jenis_kelamin']:<10} | {r['umur']:<5} | {r['alamat']}"
        )

    text_data = "\n".join(content) + "\n"

    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(text_data)

    with open(standard_backup, 'w', encoding='utf-8') as f:
        f.write(text_data)

    return backup_file, len(rows)


# Jalankan inisialisasi tabel saat modul diimpor
create_db()
