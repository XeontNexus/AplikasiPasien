"""
====================================================================
Modul Database Online & Sinkronisasi Data (MySQL / MariaDB)
Sistem Penyimpanan Ganda (Lokal SQLite & Online MySQL)
====================================================================
"""

import os
import json
import sqlite3
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime
import database

CONFIG_FILE = "config_db.json"

DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "db_pasien_bpjs",
    "charset": "utf8mb4",
    "timeout": 5
}


def load_config():
    """Memuat konfigurasi koneksi MySQL dari file JSON."""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Pastikan semua field penting ada
            for key, val in DEFAULT_CONFIG.items():
                if key not in cfg:
                    cfg[key] = val
            return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(cfg):
    """Menyimpan konfigurasi koneksi MySQL ke file JSON."""
    try:
        # Sanitasi port menjadi integer
        if "port" in cfg:
            try:
                cfg["port"] = int(cfg["port"])
            except ValueError:
                cfg["port"] = 3306

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        return True
    except Exception as e:
        print(f"Error menyimpan config: {e}")
        return False


def get_mysql_connection(config=None, create_db_if_missing=True):
    """
    Membuka koneksi ke MySQL.
    Jika database belum ada di server, otomatis membuat database tersebut.
    """
    if config is None:
        config = load_config()

    host = config.get("host", "localhost")
    port = int(config.get("port", 3306))
    user = config.get("user", "root")
    password = config.get("password", "")
    db_name = config.get("database", "db_pasien_bpjs")
    timeout = int(config.get("timeout", 5))

    if create_db_if_missing:
        # Hubungkan ke server MySQL tanpa memilih database terlebih dahulu
        try:
            temp_conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                charset="utf8mb4",
                connect_timeout=timeout,
                cursorclass=DictCursor
            )
            with temp_conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            temp_conn.commit()
            temp_conn.close()
        except Exception:
            pass  # Jika user tidak memiliki hak CREATE DATABASE, lanjutkan koneksi langsung

    # Koneksi langsung ke database yang dituju
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        charset="utf8mb4",
        connect_timeout=timeout,
        cursorclass=DictCursor
    )

    # Inisialisasi tabel users jika belum ada
    init_online_table(conn)
    return conn


