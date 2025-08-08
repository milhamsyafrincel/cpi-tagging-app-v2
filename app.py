from flask import Flask, request, render_template, send_file
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime, timedelta
import pytesseract 
import time
import re
import io
import os


app = Flask(__name__)

#LOGO_PATH = os.path.join(app.root_path, 'static', 'logo_psn.png')
FONT_REGULAR_PATH = os.path.join(app.root_path, 'static', 'ARIAL.TTF') # Arial Reguler
FONT_BOLD_PATH = os.path.join(app.root_path, 'static', 'ARIALBD.TTF') # Arial Bold
FONT_ITALIC_PATH = os.path.join(app.root_path, 'static', 'ARIALI.TTF') # Arial Italic

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_image', methods=['POST'])
def process_image():

    start_execution_time = time.time() # Mengambil waktu mulai eksekusi

    # Pengecekan file image
    if 'image' not in request.files:
        return 'No image part in the request', 400
    file = request.files['image']
    if file.filename == '':
        return 'No selected file', 400
    
    # Mendapatkan ID dari form data
    image_id = request.form.get('image_id')
    if not image_id:
        return 'ID tidak ditemukan dalam permintaan', 400
    
    # Ekseskusi Image
    if file:
        try:
            # 1. Open file Image
            original_image = Image.open(file.stream).convert("RGBA")

            # 2. Open file logo
            #logo = Image.open(LOGO_PATH).convert("RGBA")
            img_width, img_height = original_image.size

            # Atur Transparansi logo (Optional)
            #new_alpha_value = int(255 * 1)
            #alpha = logo.split()[3] 
            #alpha = alpha.point(lambda p: p * (new_alpha_value / 255.0)) 
            #logo.putalpha(alpha) 
            
            # 3. Resize logo
            #max_logo_width = 150
            #logo_aspect_ratio = logo.width / logo.height
            #new_logo_height = int(max_logo_width / logo_aspect_ratio)
            #logo = logo.resize((max_logo_width, new_logo_height), Image.Resampling.LANCZOS)

            # 4. Atur posisi logo
            padding_x = 120 
            padding_y = 80 
            #position_x = padding_x
            #position_y = padding_y
            #position_x = max(0, position_x)
            #position_y = max(0, position_y)
            #logo_position = (position_x, position_y)

            # 5. Tempel logo pada image
            #combined_image = Image.new('RGBA', original_image.size)
            #combined_image = Image.alpha_composite(combined_image, original_image)
            #combined_image.paste(logo, logo_position, logo)
            #draw = ImageDraw.Draw(combined_image)
            draw = ImageDraw.Draw(original_image)
            
            # 6. Inisialisasi size, jenis, dan warna font
            id_font_size = 50
            datetime_font_size = 32
            cn_cpi_font_size = 25
            gap_font_size = 3

            id_font = None
            datetime_font = None
            cn_cpi_font = None
            
            text_color = (255, 255, 255, 255) 

            # Font Bold untuk ID
            try:
                id_font = ImageFont.truetype(FONT_BOLD_PATH, id_font_size) 
            except IOError:
                print(f"Font Bold '{FONT_BOLD_PATH}' tidak ditemukan. Menggunakan font default.")
                id_font = ImageFont.load_default()
                id_font_size = 20 
            
            # Font Reguler untuk date time
            try:
                datetime_font = ImageFont.truetype(FONT_REGULAR_PATH, datetime_font_size) 
            except IOError:
                print(f"Font Regular '{FONT_REGULAR_PATH}' tidak ditemukan. Menggunakan font default.")
                datetime_font = ImageFont.load_default()
                datetime_font_size = 15 

            # Font Italic untuk nilai C/N dan CPI
            try:
                cn_cpi_font = ImageFont.truetype(FONT_ITALIC_PATH, cn_cpi_font_size) 
            except IOError:
                print(f"Font Italic '{FONT_ITALIC_PATH}' tidak ditemukan. Menggunakan font default.")
                cn_cpi_font = ImageFont.load_default()
                cn_cpi_font_size = 15 

            # 7. Extract nilai C/N (red) dan CPI (green) dengan OCR
            # Define nilai awal C/N dan CPI
            c_n_value = "N/A"
            cpi_value = "N/A"

            # Definie ROI (Region of Interest) / Area yang mau dicrop pada gambar
            ocr_area_red_line = (500, 60, 950, 100)  
            ocr_area_green_line = (400, 120, 1100, 170) 

            # Convert Image ke RGB
            original_image_rgb = original_image.convert("RGB")

            # Crop image sesuai dengan ROI
            cropped_red_line_raw = original_image_rgb.crop(ocr_area_red_line)
            cropped_green_line_raw = original_image_rgb.crop(ocr_area_green_line)

            # Extract nilai C/N (red)
            processed_red_line = cropped_red_line_raw
            red_text_ocr = pytesseract.image_to_string(processed_red_line, config='--psm 7 --oem 1').strip() # OCR for C/N
            if not red_text_ocr: # Cek apakah OCR berhasil
                processed_red_line = processed_red_line.convert('L') # Convert Image ke Luminance 
                threshold_red = 50 
                processed_red_line = processed_red_line.point(lambda p: 255 if p > threshold_red else 0, '1') # Convert Image ke Binary
                red_text_ocr = pytesseract.image_to_string(processed_red_line, config='--psm 7 --oem 1').strip() # OCR for C/N

            # Cari nilai C/N pada hasil OCR
            match_red_value = re.search(r'([\d\s]*\d+\s*[\.,]\s*\d+[\d\s]*\s*)d', red_text_ocr, re.IGNORECASE) # Cari nilai sebelum huruf d (dB)
            if match_red_value:
                c_n_value = match_red_value.group(1).replace(' ', '')
            else: # Fallback jika unit dB tidak terdeteksi
                match_red_value_alt = re.search(r'z\s*([\d\s]*\d+\s*[\.,]\s*\d+[\d\s])', red_text_ocr,re.IGNORECASE) # Cari nilai setelah huruf z (Mhz)
                if match_red_value_alt:
                    c_n_value = match_red_value_alt.group(1).replace(' ', '')
            
            # Extract nilai CPI (green)
            processed_green_line = cropped_green_line_raw 
            green_text_ocr = pytesseract.image_to_string(processed_green_line, config='--psm 7 --oem 1').strip() # OCR for CPI
            if not green_text_ocr: # Cek apakah OCR berhasil
                processed_green_line = processed_green_line.convert('L') # Convert Image ke Luminance
                threshold_green = 120 
                processed_green_line = processed_green_line.point(lambda p: 255 if p > threshold_green else 0, '1') # Convert Image ke Binary
                green_text_ocr = pytesseract.image_to_string(processed_green_line, config='--psm 7 --oem 1').strip() # OCR for CPI

            # Cari nilai CPI pada hasil OCR
            match_green_value = re.search(r'([\d\s]*\d+\s*[\.,]\s*\d+[\d\s]*\s*)d', green_text_ocr, re.IGNORECASE) # Cari nilai sebelum huruf d (dB)
            if match_green_value:
                cpi_value = match_green_value.group(1).replace(' ', '')
            else: # Fallback jika unit dB tidak terdeteksi
                match_green_value_alt = re.search(r'=\s*([\d\s]*\d+\s*[\.,]\s*\d+[\d\s])', green_text_ocr, re.IGNORECASE) # Cari nilai setelah karakter = 
                if match_green_value_alt:
                    cpi_value = match_green_value_alt.group(1).replace(' ', '')

            # 8. Ambil waktu saat ini
            now = datetime.now() + timedelta(hours=7)
            date_str = now.strftime("%d/%m/%Y")
            time_str = now.strftime("%H:%M")

            # 9. Tentukan text yang akan ditempel pada image
            id_text = f'{image_id}'
            datetime_text = f'{date_str}'
            split_tex = f'_____________'
            c_n_display_text = f'C/N = {c_n_value} dB'
            cpi_display_text = f'CPI = {cpi_value} dB'

            # 10. Hitung posisi text
            text_position_x = padding_x
                             
            text_id_y =  img_height - id_font_size - datetime_font_size * 2 - padding_y - 140 
            text_date_y =  img_height - datetime_font_size * 2 - padding_y - 140 + gap_font_size
            split_y =  img_height - datetime_font_size * 1 - padding_y - 165 + gap_font_size
            text_cn_y =  img_height - datetime_font_size * -1 - padding_y - 185 + gap_font_size
            text_cpi_y =  img_height - datetime_font_size * -2 - padding_y - 185 + gap_font_size*1.3
        
            # 11. Tambahkan text ke gambar
            draw.text((text_position_x, text_id_y), id_text, font=id_font, fill=text_color)
            draw.text((text_position_x, text_date_y), datetime_text, font=datetime_font, fill=text_color)
            draw.text((text_position_x, split_y), split_tex, font=datetime_font, fill=text_color)
            draw.text((text_position_x, text_cn_y), c_n_display_text, font=cn_cpi_font, fill=text_color)
            draw.text((text_position_x, text_cpi_y), cpi_display_text, font=cn_cpi_font, fill=text_color)

            # 12. Simpan gambar hasil ke buffer memori
            byte_arr = io.BytesIO()
            #combined_image.save(byte_arr, format='PNG') 
            original_image.save(byte_arr, format='PNG') 
            byte_arr.seek(0)

            end_execution_time = time.time() # Mengambil waktu selesai eksekusi
            execution_duration = end_execution_time - start_execution_time # Menghitung waktu eksekusi
            print(f"======> Image Processing Duration:  {execution_duration:.4f} s.")

            # 13. Kirim file kembali ke frontend
            return send_file(byte_arr, mimetype='image/png', as_attachment=True, download_name=f'{image_id}_{file.filename}')
        
        except Exception as e:
            print(f"Error processing file: {e}")
            return str(e), 500 # Kirim pesan error ke frontend

if __name__ == '__main__':
    #if not os.path.exists(LOGO_PATH):
        #print(f"Error: Logo file not found at {LOGO_PATH}. Please ensure 'logo_psn.png' is in the 'static' folder.")
        
    app.run(host="0.0.0.0", debug=True) 