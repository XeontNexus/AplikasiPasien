"""
Modul Cetak Laporan PDF - Sistem Rekam Medis Pasien BPJS
Menghasilkan dokumen PDF profesional siap cetak dengan header klinik resmi
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import os
import database


def cetak_daftar_pasien_pdf(filepath="daftar_pasien.pdf"):
    """
    Membuat laporan rekapitulasi data pasien ke file PDF.
    Mengembalikan (sukses: bool, pesan_atau_path: str)
    """
    try:
        pasien_list = database.get_all_patients(sort_mode="nama_asc")
        stats = database.get_statistics()

        c = canvas.Canvas(filepath, pagesize=A4)
        page_width, page_height = A4

        # Pengaturan margin
        left_margin = 35
        right_margin = page_width - 35
        content_width = right_margin - left_margin
        top_margin = page_height - 35
        bottom_margin = 40

        # Definisi Kolom Tabel (Total: 525 pt)
        # No(25), Nama(125), Alamat(130), JK(55), Umur(40), No.RM(65), No.BPJS(85)
        col_widths = [25, 125, 130, 55, 40, 65, 85]
        col_headers = ["No", "Nama Pasien", "Alamat Domisili", "Gender", "Umur", "No. RM", "No. BPJS"]

        def draw_header(c, current_page):
            # Garis aksen atas
            c.setFillColor(colors.HexColor("#0f2b48"))
            c.rect(left_margin, top_margin - 8, content_width, 4, fill=1, stroke=0)

            # Logo simbol klinik / teks instansi
            c.setFillColor(colors.HexColor("#0f2b48"))
            c.setFont("Helvetica-Bold", 14)
            c.drawString(left_margin, top_margin - 28, "FASILITAS KESEHATAN TINGKAT PERTAMA (FKTP)")

            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor("#475569"))
            c.drawString(left_margin, top_margin - 41, "Jl. Sehat Sentosa No. 128 | Layanan Pasien BPJS Kesehatan Terpadu | Telp: (021) 7890-1234")

            # Garis pemisah kop
            c.setStrokeColor(colors.HexColor("#cbd5e1"))
            c.setLineWidth(0.8)
            c.line(left_margin, top_margin - 49, right_margin, top_margin - 49)

            # Judul Laporan
            c.setFillColor(colors.HexColor("#1e293b"))
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left_margin, top_margin - 68, "LAPORAN REKAPITULASI DATA PASIEN BPJS")

            # Info Tanggal & Statistik
            now_str = datetime.now().strftime("%d %B %Y, %H:%M WIB")
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.HexColor("#64748b"))
            c.drawRightString(right_margin, top_margin - 68, f"Dicetak: {now_str}")

            c.setFont("Helvetica", 8.5)
            c.setFillColor(colors.HexColor("#334155"))
            c.drawString(left_margin, top_margin - 82, f"Total Pasien: {stats['total']} | Laki-laki: {stats['pria']} | Perempuan: {stats['wanita']}")

            # Header Tabel
            table_top = top_margin - 96
            row_height = 20

            # Background header tabel
            c.setFillColor(colors.HexColor("#0f2b48"))
            c.rect(left_margin, table_top - row_height, content_width, row_height, fill=1, stroke=0)

            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8.5)
            x_pos = left_margin
            for idx, col in enumerate(col_headers):
                align_center = idx in (0, 1, 4, 5)
                w = col_widths[idx]
                if align_center:
                    c.drawCentredString(x_pos + (w / 2), table_top - 14, col)
                else:
                    c.drawString(x_pos + 6, table_top - 14, col)
                x_pos += w

            return table_top - row_height

        def draw_footer(c, page_num):
            c.setStrokeColor(colors.HexColor("#e2e8f0"))
            c.setLineWidth(0.6)
            c.line(left_margin, bottom_margin + 12, right_margin, bottom_margin + 12)

            c.setFont("Helvetica", 8)
            c.setFillColor(colors.HexColor("#94a3b8"))
            c.drawString(left_margin, bottom_margin, "Sistem Informasi Rekam Medis Pasien BPJS")
            c.drawRightString(right_margin, bottom_margin, f"Halaman {page_num}")

        current_page = 1
        y = draw_header(c, current_page)
        row_height = 18

        for index, p in enumerate(pasien_list, 1):
            # Check pagination
            if y - row_height < bottom_margin + 60:
                draw_footer(c, current_page)
                c.showPage()
                current_page += 1
                y = draw_header(c, current_page)

            # Striping row
            if index % 2 == 0:
                c.setFillColor(colors.HexColor("#f8fafc"))
                c.rect(left_margin, y - row_height, content_width, row_height, fill=1, stroke=0)

            # Border horizontal tipis
            c.setStrokeColor(colors.HexColor("#e2e8f0"))
            c.setLineWidth(0.4)
            c.line(left_margin, y - row_height, right_margin, y - row_height)

            # Draw row text
            c.setFillColor(colors.HexColor("#1e293b"))
            c.setFont("Helvetica", 8)

            jk_display = "Laki-laki" if p['jenis_kelamin'] == "Laki-laki" else "Perempuan"
            values = [
                str(index),
                str(p['nama'])[:26],
                str(p['alamat'])[:32],
                jk_display,
                f"{p['umur']} th",
                str(p['no_rm']),
                str(p['no_bpjs'])
            ]

            x_pos = left_margin
            for idx, val in enumerate(values):
                align_center = idx in (0, 1, 4, 5)
                w = col_widths[idx]
                if align_center:
                    c.drawCentredString(x_pos + (w / 2), y - 13, val)
                else:
                    c.drawString(x_pos + 6, y - 13, val)
                x_pos += w

            y -= row_height

        # Jika ada ruang, tambahkan tanda tangan petugas
        if y - 70 > bottom_margin:
            c.setFont("Helvetica", 8.5)
            c.setFillColor(colors.HexColor("#334155"))
            c.drawString(right_margin - 140, y - 28, "Petugas Rekam Medis,")
            c.setStrokeColor(colors.HexColor("#94a3b8"))
            c.setLineWidth(0.8)
            c.line(right_margin - 140, y - 65, right_margin - 20, y - 65)
            c.drawString(right_margin - 140, y - 76, "( Administrator / Rekam Medis )")

        draw_footer(c, current_page)
        c.save()
        return True, filepath

    except PermissionError:
        return False, f"File '{filepath}' sedang dibuka oleh aplikasi lain. Silakan tutup file tersebut terlebih dahulu."
    except Exception as e:
        return False, f"Gagal membuat PDF: {str(e)}"