def init_online_table(conn):
    """Membuat tabel users di database MySQL online jika belum ada."""
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `users` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `nama` VARCHAR(255) NOT NULL,
                `umur` INT NOT NULL,
                `jenis_kelamin` VARCHAR(50) NOT NULL,
                `alamat` TEXT NOT NULL,
                `no_rm` VARCHAR(100) NOT NULL,
                `no_bpjs` VARCHAR(100) NOT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY `idx_no_rm` (`no_rm`),
                UNIQUE KEY `idx_no_bpjs` (`no_bpjs`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
    conn.commit()


def test_connection(config=None):
    """
    Menguji koneksi ke server MySQL online.
    Mengembalikan (sukses: bool, pesan: str)
    """
    if config is None:
        config = load_config()

    try:
        conn = get_mysql_connection(config, create_db_if_missing=True)
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() as version, DATABASE() as current_db")
            row = cursor.fetchone()
            version = row.get("version", "Unknown") if row else "Unknown"
            db_name = row.get("current_db", config.get("database"))
        conn.close()
        return True, f"Koneksi Berhasil!\nServer: MySQL/MariaDB v{version}\nDatabase: {db_name}"
    except pymysql.err.OperationalError as e:
        code, msg = e.args if len(e.args) == 2 else (0, str(e))
        if code == 2003:
            return False, f"Gagal menghubungi server '{config.get('host')}': Port {config.get('port')} tidak merespon / server belum aktif."
        elif code == 1045:
            return False, "Akses ditolak: Username atau Password database MySQL salah."
        elif code == 1049:
            return False, f"Database '{config.get('database')}' tidak ditemukan di server."
        else:
            return False, f"Operational Error ({code}): {msg}"
    except Exception as e:
        return False, f"Gagal terhubung ke MySQL: {str(e)}"


# ====================================================================
# FUNGSI TRANSFER DATA (LOKAL <-> ONLINE)
# ====================================================================

def transfer_lokal_ke_online():
    """
    Mengunggah seluruh data dari database lokal (SQLite) ke database online (MySQL).
    Menggunakan mekanisme UPSERT (INSERT ... ON DUPLICATE KEY UPDATE)
    agar tidak terjadi error duplikasi dan data terupdate jika sudah ada.
    """
    # 1. Ambil seluruh data dari SQLite lokal
    pasien_lokal = database.get_all_patients(sort_mode="waktu_asc")
    if not pasien_lokal:
        return True, "Database lokal masih kosong, tidak ada data yang perlu ditransfer."

    # 2. Buka koneksi ke MySQL online
    conn = get_mysql_connection()
    terproses = 0
    diperbarui = 0

    try:
        with conn.cursor() as cursor:
            for p in pasien_lokal:
                # Query UPSERT berdasarkan no_rm / no_bpjs
                query = """
                    INSERT INTO `users` (nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        nama = VALUES(nama),
                        umur = VALUES(umur),
                        jenis_kelamin = VALUES(jenis_kelamin),
                        alamat = VALUES(alamat),
                        no_bpjs = VALUES(no_bpjs);
                """
                affected = cursor.execute(query, (
                    p["nama"],
                    p["umur"],
                    p["jenis_kelamin"],
                    p["alamat"],
                    p["no_rm"],
                    p["no_bpjs"]
                ))
                if affected == 1:
                    terproses += 1  # Baris baru masuk
                elif affected == 2:
                    diperbarui += 1  # Baris terupdate

            conn.commit()

        total = len(pasien_lokal)
        return True, (
            f"Transfer Selesai Berhasil!\n"
            f"• Total Data Lokal Diproses: {total} data\n"
            f"• Data Baru Diunggah: {terproses} pasien\n"
            f"• Data Sudah Ada (Diperbarui): {diperbarui} pasien"
        )
    except Exception as e:
        conn.rollback()
        return False, f"Terjadi kesalahan saat mengunggah data: {str(e)}"
    finally:
        conn.close()


def transfer_online_ke_lokal():
    """
    Mengunduh data dari database online (MySQL) ke database lokal (SQLite).
    Data baru akan dimasukkan ke SQLite, dan data yang sudah ada akan disinkronkan.
    """
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs FROM `users` ORDER BY id ASC")
            online_data = cursor.fetchall()
    except Exception as e:
        conn.close()
        return False, f"Gagal mengambil data dari server online: {str(e)}"
    finally:
        conn.close()

    if not online_data:
        return True, "Database online masih kosong, tidak ada data untuk diunduh."

    # Masukkan ke SQLite lokal
    conn_sqlite = database.get_connection()
    cursor_sqlite = conn_sqlite.cursor()
    baru = 0
    diupdate = 0

    try:
        for p in online_data:
            # Cek apakah No. RM atau No. BPJS sudah ada di SQLite
            cursor_sqlite.execute("SELECT id FROM users WHERE no_rm = ? OR no_bpjs = ?", (p["no_rm"], p["no_bpjs"]))
            ada = cursor_sqlite.fetchone()

            if ada:
                cursor_sqlite.execute(
                    """UPDATE users
                       SET nama = ?, umur = ?, jenis_kelamin = ?, alamat = ?, no_rm = ?, no_bpjs = ?
                       WHERE id = ?""",
                    (p["nama"], p["umur"], p["jenis_kelamin"], p["alamat"], p["no_rm"], p["no_bpjs"], ada["id"])
                )
                diupdate += 1
            else:
                cursor_sqlite.execute(
                    """INSERT INTO users (nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (p["nama"], p["umur"], p["jenis_kelamin"], p["alamat"], p["no_rm"], p["no_bpjs"])
                )
                baru += 1

        conn_sqlite.commit()
        total = len(online_data)
        return True, (
            f"Download Data Selesai Berhasil!\n"
            f"• Total Data Online Diterima: {total} data\n"
            f"• Data Baru Disimpan ke Lokal: {baru} pasien\n"
            f"• Data Lokal Diperbarui: {diupdate} pasien"
        )
    except Exception as e:
        conn_sqlite.rollback()
        return False, f"Gagal menyimpan data ke database lokal: {str(e)}"
    finally:
        conn_sqlite.close()


def sync_dua_arah():
    """
    Sinkronisasi dua arah (Bidirectional Sync):
    1. Tarik data dari online ke lokal
    2. Unggah data dari lokal ke online
    Kedua database akan memiliki data yang identik dan lengkap.
    """
    # Langkah 1: Tarik dari online ke lokal
    ok_down, msg_down = transfer_online_ke_lokal()
    if not ok_down:
        return False, f"Sinkronisasi Gagal saat mengambil data online:\n{msg_down}"

    # Langkah 2: Unggah kembali semua dari lokal ke online
    ok_up, msg_up = transfer_lokal_ke_online()
    if not ok_up:
        return False, f"Sinkronisasi Gagal saat mengunggah data ke online:\n{msg_up}"

    # Hitung total sekarang
    stats_lokal = database.get_statistics()
    return True, (
        f"Sinkronisasi Dua Arah Berhasil!\n\n"
        f"Data pada Penyimpanan Lokal (SQLite) dan Online (MySQL) kini telah identik.\n"
        f"Total Data Terdaftar: {stats_lokal['total']} Pasien"
    )
