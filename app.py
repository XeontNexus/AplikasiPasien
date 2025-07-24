import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os

def create_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nama TEXT,
                        umur INTEGER,
                        jenis_kelamin TEXT,
                        alamat TEXT,
                        no_rm TEXT UNIQUE,
                        no_bpjs TEXT UNIQUE
                    )''')
    conn.commit()
    conn.close()

create_db()

def is_data_exists(no_rm, no_bpjs):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE no_rm = ? OR no_bpjs = ?", (no_rm, no_bpjs))
    data = cursor.fetchall()
    conn.close()
    return len(data) > 0

def tambah_data():
    nama = entry_nama.get()
    umur = entry_umur.get()
    jenis_kelamin = combo_jenis_kelamin.get()
    alamat = entry_alamat.get()
    no_rm = entry_no_rm.get()
    no_bpjs = entry_no_bpjs.get()
    if jenis_kelamin == "Pilih":
        messagebox.showerror("Error", "Pilih jenis kelamin!")
        return
    if is_data_exists(no_rm, no_bpjs):
        messagebox.showerror("Error", "Data dengan No. RM atau No. BPJS yang sama sudah ada.")
        return
    if not all([nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs]):
        messagebox.showerror("Error", "Semua field harus diisi!")
        return
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs) VALUES (?, ?, ?, ?, ?, ?)",
                   (nama, umur, jenis_kelamin, alamat, no_rm, no_bpjs))
    conn.commit()
    conn.close()
    messagebox.showinfo("Berhasil", "Data berhasil ditambahkan!")
    tampilkan_data()
    clear_fields()

def clear_fields():
    entry_nama.delete(0, tk.END)
    entry_umur.delete(0, tk.END)
    combo_jenis_kelamin.set('Pilih')
    entry_alamat.delete(0, tk.END)
    entry_no_rm.delete(0, tk.END)
    entry_no_bpjs.delete(0, tk.END)

def backup_data():
    if not os.path.exists('backups'):
        os.makedirs('backups')
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    with open('backups/backup_data.txt', 'w') as file:
        for row in data:
            file.write(f"{row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}\n")
    messagebox.showinfo("Sukses", "Data berhasil dibackup!")

def backup_deleted_data(selected_id):
    if not os.path.exists('backups'):
        os.makedirs('backups')
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (selected_id,))
    deleted_data = cursor.fetchone()
    conn.close()
    if deleted_data:
        with open('backups/deleted_data.txt', 'a') as file:
            file.write(f"{deleted_data[1]}, {deleted_data[2]}, {deleted_data[3]}, {deleted_data[4]}, {deleted_data[5]}, {deleted_data[6]}\n")

def cetak_pdf():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    conn.close()

    pdf_file = "daftar_pasien.pdf"
    c = canvas.Canvas(pdf_file, pagesize=A4)
    width, height = A4

    left_margin = 20 * mm
    right_margin = 20 * mm
    top_margin = 20 * mm
    bottom_margin = 20 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left_margin, height - top_margin, "Daftar Pasien")

    headers = ["Nama", "Umur", "Jenis Kelamin", "Alamat", "No RM", "No BPJS"]
    col_widths = [35*mm, 15*mm, 30*mm, 50*mm, 25*mm, 30*mm]
    row_height = 12

    y = height - top_margin - 25
    x = left_margin

    # Draw header
    c.setFont("Helvetica-Bold", 11)
    for i, header in enumerate(headers):
        c.drawString(x + 2, y + 2, header)
        c.rect(x, y, col_widths[i], row_height, stroke=1, fill=0)
        x += col_widths[i]

    # Draw rows
    c.setFont("Helvetica", 10)
    y -= row_height
    for row in data:
        x = left_margin
        for i, value in enumerate(row[1:]):
            c.drawString(x + 2, y + 2, str(value))
            c.rect(x, y, col_widths[i], row_height, stroke=1, fill=0)
            x += col_widths[i]
        y -= row_height
        if y < bottom_margin:
            c.showPage()
            y = height - top_margin - 25
            x = left_margin
            c.setFont("Helvetica-Bold", 11)
            for i, header in enumerate(headers):
                c.drawString(x + 2, y + 2, header)
                c.rect(x, y, col_widths[i], row_height, stroke=1, fill=0)
                x += col_widths[i]
            c.setFont("Helvetica", 10)
            y -= row_height

    c.save()
    messagebox.showinfo("Sukses", f"Data berhasil dicetak ke {pdf_file}")

def hapus_data():
    selected_item = treeview.selection()
    if not selected_item:
        messagebox.showwarning("Peringatan", "Pilih data yang ingin dihapus.")
        return
    selected_id = selected_item[0]  # iid adalah id di database
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    backup_deleted_data(selected_id)
    cursor.execute("DELETE FROM users WHERE id = ?", (selected_id,))
    conn.commit()
    conn.close()
    treeview.delete(selected_id)
    tampilkan_data()
    messagebox.showinfo("Sukses", "Data berhasil dihapus!")

def tampilkan_data(cari=None):
    for row in treeview.get_children():
        treeview.delete(row)
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # Sorting dan pencarian
    sort_mode = sort_var.get() if 'sort_var' in globals() else "waktu_desc"
    if sort_mode == "nama_asc":
        order_by = "ORDER BY nama ASC"
    elif sort_mode == "nama_desc":
        order_by = "ORDER BY nama DESC"
    elif sort_mode == "waktu_asc":
        order_by = "ORDER BY id ASC"
    else:
        order_by = "ORDER BY id DESC"
    if cari:
        cursor.execute(f"SELECT * FROM users WHERE nama LIKE ? OR no_bpjs LIKE ? {order_by}", ('%' + cari + '%', '%' + cari + '%'))
    else:
        cursor.execute(f"SELECT * FROM users {order_by}")
    data = cursor.fetchall()
    for idx, row in enumerate(data):
        tag = 'oddrow' if idx % 2 == 0 else 'evenrow'
        treeview.insert("", tk.END, iid=row[0], values=row[1:], tags=(tag,))
    conn.close()
    label_jumlah.config(text=f"Jumlah pasien terdaftar: {len(data)}")

def cari_data_otomatis():
    search_term = entry_search.get()
    if search_term.strip() == "":
        tampilkan_data()
    else:
        tampilkan_data(search_term)

# GUI
root = tk.Tk()
root.title("Aplikasi Data Pasien")
root.geometry("1200x750")
root.config(bg="#F5F5F5")

frame_input = tk.Frame(root, bg="#FFFFFF", pady=20)
frame_input.grid(row=0, column=0, padx=30, pady=10, sticky="w")

tk.Label(frame_input, text="Nama", font=("Arial", 12), bg="#FFFFFF").grid(row=0, column=0, padx=10, pady=5, sticky="w")
entry_nama = tk.Entry(frame_input, font=("Arial", 12), width=30)
entry_nama.grid(row=0, column=1, padx=10, pady=5)

tk.Label(frame_input, text="Umur", font=("Arial", 12), bg="#FFFFFF").grid(row=1, column=0, padx=10, pady=5, sticky="w")
entry_umur = tk.Entry(frame_input, font=("Arial", 12), width=30)
entry_umur.grid(row=1, column=1, padx=10, pady=5)

tk.Label(frame_input, text="Jenis Kelamin", font=("Arial", 12), bg="#FFFFFF").grid(row=2, column=0, padx=10, pady=5, sticky="w")
combo_jenis_kelamin = tk.StringVar(root)
combo_jenis_kelamin.set("Pilih")
tk.OptionMenu(frame_input, combo_jenis_kelamin, "Laki-laki", "Perempuan").grid(row=2, column=1, padx=10, pady=5)

tk.Label(frame_input, text="Alamat", font=("Arial", 12), bg="#FFFFFF").grid(row=3, column=0, padx=10, pady=5, sticky="w")
entry_alamat = tk.Entry(frame_input, font=("Arial", 12), width=30)
entry_alamat.grid(row=3, column=1, padx=10, pady=5)

tk.Label(frame_input, text="No. RM", font=("Arial", 12), bg="#FFFFFF").grid(row=4, column=0, padx=10, pady=5, sticky="w")
entry_no_rm = tk.Entry(frame_input, font=("Arial", 12), width=30)
entry_no_rm.grid(row=4, column=1, padx=10, pady=5)

tk.Label(frame_input, text="No. BPJS", font=("Arial", 12), bg="#FFFFFF").grid(row=5, column=0, padx=10, pady=5, sticky="w")
entry_no_bpjs = tk.Entry(frame_input, font=("Arial", 12), width=30)
entry_no_bpjs.grid(row=5, column=1, padx=10, pady=5)

# Frame tombol dan searching di kanan
frame_buttons = tk.Frame(root, bg="#F5F5F5", pady=30, padx=30)
frame_buttons.grid(row=0, column=1, padx=(60,40), pady=(30,10), sticky="ne")

tk.Label(frame_buttons, text="Cari Nama atau No. BPJS:", font=("Arial", 12), bg="#F5F5F5", anchor="e", width=25).grid(row=0, column=0, padx=10, pady=5, sticky="e")
entry_search = tk.Entry(frame_buttons, font=("Arial", 12), width=30, justify="right")
entry_search.grid(row=0, column=1, padx=10, pady=5, sticky="e")
entry_search.bind('<KeyRelease>', lambda event: cari_data_otomatis())
tk.Button(frame_buttons, text="Cari", command=cari_data_otomatis, font=("Arial", 12), bg="#FFC107", fg="black", width=10).grid(row=0, column=2, padx=10, pady=5, sticky="e")

tk.Button(frame_buttons, text="Tambah Data", command=tambah_data, font=("Arial", 12), bg="#4CAF50", fg="white", width=18).grid(row=1, column=0, padx=10, pady=8, sticky="e")
tk.Button(frame_buttons, text="Cetak Daftar ke PDF", command=cetak_pdf, font=("Arial", 12), bg="#2196F3", fg="white", width=18).grid(row=1, column=1, padx=10, pady=8, sticky="e")
tk.Button(frame_buttons, text="Backup Data", command=backup_data, font=("Arial", 12), bg="#FF5722", fg="white", width=18).grid(row=1, column=2, padx=10, pady=8, sticky="e")
tk.Button(frame_buttons, text="Hapus Data", command=hapus_data, font=("Arial", 12), bg="#FF0000", fg="white", width=18).grid(row=2, column=0, padx=10, pady=8, sticky="e")

# Pilihan urutan data
sort_var = tk.StringVar(value="waktu_desc")
tk.Label(frame_buttons, text="Urutkan Berdasarkan:", font=("Arial", 11), bg="#F5F5F5").grid(row=3, column=0, padx=10, pady=(15,5), sticky="e")
tk.Radiobutton(frame_buttons, text="Nama (A-Z)", variable=sort_var, value="nama_asc", font=("Arial", 11), bg="#F5F5F5", command=lambda: tampilkan_data()).grid(row=3, column=1, padx=5, pady=(15,5), sticky="w")
tk.Radiobutton(frame_buttons, text="Nama (Z-A)", variable=sort_var, value="nama_desc", font=("Arial", 11), bg="#F5F5F5", command=lambda: tampilkan_data()).grid(row=3, column=2, padx=5, pady=(15,5), sticky="w")
tk.Radiobutton(frame_buttons, text="Terbaru", variable=sort_var, value="waktu_desc", font=("Arial", 11), bg="#F5F5F5", command=lambda: tampilkan_data()).grid(row=4, column=1, padx=5, pady=5, sticky="w")
tk.Radiobutton(frame_buttons, text="Terlama", variable=sort_var, value="waktu_asc", font=("Arial", 11), bg="#F5F5F5", command=lambda: tampilkan_data()).grid(row=4, column=2, padx=5, pady=5, sticky="w")

# Frame tabel
frame_tabel = tk.Frame(root, bg="#FFFFFF")
frame_tabel.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
frame_tabel.grid_rowconfigure(0, weight=1)
frame_tabel.grid_columnconfigure(0, weight=1)

treeview = ttk.Treeview(frame_tabel, columns=("Nama", "Umur", "Jenis Kelamin", "Alamat", "No RM", "No BPJS"), show="headings", height=15)
treeview.heading("Nama", text="Nama")
treeview.heading("Umur", text="Umur")
treeview.heading("Jenis Kelamin", text="Jenis Kelamin")
treeview.heading("Alamat", text="Alamat")
treeview.heading("No RM", text="No RM")
treeview.heading("No BPJS", text="No BPJS")

# Scrollbar
vsb = ttk.Scrollbar(frame_tabel, orient="vertical", command=treeview.yview)
hsb = ttk.Scrollbar(frame_tabel, orient="horizontal", command=treeview.xview)
treeview.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
treeview.grid(row=0, column=0, sticky="nsew")
vsb.grid(row=0, column=1, sticky="ns")
hsb.grid(row=1, column=0, sticky="ew")

# Kolom dan style
treeview.column("Nama", width=180, anchor="center")
treeview.column("Umur", width=100, anchor="center")
treeview.column("Jenis Kelamin", width=140, anchor="center")
treeview.column("Alamat", width=350, anchor="w")
treeview.column("No RM", width=150, anchor="center")
treeview.column("No BPJS", width=150, anchor="center")

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview",
    font=("Arial", 12),
    rowheight=44,
    bordercolor="#000000",
    borderwidth=1,
    relief="solid"
)
style.configure("Treeview.Heading",
    font=("Arial", 13, "bold"),
    background="#1976D2",
    foreground="#FFFFFF",
    bordercolor="#000000",
    borderwidth=1,
    relief="solid"
)
style.layout("Treeview", [
    ("Treeview.treearea", {"sticky": "nswe"})
])

treeview.tag_configure('oddrow', background='#4FC3F7')
treeview.tag_configure('evenrow', background='#E3F2FD')

# Label jumlah data
label_jumlah = tk.Label(root, text="", font=("Arial", 12), bg="#F5F5F5")
label_jumlah.grid(row=2, column=0, columnspan=2, sticky="w", padx=30, pady=(0,10))

tampilkan_data()
root.mainloop()