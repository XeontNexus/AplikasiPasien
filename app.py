"""
====================================================================
Sistem Informasi & Rekam Medis Pasien BPJS Kesehatan
Aplikasi Desktop Manajemen Pasien FKTP / Klinik / Praktik Dokter
Fitur Dual-Storage: Lokal (SQLite) & Online (MySQL) + Transfer Data
====================================================================
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

# Import modul internal
import database
import pdf_generator
import online_db

# Atur DPI Awareness untuk Windows agar tampilan tajam dan tidak buram
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class AplikasiPasienBPJS:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Informasi Rekam Medis & Pasien BPJS")
        
        # Ukuran adaptif untuk layar sedang (laptop 1366x768 & 1280x720)
        self.root.geometry("1200x670")
        self.root.minsize(980, 540)

        # Variabel State
        self.selected_patient_id = None
        self.sort_var = tk.StringVar(value="waktu_desc")
        self.search_var = tk.StringVar()

        # Inisialisasi Database Lokal
        database.create_db()

        # Palet Warna Modern (Clean Medical Slate & Indigo Theme)
        self.colors = {
            "bg": "#f1f5f9",              # Slate 100
            "card_bg": "#ffffff",         # Putih Bersih
            "header_bg": "#0f2b48",       # Deep Navy Medical
            "header_fg": "#ffffff",
            "text_main": "#0f172a",       # Slate 900
            "text_muted": "#64748b",      # Slate 500
            "border": "#cbd5e1",          # Slate 300
            "primary": "#0284c7",         # Sky 600
            "primary_hover": "#0369a1",
            "success": "#059669",         # Emerald 600
            "success_hover": "#047857",
            "update_blue": "#2563eb",     # Royal Blue untuk Simpan Perubahan
            "update_hover": "#1d4ed8",
            "danger": "#dc2626",          # Red 600
            "danger_hover": "#b91c1c",
            "info": "#4f46e5",            # Indigo 600
            "info_hover": "#4338ca",
            "cloud": "#0284c7",           # Cloud Teal/Blue
            "row_even": "#ffffff",        # Baris Genap: Putih Bersih
            "row_odd": "#e0f2fe",         # Baris Ganjil: Biru Langit Lembut
            "row_select": "#bfdbfe"       # Baris Terpilih: Biru Muda
        }

        self.root.configure(bg=self.colors["bg"])

        # Konfigurasi Style ttk
        self.setup_styles()

        # Bangun Komponen Antarmuka
        self.create_header()
        self.create_main_content()
        self.create_status_bar()

        # Muat Data Awal
        self.muat_data()
        self.update_stats()

    def setup_styles(self):
        """Mengatur tema dan styling ttk."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        default_font = ("Segoe UI", 9)
        bold_font = ("Segoe UI", 9, "bold")

        # Style Treeview
        self.style.configure(
            "Custom.Treeview",
            background=self.colors["card_bg"],
            foreground=self.colors["text_main"],
            fieldbackground=self.colors["card_bg"],
            rowheight=30,
            font=default_font,
            borderwidth=0
        )
        self.style.map(
            "Custom.Treeview",
            background=[("selected", self.colors["row_select"])],
            foreground=[("selected", "#1e3a8a")]
        )

        # Style Heading Treeview
        self.style.configure(
            "Custom.Treeview.Heading",
            background=self.colors["header_bg"],
            foreground=self.colors["header_fg"],
            font=bold_font,
            relief="flat",
            padding=(6, 6)
        )
        self.style.map(
            "Custom.Treeview.Heading",
            background=[("active", "#163c63")]
        )

        # Style Combobox
        self.style.configure(
            "Custom.TCombobox",
            fieldbackground="#ffffff",
            background="#f8fafc",
            padding=3,
            font=default_font
        )

    def create_header(self):
        """Header atas yang ramping dan adaptif untuk layar sedang."""
        header_frame = tk.Frame(self.root, bg=self.colors["header_bg"], height=65)
        header_frame.pack(fill="x", side="top")

        inner_header = tk.Frame(header_frame, bg=self.colors["header_bg"])
        inner_header.pack(fill="both", expand=True, padx=18, pady=8)

        # Kolom Kiri: Judul & Subjudul
        title_frame = tk.Frame(inner_header, bg=self.colors["header_bg"])
        title_frame.pack(side="left", fill="y")

        lbl_title = tk.Label(
            title_frame,
            text="🏥  SISTEM INFORMASI & REKAM MEDIS PASIEN BPJS",
            font=("Segoe UI", 13, "bold"),
            fg="#ffffff",
            bg=self.colors["header_bg"]
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            title_frame,
            text="Klinik Pratama Rawat Jalan - Fasilitas Kesehatan Tingkat Pertama (FKTP)",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg=self.colors["header_bg"]
        )
        lbl_sub.pack(anchor="w", pady=(1, 0))

        # Kolom Kanan: Kartu Statistik & Tombol Cloud
        stats_frame = tk.Frame(inner_header, bg=self.colors["header_bg"])
        stats_frame.pack(side="right", fill="y")

        self.card_total = self.buat_stat_chip(stats_frame, "Total Pasien", "0")
        self.card_pria = self.buat_stat_chip(stats_frame, "Laki-laki", "0")
        self.card_wanita = self.buat_stat_chip(stats_frame, "Perempuan", "0")

        # Tombol Cepat Pengaturan Online di Header
        btn_cloud_hdr = tk.Button(
            stats_frame,
            text="☁️ DB Online",
            command=self.buka_dialog_sinkronisasi,
            font=("Segoe UI", 8, "bold"),
            bg="#163c63",
            fg="#67e8f9",
            activebackground="#234c75",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=4,
            bd=0
        )
        btn_cloud_hdr.pack(side="left", padx=(6, 0))

    def buat_stat_chip(self, parent, label_text, initial_value):
        """Membuat chip indikator statistik kompak di header."""
        frame = tk.Frame(parent, bg="#163c63", padx=10, pady=4, relief="flat", highlightbackground="#234c75", highlightthickness=1)
        frame.pack(side="left", padx=4)

        lbl_val = tk.Label(frame, text=initial_value, font=("Segoe UI", 11, "bold"), fg="#ffffff", bg="#163c63")
        lbl_val.pack(anchor="center")

        lbl_txt = tk.Label(frame, text=label_text, font=("Segoe UI", 7), fg="#cbd5e1", bg="#163c63")
        lbl_txt.pack(anchor="center")

        return lbl_val

    def buat_validator_angka(self, max_length):
        """Membuat fungsi validasi real-time: hanya boleh angka dan dibatasi panjang maksimal."""
        def validator(new_val):
            if new_val == "":
                return True
            return new_val.isdigit() and len(new_val) <= max_length
        return self.root.register(validator)

    def create_main_content(self):
        """Membagi layar menjadi Panel Kiri (Form) dan Panel Kanan (Tabel & Aksi)."""
        content_frame = tk.Frame(self.root, bg=self.colors["bg"])
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # -------------------------------------------------------------
        # PANEL KIRI: Form Input (Ringkas, Rapi, Adaptif Layar Sedang)
        # -------------------------------------------------------------
        left_panel = tk.Frame(
            content_frame,
            bg=self.colors["card_bg"],
            width=390,
            padx=16,
            pady=12,
            relief="flat",
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        left_panel.pack(side="left", fill="y", padx=(0, 12))
        left_panel.pack_propagate(False)
        self.left_panel = left_panel

        # Header Form & Badge Status Mode
        form_title_frame = tk.Frame(left_panel, bg=self.colors["card_bg"])
        form_title_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            form_title_frame,
            text="Form Data Pasien",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(side="left")

        self.lbl_mode_badge = tk.Label(
            form_title_frame,
            text="Mode: Tambah Baru",
            font=("Segoe UI", 8, "bold"),
            fg="#059669",
            bg="#d1fae5",
            padx=6,
            pady=2
        )
        self.lbl_mode_badge.pack(side="right")

        self.inputs = {}

        # 1. NAMA LENGKAP PASIEN
        self.create_form_field(
            left_panel, "1. Nama Lengkap Pasien *", "nama",
            placeholder="Nama lengkap sesuai KTP"
        )

        # 2. ALAMAT DOMISILI
        self.create_form_field(
            left_panel, "2. Alamat Domisili *", "alamat",
            placeholder="Jl., RT/RW, Kelurahan, Kecamatan"
        )

        # 3. JENIS KELAMIN
        field_jk = tk.Frame(left_panel, bg=self.colors["card_bg"])
        field_jk.pack(fill="x", pady=(0, 6))

        tk.Label(
            field_jk,
            text="3. Jenis Kelamin *",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 2))

        self.combo_jk = ttk.Combobox(
            field_jk,
            values=["Laki-laki", "Perempuan"],
            state="readonly",
            style="Custom.TCombobox",
            font=("Segoe UI", 9)
        )
        self.combo_jk.set("Laki-laki")
        self.combo_jk.pack(fill="x", ipady=2)

        # Validator Real-time Input Angka & Batas Panjang Digit
        vcmd_umur = (self.buat_validator_angka(3), "%P")
        vcmd_rm = (self.buat_validator_angka(10), "%P")
        vcmd_bpjs = (self.buat_validator_angka(14), "%P")

        # 4. UMUR (Tahun) - Maksimal 3 Digit Angka
        field_umur = tk.Frame(left_panel, bg=self.colors["card_bg"])
        field_umur.pack(fill="x", pady=(0, 6))

        tk.Label(
            field_umur,
            text="4. Umur (Tahun, Maks 3 Digit) *",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 2))

        entry_umur = tk.Entry(
            field_umur,
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg=self.colors["text_main"],
            relief="flat",
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
            highlightthickness=1,
            validate="key",
            validatecommand=vcmd_umur
        )
        entry_umur.pack(fill="x", ipady=2)
        self.inputs["umur"] = entry_umur

        # 5. NO. REKAM MEDIS (RM) - Maksimal 10 Digit Angka
        field_rm = tk.Frame(left_panel, bg=self.colors["card_bg"])
        field_rm.pack(fill="x", pady=(0, 6))

        tk.Label(
            field_rm,
            text="5. No. Rekam Medis (Maks 10 Digit) *",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 2))

        entry_rm = tk.Entry(
            field_rm,
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg=self.colors["text_main"],
            relief="flat",
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
            highlightthickness=1,
            validate="key",
            validatecommand=vcmd_rm
        )
        entry_rm.pack(fill="x", ipady=2)
        self.inputs["no_rm"] = entry_rm

        # 6. NO. KARTU BPJS - Maksimal 14 Digit Angka
        field_bpjs = tk.Frame(left_panel, bg=self.colors["card_bg"])
        field_bpjs.pack(fill="x", pady=(0, 8))

        tk.Label(
            field_bpjs,
            text="6. No. BPJS (Maks 14 Digit) *",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 2))

        entry_bpjs = tk.Entry(
            field_bpjs,
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg=self.colors["text_main"],
            relief="flat",
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
            highlightthickness=1,
            validate="key",
            validatecommand=vcmd_bpjs
        )
        entry_bpjs.pack(fill="x", ipady=2)
        self.inputs["no_bpjs"] = entry_bpjs

        # Tombol Aksi Form (2 Baris Rapi, Bersih, Sesuai Permintaan)
        btn_frame = tk.Frame(left_panel, bg=self.colors["card_bg"])
        btn_frame.pack(fill="x", pady=(10, 0))

        # Baris 1: Tambah Data Baru & Simpan Perubahan (Tulisan Putih)
        row_btn1 = tk.Frame(btn_frame, bg=self.colors["card_bg"])
        row_btn1.pack(fill="x", pady=(0, 6))

        self.btn_tambah = tk.Button(
            row_btn1,
            text="➕  Tambah Data",
            command=self.aksi_tambah,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["success"],
            fg="#ffffff",
            activebackground=self.colors["success_hover"],
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5,
            bd=0
        )
        self.btn_tambah.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # Tombol SIMPAN PERUBAHAN: Tulisan PUTIH murni
        self.btn_update = tk.Button(
            row_btn1,
            text="✏️  Simpan Perubahan",
            command=self.aksi_update,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["update_blue"],
            fg="#ffffff",
            activebackground=self.colors["update_hover"],
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5,
            bd=0
        )
        self.btn_update.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Baris 2: Reset Form & HAPUS DATA (Warna Putih)
        row_btn2 = tk.Frame(btn_frame, bg=self.colors["card_bg"])
        row_btn2.pack(fill="x")

        self.btn_reset = tk.Button(
            row_btn2,
            text="🔄  Reset Form",
            command=self.bersihkan_form,
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#334155",
            activebackground="#e2e8f0",
            activeforeground="#0f172a",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=4
        )
        self.btn_reset.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # Tombol HAPUS DATA: WARNA PUTIH
        self.btn_hapus = tk.Button(
            row_btn2,
            text="🗑️  Hapus Data",
            command=self.aksi_hapus,
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",                   # WARNA PUTIH
            fg=self.colors["danger"],       # Teks Merah
            activebackground="#fee2e2",
            activeforeground="#b91c1c",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=4,
            highlightbackground=self.colors["danger"],
            highlightcolor=self.colors["danger"]
        )
        self.btn_hapus.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # -------------------------------------------------------------
        # PANEL KANAN: Toolbar Pencarian & Tabel Data Pasien
        # -------------------------------------------------------------
        right_panel = tk.Frame(content_frame, bg=self.colors["bg"])
        right_panel.pack(side="right", fill="both", expand=True)

        # Toolbar Atas
        toolbar_frame = tk.Frame(
            right_panel,
            bg=self.colors["card_bg"],
            padx=12,
            pady=8,
            relief="flat",
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        toolbar_frame.pack(fill="x", pady=(0, 10))

        # Kotak Pencarian
        search_box = tk.Frame(toolbar_frame, bg=self.colors["card_bg"])
        search_box.pack(side="left", fill="x", expand=True)

        lbl_cari_icon = tk.Label(
            search_box,
            text="🔍",
            font=("Segoe UI", 10),
            bg=self.colors["card_bg"],
            fg=self.colors["text_muted"]
        )
        lbl_cari_icon.pack(side="left", padx=(0, 4))

        self.entry_search = tk.Entry(
            search_box,
            textvariable=self.search_var,
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg=self.colors["text_main"],
            relief="flat",
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
            highlightthickness=1
        )
        self.entry_search.pack(side="left", fill="x", expand=True, ipady=3, padx=(0, 4))
        self.entry_search.bind("<KeyRelease>", lambda e: self.muat_data())

        btn_clear_search = tk.Button(
            search_box,
            text="✕",
            font=("Segoe UI", 8, "bold"),
            bg="#e2e8f0",
            fg="#475569",
            activebackground="#cbd5e1",
            relief="flat",
            cursor="hand2",
            command=self.reset_pencarian,
            width=3
        )
        btn_clear_search.pack(side="left", padx=(0, 8))

        # Pengurutan
        lbl_sort = tk.Label(
            toolbar_frame,
            text="Urutkan:",
            font=("Segoe UI", 8),
            bg=self.colors["card_bg"],
            fg=self.colors["text_muted"]
        )
        lbl_sort.pack(side="left", padx=(0, 4))

        self.sort_options = {
            "Terbaru (ID Terakhir)": "waktu_desc",
            "Terlama (ID Awal)": "waktu_asc",
            "Nama Pasien (A - Z)": "nama_asc",
            "Nama Pasien (Z - A)": "nama_desc"
        }
        self.combo_sort = ttk.Combobox(
            toolbar_frame,
            values=list(self.sort_options.keys()),
            state="readonly",
            style="Custom.TCombobox",
            width=16,
            font=("Segoe UI", 8)
        )
        self.combo_sort.set("Terbaru (ID Terakhir)")
        self.combo_sort.pack(side="left", padx=(0, 8))
        self.combo_sort.bind("<<ComboboxSelected>>", self.on_sort_changed)

        # Tombol Aksi Kanan Toolbar: Transfer Cloud, PDF, Backup
        btn_cloud = tk.Button(
            toolbar_frame,
            text="☁️ Transfer Data",
            command=self.buka_dialog_sinkronisasi,
            font=("Segoe UI", 8, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            bd=0
        )
        btn_cloud.pack(side="right", padx=(4, 0))

        btn_pdf = tk.Button(
            toolbar_frame,
            text="📄 Cetak PDF",
            command=self.aksi_cetak_pdf,
            font=("Segoe UI", 8, "bold"),
            bg="#0f766e",
            fg="#ffffff",
            activebackground="#115e59",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            bd=0
        )
        btn_pdf.pack(side="right", padx=(4, 0))

        btn_backup = tk.Button(
            toolbar_frame,
            text="💾 Backup",
            command=self.aksi_backup,
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["info"],
            fg="#ffffff",
            activebackground=self.colors["info_hover"],
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            bd=0
        )
        btn_backup.pack(side="right")

        # Kontainer Tabel Pasien (Card View)
        table_card = tk.Frame(
            right_panel,
            bg=self.colors["card_bg"],
            relief="flat",
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        table_card.pack(fill="both", expand=True)

        # Definisi Kolom Treeview Sesuai Urutan Baru
        columns = ("id", "nama", "alamat", "jk", "umur", "no_rm", "no_bpjs")
        self.tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse"
        )

        headers = [
            ("id", "ID", 45, "center"),
            ("nama", "Nama Lengkap Pasien", 170, "w"),
            ("alamat", "Alamat Domisili", 210, "w"),
            ("jk", "Gender", 85, "center"),
            ("umur", "Umur", 65, "center"),
            ("no_rm", "No. RM", 95, "center"),
            ("no_bpjs", "No. BPJS", 130, "center")
        ]

        for col_id, text, width, anchor in headers:
            self.tree.heading(col_id, text=text, command=lambda c=col_id: self.sort_by_column(c))
            self.tree.column(col_id, width=width, anchor=anchor, minwidth=45)

        # Scrollbar
        self.vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")

        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        # WARNA BARIS BERBEDA (GENAP & GANJIL):
        # Baris Genap = Putih Bersih (#ffffff)
        # Baris Ganjil = Biru Langit Lembut (#e0f2fe)
        self.tree.tag_configure("even", background=self.colors["row_even"], foreground=self.colors["text_main"])
        self.tree.tag_configure("odd", background=self.colors["row_odd"], foreground=self.colors["text_main"])

        # Event Binding
        self.tree.bind("<<TreeviewSelect>>", self.on_row_selected)
        self.tree.bind("<Double-1>", self.on_row_double_click)

        # Global Click Binding (Deselect & Kosongkan Form jika klik di tempat lain)
        self.root.bind_all("<Button-1>", self.on_global_click, add="+")

    def is_inside_left_panel(self, widget):
        """Mengecek apakah widget berada di dalam panel form kiri (sidebar) atau dropdown combobox."""
        if widget is None:
            return False
        # Dukungan jika widget adalah popup/drop-down combobox
        if "popdown" in str(widget).lower():
            return True
        curr = widget
        target = getattr(self, "left_panel", None)
        while curr is not None:
            if curr == target:
                return True
            try:
                curr = curr.master
            except Exception:
                break
        return False

    def on_global_click(self, event):
        """
        Mendeteksi klik di luar form dan luar baris tabel.
        Jika data pasien sedang dipilih di sidebar dan pengguna mengklik tempat lain
        (seperti area kosong tabel, background, search box, header, toolbar, dll),
        maka data pasien di sidebar akan dikosongkan (bukan terhapus dari database)
        untuk menghindari ketidaksengajaan perubahan data.
        """
        # Abaikan klik pada jendela dialog/popup (misal: Detail Pasien, Sinkronisasi, Messagebox)
        try:
            if event.widget.winfo_toplevel() != self.root:
                return
        except Exception:
            return

        # Jika klik di dalam sidebar form, biarkan pengguna mengedit atau menekan tombol form
        if self.is_inside_left_panel(event.widget):
            return

        # Abaikan klik pada scrollbar tabel
        if event.widget in (getattr(self, "vsb", None), getattr(self, "hsb", None)):
            return

        # Jika klik pada widget tabel pasien (self.tree)
        if event.widget == self.tree:
            region = self.tree.identify_region(event.x, event.y)
            row_id = self.tree.identify_row(event.y)
            # Jika klik tepat pada baris data, biarkan seleksi tabel bekerja normal
            if row_id and region in ("cell", "tree"):
                return
            # Jika klik di area kosong tabel / bukan baris data
            if self.selected_patient_id is not None or self.tree.selection():
                self.bersihkan_form()
            return

        # Jika klik di tempat lain mana pun (background, search box, header, toolbar)
        # dan saat itu data pasien sedang aktif di form
        if self.selected_patient_id is not None or self.tree.selection():
            self.bersihkan_form()

    def create_form_field(self, parent, label_text, key, placeholder=""):
        """Fungsi helper untuk membuat label dan input field form secara rapi."""
        field_frame = tk.Frame(parent, bg=self.colors["card_bg"])
        field_frame.pack(fill="x", pady=(0, 7))

        tk.Label(
            field_frame,
            text=label_text,
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 2))

        entry = tk.Entry(
            field_frame,
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg=self.colors["text_main"],
            relief="flat",
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
            highlightthickness=1
        )
        entry.pack(fill="x", ipady=3)
        self.inputs[key] = entry

    def create_status_bar(self):
        """Status bar bawah dengan informasi live dan total pasien."""
        status_frame = tk.Frame(self.root, bg="#e2e8f0", height=28, padx=16)
        status_frame.pack(fill="x", side="bottom")

        self.lbl_status = tk.Label(
            status_frame,
            text="Siap",
            font=("Segoe UI", 8),
            bg="#e2e8f0",
            fg="#475569"
        )
        self.lbl_status.pack(side="left", pady=4)

        self.lbl_counter = tk.Label(
            status_frame,
            text="Menampilkan 0 pasien",
            font=("Segoe UI", 8, "bold"),
            bg="#e2e8f0",
            fg="#0f2b48"
        )
        self.lbl_counter.pack(side="right", pady=4)

    def set_status(self, text, is_error=False):
        """Memperbarui teks status bar."""
        color = "#dc2626" if is_error else "#0f2b48"
        self.lbl_status.config(text=f"●  {text}", fg=color)

    # -------------------------------------------------------------
    # LOGIKA OPERASI DATA & EVENT HANDLER
    # -------------------------------------------------------------
    def muat_data(self):
        """Mengambil data dari database dan memberi warna selang-seling genap dan ganjil."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        cari = self.search_var.get().strip()
        sort_mode = self.sort_var.get()

        pasien_list = database.get_all_patients(cari=cari, sort_mode=sort_mode)

        for idx, p in enumerate(pasien_list, 1):
            tag = "even" if idx % 2 == 0 else "odd"
            values = (
                p["id"],
                p["nama"],
                p["alamat"],
                p["jenis_kelamin"],
                f"{p['umur']} th",
                p["no_rm"],
                p["no_bpjs"]
            )
            self.tree.insert("", "end", iid=str(p["id"]), values=values, tags=(tag,))

        total_ditampilkan = len(pasien_list)
        if cari:
            self.lbl_counter.config(text=f"Ditemukan {total_ditampilkan} pasien sesuai pencarian '{cari}'")
        else:
            self.lbl_counter.config(text=f"Total: {total_ditampilkan} pasien terdaftar")

    def update_stats(self):
        """Memperbarui kartu statistik di header."""
        stats = database.get_statistics()
        self.card_total.config(text=str(stats["total"]))
        self.card_pria.config(text=str(stats["pria"]))
        self.card_wanita.config(text=str(stats["wanita"]))

    def on_sort_changed(self, event=None):
        """Saat pilihan combobox urutan berubah."""
        selected_text = self.combo_sort.get()
        mode = self.sort_options.get(selected_text, "waktu_desc")
        self.sort_var.set(mode)
        self.muat_data()

    def sort_by_column(self, col):
        """Pengurutan cepat saat kolom header tabel diklik."""
        if col == "nama":
            current = self.sort_var.get()
            new_mode = "nama_desc" if current == "nama_asc" else "nama_asc"
            self.sort_var.set(new_mode)
            self.combo_sort.set("Nama Pasien (A - Z)" if new_mode == "nama_asc" else "Nama Pasien (Z - A)")
        elif col in ("id", "no_rm"):
            current = self.sort_var.get()
            new_mode = "waktu_asc" if current == "waktu_desc" else "waktu_desc"
            self.sort_var.set(new_mode)
            self.combo_sort.set("Terlama (ID Awal)" if new_mode == "waktu_asc" else "Terbaru (ID Terakhir)")
        self.muat_data()

    def reset_pencarian(self):
        """Menghapus kata kunci pencarian dan mengembalikan semua data."""
        self.search_var.set("")
        self.muat_data()
        self.set_status("Filter pencarian dibersihkan.")

    def on_row_selected(self, event=None):
        """Saat pengguna mengklik baris di tabel, masukkan datanya ke form."""
        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        patient = database.get_patient_by_id(item_id)
        if not patient:
            return

        self.selected_patient_id = patient["id"]

        self.inputs["nama"].delete(0, tk.END)
        self.inputs["nama"].insert(0, str(patient["nama"]))

        self.inputs["alamat"].delete(0, tk.END)
        self.inputs["alamat"].insert(0, str(patient["alamat"]))

        self.combo_jk.set(patient["jenis_kelamin"])

        self.inputs["umur"].delete(0, tk.END)
        self.inputs["umur"].insert(0, str(patient["umur"])[:3])

        self.inputs["no_rm"].delete(0, tk.END)
        self.inputs["no_rm"].insert(0, str(patient["no_rm"])[:10])

        self.inputs["no_bpjs"].delete(0, tk.END)
        self.inputs["no_bpjs"].insert(0, str(patient["no_bpjs"])[:14])

        # Pastikan validasi key tetap aktif
        self.inputs["umur"].config(validate="key")
        self.inputs["no_rm"].config(validate="key")
        self.inputs["no_bpjs"].config(validate="key")

        self.lbl_mode_badge.config(
            text=f"Mode: Edit (ID #{self.selected_patient_id})",
            fg="#b45309",
            bg="#fef3c7"
        )
        self.set_status(f"Memilih data pasien: {patient['nama']} (No. RM: {patient['no_rm']})")

    def on_row_double_click(self, event=None):
        """Menampilkan dialog rincian lengkap pasien saat baris diklik ganda."""
        selected = self.tree.selection()
        if not selected:
            return
        patient = database.get_patient_by_id(selected[0])
        if not patient:
            return

        dlg = tk.Toplevel(self.root)
        dlg.title(f"Detail Pasien - {patient['nama']}")
        dlg.geometry("450x370")
        dlg.resizable(False, False)
        dlg.configure(bg="#ffffff")
        dlg.transient(self.root)
        dlg.grab_set()

        d_head = tk.Frame(dlg, bg=self.colors["header_bg"], padx=15, pady=10)
        d_head.pack(fill="x")
        tk.Label(
            d_head,
            text=f"📋 Kartu Identitas Pasien",
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg=self.colors["header_bg"]
        ).pack(anchor="w")

        d_body = tk.Frame(dlg, bg="#ffffff", padx=20, pady=15)
        d_body.pack(fill="both", expand=True)

        rows = [
            ("ID Pasien", str(patient["id"])),
            ("Nama Lengkap", str(patient["nama"])),
            ("Alamat Domisili", str(patient["alamat"])),
            ("Jenis Kelamin", str(patient["jenis_kelamin"])),
            ("Umur", f"{patient['umur']} Tahun"),
            ("No. Rekam Medis", str(patient["no_rm"])),
            ("No. BPJS Kesehatan", str(patient["no_bpjs"])),
        ]

        for label, val in rows:
            f = tk.Frame(d_body, bg="#ffffff")
            f.pack(fill="x", pady=3)
            tk.Label(f, text=f"{label}:", font=("Segoe UI", 9, "bold"), width=16, anchor="w", bg="#ffffff", fg="#475569").pack(side="left")
            tk.Label(f, text=val, font=("Segoe UI", 9), anchor="w", bg="#ffffff", fg="#0f172a").pack(side="left", fill="x", expand=True)

        tk.Button(
            d_body,
            text="Tutup",
            command=dlg.destroy,
            font=("Segoe UI", 9, "bold"),
            bg="#0f2b48",
            fg="#ffffff",
            relief="flat",
            pady=4,
            cursor="hand2"
        ).pack(side="bottom", fill="x", pady=(10, 0))

    def validasi_input(self):
        """Memvalidasi field formulir sebelum penambahan atau pembaruan."""
        nama = self.inputs["nama"].get().strip()
        alamat = self.inputs["alamat"].get().strip()
        jk = self.combo_jk.get().strip()
        umur_str = self.inputs["umur"].get().strip()
        no_rm = self.inputs["no_rm"].get().strip()
        no_bpjs = self.inputs["no_bpjs"].get().strip()

        if not all([nama, alamat, jk, umur_str, no_rm, no_bpjs]):
            messagebox.showwarning("Form Belum Lengkap", "Semua kolom bertanda bintang (*) wajib diisi!")
            return None

        # 1. Validasi Umur (Maksimal 3 Digit Angka)
        if not umur_str.isdigit():
            messagebox.showwarning("Format Salah", "Kolom Umur hanya boleh berisi angka (tidak bisa huruf)!")
            self.inputs["umur"].focus_set()
            return None

        if len(umur_str) > 3:
            messagebox.showwarning("Format Salah", "Umur maksimal 3 digit angka!")
            self.inputs["umur"].focus_set()
            return None

        umur = int(umur_str)
        if umur <= 0 or umur > 150:
            messagebox.showwarning("Format Salah", "Nilai umur tidak valid (harus antara 1 hingga 150 tahun)!")
            self.inputs["umur"].focus_set()
            return None

        # 2. Validasi No. Rekam Medis (Maksimal 10 Digit Angka)
        if not no_rm.isdigit():
            messagebox.showwarning("Format Salah", "No. Rekam Medis hanya boleh berisi angka (tidak bisa huruf)!")
            self.inputs["no_rm"].focus_set()
            return None

        if len(no_rm) > 10:
            messagebox.showwarning("Format Salah", "No. Rekam Medis maksimal 10 digit angka!")
            self.inputs["no_rm"].focus_set()
            return None

        # 3. Validasi No. BPJS Kesehatan (Maksimal 14 Digit Angka)
        if not no_bpjs.isdigit():
            messagebox.showwarning("Format Salah", "No. BPJS Kesehatan hanya boleh berisi angka (tidak bisa huruf)!")
            self.inputs["no_bpjs"].focus_set()
            return None

        if len(no_bpjs) > 14:
            messagebox.showwarning("Format Salah", "No. BPJS Kesehatan maksimal 14 digit angka!")
            self.inputs["no_bpjs"].focus_set()
            return None

        return {
            "nama": nama,
            "alamat": alamat,
            "jenis_kelamin": jk,
            "umur": umur,
            "no_rm": no_rm,
            "no_bpjs": no_bpjs
        }

    def bersihkan_form(self):
        """Mengosongkan seluruh kolom input dan reset state form."""
        self.selected_patient_id = None
        for entry in self.inputs.values():
            entry.delete(0, tk.END)
        self.combo_jk.set("Laki-laki")

        self.lbl_mode_badge.config(
            text="Mode: Tambah Baru",
            fg="#059669",
            bg="#d1fae5"
        )
        self.tree.selection_remove(self.tree.selection())
        self.set_status("Form siap untuk entri data baru.")

    def aksi_tambah(self):
        """Menambahkan data pasien baru ke database."""
        data = self.validasi_input()
        if not data:
            return

        pesan_duplikat = database.is_data_exists(data["no_rm"], data["no_bpjs"])
        if pesan_duplikat:
            messagebox.showerror("Data Duplikat", pesan_duplikat)
            return

        try:
            new_id = database.tambah_pasien(
                data["nama"], data["umur"], data["jenis_kelamin"],
                data["alamat"], data["no_rm"], data["no_bpjs"]
            )
            messagebox.showinfo("Berhasil", f"Pasien '{data['nama']}' berhasil ditambahkan!")
            self.bersihkan_form()
            self.muat_data()
            self.update_stats()
            self.set_status(f"Sukses menambahkan pasien baru: {data['nama']}")
        except Exception as e:
            messagebox.showerror("Kesalahan Database", f"Gagal menambahkan data:\n{str(e)}")

    def aksi_update(self):
        """Memperbarui data pasien yang sedang dipilih (Tulisan Simpan Perubahan Putih)."""
        if not self.selected_patient_id:
            messagebox.showinfo(
                "Pilih Pasien Terlebih Dahulu",
                "Silakan klik salah satu baris data pasien pada tabel di sebelah kanan terlebih dahulu untuk mengedit/memperbarui data."
            )
            return

        data = self.validasi_input()
        if not data:
            return

        pesan_duplikat = database.is_data_exists(data["no_rm"], data["no_bpjs"], exclude_id=self.selected_patient_id)
        if pesan_duplikat:
            messagebox.showerror("Data Duplikat", pesan_duplikat)
            return

        try:
            database.update_pasien(
                self.selected_patient_id,
                data["nama"], data["umur"], data["jenis_kelamin"],
                data["alamat"], data["no_rm"], data["no_bpjs"]
            )
            messagebox.showinfo("Berhasil", "Data pasien berhasil diperbarui!")
            self.bersihkan_form()
            self.muat_data()
            self.update_stats()
            self.set_status(f"Sukses memperbarui data pasien: {data['nama']}")
        except Exception as e:
            messagebox.showerror("Kesalahan Database", f"Gagal memperbarui data:\n{str(e)}")

    def aksi_hapus(self):
        """Menghapus data pasien terpilih (Tombol Putih Bersih)."""
        if not self.selected_patient_id:
            messagebox.showinfo(
                "Pilih Pasien Terlebih Dahulu",
                "Silakan klik salah satu data pasien pada tabel di sebelah kanan yang ingin Anda hapus."
            )
            return

        patient = database.get_patient_by_id(self.selected_patient_id)
        if not patient:
            messagebox.showerror("Error", "Data pasien tidak ditemukan di database.")
            return

        konfirmasi = messagebox.askyesno(
            "Konfirmasi Hapus Data",
            f"Apakah Anda yakin ingin menghapus data pasien berikut?\n\n"
            f"• Nama: {patient['nama']}\n"
            f"• No. RM: {patient['no_rm']}\n"
            f"• No. BPJS: {patient['no_bpjs']}\n\n"
            "Data yang terhapus akan otomatis dicadangkan ke folder 'backups'.",
            icon="warning"
        )

        if konfirmasi:
            try:
                database.hapus_pasien(self.selected_patient_id)
                messagebox.showinfo("Terhapus", f"Data pasien '{patient['nama']}' berhasil dihapus.")
                self.bersihkan_form()
                self.muat_data()
                self.update_stats()
                self.set_status(f"Data pasien '{patient['nama']}' telah dihapus.")
            except Exception as e:
                messagebox.showerror("Kesalahan", f"Gagal menghapus data: {str(e)}")

    def aksi_cetak_pdf(self):
        """Mencetak daftar rekap pasien ke dokumen PDF profesional."""
        pdf_filename = "daftar_pasien.pdf"
        sukses, hasil = pdf_generator.cetak_daftar_pasien_pdf(pdf_filename)

        if sukses:
            konfirmasi = messagebox.askyesno(
                "Cetak PDF Berhasil",
                f"Laporan berhasil dibuat ke '{pdf_filename}'.\n\nApakah Anda ingin langsung membuka file PDF tersebut sekarang?"
            )
            self.set_status(f"File PDF berhasil dibuat: {pdf_filename}")
            if konfirmasi:
                try:
                    os.startfile(pdf_filename)
                except Exception as e:
                    messagebox.showinfo("Buka File", f"Silakan buka file secara manual di folder:\n{os.path.abspath(pdf_filename)}")
        else:
            messagebox.showerror("Gagal Mencetak PDF", hasil)
            self.set_status("Gagal mencetak PDF.", is_error=True)

    def aksi_backup(self):
        """Mencadangkan seluruh data pasien ke file teks."""
        try:
            backup_path, jumlah = database.backup_database()
            messagebox.showinfo(
                "Backup Selesai",
                f"Seluruh data pasien ({jumlah} data) berhasil dicadangkan ke:\n\n{backup_path}"
            )
            self.set_status(f"Backup berhasil dibuat: {os.path.basename(backup_path)}")
        except Exception as e:
            messagebox.showerror("Gagal Backup", f"Terjadi kesalahan saat membackup data:\n{str(e)}")
            self.set_status("Gagal membackup data.", is_error=True)

    # -------------------------------------------------------------
    # DIALOG TRANSFER & SINKRONISASI DATABASE ONLINE (MYSQL)
    # -------------------------------------------------------------
    def buka_dialog_sinkronisasi(self):
        """Membuka modal dialog Transfer Data & Pengaturan Database Online MySQL."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Transfer & Sinkronisasi Database Online (MySQL)")
        dlg.geometry("540x580")
        dlg.minsize(500, 520)
        dlg.configure(bg="#f8fafc")
        dlg.transient(self.root)
        dlg.grab_set()

        # Header Dialog
        head = tk.Frame(dlg, bg="#0f2b48", padx=16, pady=12)
        head.pack(fill="x")

        tk.Label(
            head,
            text="☁️  Transfer & Sinkronisasi Database Online",
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#0f2b48"
        ).pack(anchor="w")

        tk.Label(
            head,
            text="Penyimpanan Ganda: Database Lokal (SQLite) ⇄ Server Online (MySQL)",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#0f2b48"
        ).pack(anchor="w", pady=(2, 0))

        # Konten Utama Dialog (Notebook / Tab)
        body = tk.Frame(dlg, bg="#f8fafc", padx=16, pady=12)
        body.pack(fill="both", expand=True)

        # CARD 1: AKSI TRANSFER DATA
        card_transfer = tk.LabelFrame(
            body,
            text="  Aksi Transfer Data  ",
            font=("Segoe UI", 9, "bold"),
            fg="#0f172a",
            bg="#ffffff",
            padx=12,
            pady=10,
            relief="solid",
            bd=1
        )
        card_transfer.pack(fill="x", pady=(0, 12))

        # Opsi 1: Upload Lokal -> Online
        f_up = tk.Frame(card_transfer, bg="#ffffff")
        f_up.pack(fill="x", pady=4)
        tk.Label(
            f_up,
            text="⬆️ Upload ke Online:\n   Kirim data lokal (SQLite) ke server MySQL",
            font=("Segoe UI", 8),
            justify="left",
            bg="#ffffff",
            fg="#334155"
        ).pack(side="left")

        def proses_upload():
            self.set_status("Sedang mentransfer data ke MySQL online...")
            dlg.update()
            ok, msg = online_db.transfer_lokal_ke_online()
            if ok:
                messagebox.showinfo("Upload Berhasil", msg, parent=dlg)
                self.set_status("Transfer ke online berhasil.")
            else:
                messagebox.showerror("Upload Gagal", msg, parent=dlg)
                self.set_status("Transfer ke online gagal.", is_error=True)

        btn_up = tk.Button(
            f_up,
            text="Upload ke MySQL",
            command=proses_upload,
            font=("Segoe UI", 8, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4
        )
        btn_up.pack(side="right")

        # Divider
        tk.Frame(card_transfer, bg="#e2e8f0", height=1).pack(fill="x", pady=6)

        # Opsi 2: Download Online -> Lokal
        f_down = tk.Frame(card_transfer, bg="#ffffff")
        f_down.pack(fill="x", pady=4)
        tk.Label(
            f_down,
            text="⬇️ Download ke Lokal:\n   Tarik data dari server MySQL ke database lokal",
            font=("Segoe UI", 8),
            justify="left",
            bg="#ffffff",
            fg="#334155"
        ).pack(side="left")

        def proses_download():
            self.set_status("Sedang mengambil data dari MySQL online...")
            dlg.update()
            ok, msg = online_db.transfer_online_ke_lokal()
            if ok:
                self.muat_data()
                self.update_stats()
                messagebox.showinfo("Download Berhasil", msg, parent=dlg)
                self.set_status("Download dari online berhasil.")
            else:
                messagebox.showerror("Download Gagal", msg, parent=dlg)
                self.set_status("Download dari online gagal.", is_error=True)

        btn_down = tk.Button(
            f_down,
            text="Download ke Lokal",
            command=proses_download,
            font=("Segoe UI", 8, "bold"),
            bg="#4f46e5",
            fg="#ffffff",
            activebackground="#4338ca",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4
        )
        btn_down.pack(side="right")

        # Divider
        tk.Frame(card_transfer, bg="#e2e8f0", height=1).pack(fill="x", pady=6)

        # Opsi 3: Sinkronisasi Dua Arah
        f_sync = tk.Frame(card_transfer, bg="#ffffff")
        f_sync.pack(fill="x", pady=4)
        tk.Label(
            f_sync,
            text="🔄 Sinkronisasi 2 Arah:\n   Gabungkan data kedua database agar identik",
            font=("Segoe UI", 8),
            justify="left",
            bg="#ffffff",
            fg="#334155"
        ).pack(side="left")

        def proses_sync():
            self.set_status("Sedang melakukan sinkronisasi dua arah...")
            dlg.update()
            ok, msg = online_db.sync_dua_arah()
            if ok:
                self.muat_data()
                self.update_stats()
                messagebox.showinfo("Sinkronisasi Selesai", msg, parent=dlg)
                self.set_status("Sinkronisasi dua arah selesai.")
            else:
                messagebox.showerror("Sinkronisasi Gagal", msg, parent=dlg)
                self.set_status("Sinkronisasi dua arah gagal.", is_error=True)

        btn_sync = tk.Button(
            f_sync,
            text="Sinkronkan 2 Arah",
            command=proses_sync,
            font=("Segoe UI", 8, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#047857",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4
        )
        btn_sync.pack(side="right")

        # CARD 2: PENGATURAN KONEKSI DATABASE ONLINE (MYSQL)
        card_cfg = tk.LabelFrame(
            body,
            text="  Pengaturan Server MySQL Online  ",
            font=("Segoe UI", 9, "bold"),
            fg="#0f172a",
            bg="#ffffff",
            padx=12,
            pady=10,
            relief="solid",
            bd=1
        )
        card_cfg.pack(fill="both", expand=True)

        current_cfg = online_db.load_config()
        entries_cfg = {}

        fields_cfg = [
            ("Host / IP Server:", "host", current_cfg.get("host", "localhost")),
            ("Port (Default 3306):", "port", str(current_cfg.get("port", 3306))),
            ("Nama Database:", "database", current_cfg.get("database", "db_pasien_bpjs")),
            ("Username Database:", "user", current_cfg.get("user", "root")),
            ("Password Database:", "password", current_cfg.get("password", ""))
        ]

        for idx, (label_txt, key, val) in enumerate(fields_cfg):
            f_row = tk.Frame(card_cfg, bg="#ffffff")
            f_row.pack(fill="x", pady=2)

            tk.Label(
                f_row,
                text=label_txt,
                font=("Segoe UI", 8, "bold"),
                width=18,
                anchor="w",
                bg="#ffffff",
                fg="#475569"
            ).pack(side="left")

            show_char = "*" if key == "password" else ""
            ent = tk.Entry(
                f_row,
                font=("Segoe UI", 9),
                bg="#f8fafc",
                fg="#0f172a",
                relief="flat",
                highlightbackground="#cbd5e1",
                highlightcolor="#0284c7",
                highlightthickness=1,
                show=show_char
            )
            ent.insert(0, str(val))
            ent.pack(side="right", fill="x", expand=True, ipady=2)
            entries_cfg[key] = ent

        # Tombol Tes Koneksi & Simpan Pengaturan
        f_cfg_btn = tk.Frame(card_cfg, bg="#ffffff")
        f_cfg_btn.pack(fill="x", pady=(10, 0))

        def aksi_tes_koneksi():
            test_data = {k: e.get().strip() for k, e in entries_cfg.items()}
            self.set_status("Menguji koneksi ke server MySQL...")
            dlg.update()
            ok, msg = online_db.test_connection(test_data)
            if ok:
                messagebox.showinfo("Koneksi Berhasil", msg, parent=dlg)
                self.set_status("Koneksi MySQL Online terverifikasi!")
            else:
                messagebox.showerror("Koneksi Gagal", msg, parent=dlg)
                self.set_status("Gagal terhubung ke MySQL Online.", is_error=True)

        def aksi_simpan_cfg():
            saved_data = {k: e.get().strip() for k, e in entries_cfg.items()}
            sukses = online_db.save_config(saved_data)
            if sukses:
                messagebox.showinfo(
                    "Pengaturan Disimpan",
                    "Konfigurasi koneksi MySQL online berhasil disimpan ke 'config_db.json'!",
                    parent=dlg
                )
                self.set_status("Pengaturan MySQL Online disimpan.")
            else:
                messagebox.showerror("Gagal Simpan", "Gagal menyimpan konfigurasi ke file.", parent=dlg)

        btn_test = tk.Button(
            f_cfg_btn,
            text="🔌 Tes Koneksi",
            command=aksi_tes_koneksi,
            font=("Segoe UI", 8, "bold"),
            bg="#f1f5f9",
            fg="#0f2b48",
            activebackground="#e2e8f0",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=10,
            pady=4
        )
        btn_test.pack(side="left")

        btn_save = tk.Button(
            f_cfg_btn,
            text="💾 Simpan Pengaturan",
            command=aksi_simpan_cfg,
            font=("Segoe UI", 8, "bold"),
            bg="#0f2b48",
            fg="#ffffff",
            activebackground="#163c63",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4
        )
        btn_save.pack(side="right")


def main():
    root = tk.Tk()
    app = AplikasiPasienBPJS(root)
    root.mainloop()


if __name__ == "__main__":
    main()