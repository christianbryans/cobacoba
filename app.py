# Bagian backend (Flask)
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Aktifkan CORS untuk semua route
CORS(app)

# Masukkan API Key Spoonacular Anda
API_KEY = "e37c30001c6645009d1e1a7d9245da93"

# Daftar harga bahan per unit sebagai contoh (misalnya harga bahan makanan)
price_estimates = {
    "egg": 3000,
    "chicken breast": 45000,
    "tomato": 5000,
    "onion": 3000,
    "garlic": 2000,
    "potato": 3500,
    # Tambahkan bahan lainnya sesuai dengan resep yang Anda ambil
}

# Atur logging untuk Flask
logging.basicConfig(level=logging.DEBUG)

@app.route('/get_recipe', methods=['POST'])
def get_recipe():
    try:
        # Ambil data dari request
        makanan = request.json.get('makanan', '').lower()
        app.logger.debug(f"Makanan yang dicari: {makanan}")

        if not makanan:
            return jsonify({"status": "error", "message": "Nama makanan tidak boleh kosong."}), 400

        # API URL Spoonacular untuk mencari resep
        search_url = "https://api.spoonacular.com/recipes/complexSearch"
        search_params = {
            "query": makanan,
            "number": 1,  # Jumlah hasil yang diambil
            "apiKey": API_KEY
        }

        # Kirim permintaan untuk pencarian resep
        response = requests.get(search_url, params=search_params)
        if response.status_code != 200:
            app.logger.error(f"Error saat menghubungi API Spoonacular: {response.status_code}")
            return jsonify({"status": "error", "message": "Gagal menghubungi Spoonacular API."}), 500

        search_data = response.json()
        if not search_data.get("results"):
            app.logger.error("Resep tidak ditemukan.")
            return jsonify({"status": "error", "message": "Resep tidak ditemukan."}), 404

        app.logger.debug(f"Hasil pencarian: {search_data}")

        # Ambil ID Resep dan detilnya
        recipe_id = search_data["results"][0]["id"]
        recipe_detail_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        detail_response = requests.get(recipe_detail_url, params={"apiKey": API_KEY})

        if detail_response.status_code != 200:
            return jsonify({"status": "error", "message": "Gagal mendapatkan detail resep."}), 500

        detail_data = detail_response.json()

        # Ambil bahan dan hitung total harga
        ingredients = detail_data.get("extendedIngredients", [])
        bahan = []
        total_harga = 0

        for ing in ingredients:
            ingredient_name = ing["name"].lower()
            # Mengambil harga dari dictionary harga estimasi
            harga_estimasi = price_estimates.get(ingredient_name, 5000)  # 5000 adalah harga default jika tidak ada harga yang sesuai
            bahan.append({
                "nama": ing["name"],
                "jumlah": ing["amount"],
                "satuan": ing["unit"],
                "harga_estimasi": harga_estimasi
            })
            total_harga += harga_estimasi * ing["amount"]  # Harga total per bahan

        app.logger.debug(f"Data detail resep: {detail_data}")

        # Return data ke frontend
        return jsonify({
            "status": "success",
            "judul": detail_data.get("title", "Resep Tidak Diketahui"),
            "bahan": bahan,
            "total_harga": total_harga,
            "instruksi": detail_data.get("instructions", "Tidak ada instruksi yang tersedia.")
        })
    except Exception as e:
        app.logger.error(f"Terjadi kesalahan internal: {str(e)}")
        return jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
