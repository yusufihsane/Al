from flask import Flask, request, jsonify, render_template
from google import genai
import os
import tempfile

app = Flask(__name__)

# ==========================================
# GEMINI API
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("UYARI: GEMINI_API_KEY bulunamadı!")

client = genai.Client(
    api_key=API_KEY
)


# ==========================================
# ANA SAYFA
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# GEMINI TEST
# ==========================================

@app.route("/test")
def test():

    try:

        if not API_KEY:
            return jsonify({
                "durum": "HATA",
                "mesaj": "GEMINI_API_KEY Render'da bulunamadı."
            }), 500

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents="Merhaba! Sadece TEST yaz."
        )

        return jsonify({
            "durum": "OK",
            "cevap": response.text
        })

    except Exception as e:

        print("TEST HATASI:", repr(e))

        return jsonify({
            "durum": "HATA",
            "mesaj": str(e)
        }), 500


# ==========================================
# SOR
# ==========================================

@app.route("/sor", methods=["POST"])
def sor():

    try:

        print("================================")
        print("SOR İSTEĞİ GELDİ")
        print("================================")

        # Kullanıcının sorusu
        soru = request.form.get("soru", "").strip()

        # Dosya
        dosya = request.files.get("dosya")

        print("Soru:", soru)

        if dosya:
            print("Dosya:", dosya.filename)
        else:
            print("Dosya yok")


        # ==================================
        # API KEY KONTROL
        # ==================================

        if not API_KEY:

            return jsonify({
                "cevap": "❌ GEMINI_API_KEY Render'da ayarlanmamış."
            }), 500


        # ==================================
        # DOSYA VARSA
        # ==================================

        if dosya and dosya.filename:

            uzanti = os.path.splitext(
                dosya.filename
            )[1]

            dosya_yolu = None

            try:

                # Geçici dosya
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=uzanti
                ) as temp:

                    dosya.save(temp.name)

                    dosya_yolu = temp.name


                print("Dosya Gemini'ye yükleniyor...")

                # Gemini Files API
                gemini_dosyasi = client.files.upload(
                    file=dosya_yolu
                )

                print("Dosya yüklendi.")


                # Soru yoksa
                if not soru:

                    soru = (
                        "Bu dosyayı incele. "
                        "İçeriğini bana Türkçe olarak açıkla."
                    )


                print("Gemini cevap oluşturuyor...")


                response = client.models.generate_content(

                    model="gemini-3.7-flash-lite",

                    contents=[
                        soru,
                        gemini_dosyasi
                    ]

                )


                print("Gemini cevap verdi.")


            finally:

                # Geçici dosyayı sil
                if dosya_yolu and os.path.exists(dosya_yolu):

                    os.remove(dosya_yolu)


        # ==================================
        # SADECE YAZI
        # ==================================

        else:

            if not soru:

                return jsonify({
                    "cevap": "Lütfen bir mesaj yaz."
                })


            print("Sadece yazı gönderiliyor...")

            response = client.models.generate_content(

                model="gemini-3.7-flash-lite",

                contents=soru

            )

            print("Gemini cevap verdi.")


        # ==================================
        # CEVAP
        # ==================================

        cevap = response.text

        print("Cevap:", cevap)

        return jsonify({
            "cevap": cevap
        })


    # ==================================
    # HATA
    # ==================================

    except Exception as e:

        print("================================")
        print("GEMINI / FLASK HATASI")
        print("================================")
        print(repr(e))
        print("================================")

        return jsonify({

            "cevap":
            "❌ Gemini hatası:\n" + str(e)

        }), 500


# ==========================================
# SITEMAP
# ==========================================

@app.route("/sitemap.xml")
def sitemap():

    return """<?xml version="1.0" encoding="UTF-8"?>

<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

<url>

<loc>https://al-bq0g.onrender.com/</loc>

<priority>1.0</priority>

</url>

</urlset>
""", 200, {
        "Content-Type": "application/xml"
    }


# ==========================================
# ROBOTS
# ==========================================

@app.route("/robots.txt")
def robots():

    return """User-agent: *
Allow: /

Sitemap: https://al-bq0g.onrender.com/sitemap.xml
""", 200, {
        "Content-Type": "text/plain"
    }


# ==========================================
# ÇALIŞTIR
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )
