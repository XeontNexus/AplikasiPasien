# Sistem Informasi & Rekam Medis Pasien BPJS

Aplikasi desktop modern berbasis Python & Tkinter untuk manajemen data dan rekam medis pasien BPJS pada Fasilitas Kesehatan Tingkat Pertama (FKTP), klinik, maupun praktik mandiri.

## ✨ Fitur Utama
- **Antarmuka Modern & Responsif**: Menggunakan tema medis kontemporer (*Clean Medical Slate & Indigo*), dukungan High-DPI Windows agar tampilan tajam dan bebas buram pada resolusi laptop maupun desktop.
- **Penyimpanan Ganda (Dual-Storage Architecture)**:
  - 🏠 **Penyimpanan Lokal (SQLite)**: Berkas `data.db` cepat, mandiri, dan bekerja 100% tanpa internet (Offline-First).
  - ☁️ **Penyimpanan Online (MySQL / MariaDB)**: Terhubung ke server MySQL lokal (XAMPP/Laragon) maupun server cloud/hosting.
- **Fitur Transfer & Sinkronisasi Data**:
  - ⬆️ **Upload ke Online**: Mengunggah data lokal ke server MySQL dengan mekanisme UPSERT (mencegah duplikasi).
  - ⬇️ **Download ke Lokal**: Menarik data dari server MySQL ke database SQLite lokal.
  - 🔄 **Sinkronisasi Dua Arah**: Menyamakan data antara database lokal dan server online agar identik.
  - 🔌 **Uji Koneksi & Pengaturan**: Form konfigurasi host, port, user, password, dan database dengan tombol uji koneksi langsung.
- **Kartu Statistik Real-time**: Menampilkan total pasien, pasien pria, dan wanita langsung di header.
- **Operasi CRUD Lengkap**:
  - ➕ **Tambah Data**: Formulir terstruktur dengan validasi umur dan pencegahan duplikasi No. RM / No. BPJS.
  - ✏️ **Edit / Update Data**: Klik baris data pada tabel untuk memuat data dan simpan perubahan.
  - 🗑️ **Hapus Data Aman**: Dilengkapi konfirmasi penghapusan dan pencadangan riwayat data terhapus ke folder `backups/`.
  - 📋 **Detail Pasien Modal**: Klik ganda baris tabel untuk melihat kartu detail identitas pasien.
- **Pencarian Cepat & Filter**: Pencarian instan berdasarkan Nama, No. RM, No. BPJS, atau Alamat.
- **Cetak Laporan PDF Profesional**: Dilengkapi kop fasilitas kesehatan resmi, tabel rapi, paginasi, dan kolom tanda tangan petugas rekam medis.
- **Pencadangan Data (Backup)**: Ekspor data ke berkas teks terstruktur di folder `backups/`.

## 📁 Struktur Berkas
- [app.py](file:///c:/abdulroni/projek%20etc/list%20berobat%20bpjs/app.py) : Antarmuka GUI utama (Tkinter / TTK) berorientasi objek (`AplikasiPasienBPJS`).
- [database.py](file:///c:/abdulroni/projek%20etc/list%20berobat%20bpjs/database.py) : Lapisan basis data lokal SQLite (`data.db`).
- [online_db.py](file:///c:/abdulroni/projek%20etc/list%20berobat%20bpjs/online_db.py) : Lapisan basis data online MySQL, transfer data, dan sinkronisasi.
- [config_db.json](file:///c:/abdulroni/projek%20etc/list%20berobat%20bpjs/config_db.json) : Berkas konfigurasi koneksi server MySQL online.
- [pdf_generator.py](file:///c:/abdulroni/projek%20etc/list%20berobat%20bpjs/pdf_generator.py) : Modul pembuat laporan PDF profesional berbasis ReportLab.
- [run.bat](file:///c:/abdulroni/projek%20etc/list%20berobat%20bpjs/run.bat) : Skrip peluncur cepat satu klik untuk pengguna Windows.

## 🚀 Cara Menjalankan
1. **Opsi 1**: Klik ganda (*double-click*) pada berkas `run.bat`.
2. **Opsi 2**: Buka terminal / Command Prompt lalu jalankan:
   ```bash
   python app.py
   ```
