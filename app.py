from flask import Flask, request, jsonify, render_template
from google import genai
import os
import tempfile

app = Flask(__name__)

# Gemini API
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sor", methods=["POST"])
def sor():

    try:

        # Kullanıcının yazdığı soru
        soru = request.form.get("soru", "").strip()

        # Gönderilen dosya
        dosya = request.files.get("dosya")


        # --------------------------------
        # DOSYA VARSA
        # --------------------------------

        if dosya and dosya.filename:

            uzanti = os.path.splitext(
                dosya.filename
            )[1]


            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=uzanti
            ) as temp:

                dosya.save(temp.name)

                dosya_yolu = temp.name


            try:

                # Gemini'ye dosyayı yükle
                gemini_dosyasi = client.files.upload(
                    file=dosya_yolu
                )


                # Soru boşsa varsayılan soru
                if not soru:

                    soru = (
                        "Bu dosyayı incele ve "
                        "bana açıklayabilir misin?"
                    )


                # Gemini
                response = client.models.generate_content(

                    model="gemini-3.6-flash",

                    contents=[
                        soru,
                        gemini_dosyasi
                    ]

                )


            finally:

                # Geçici dosyayı sil
                if os.path.exists(dosya_yolu):

                    os.remove(dosya_yolu)


        # --------------------------------
        # SADECE YAZI
        # --------------------------------

        else:

            if not soru:

                return jsonify({
                    "cevap": "Lütfen bir mesaj yaz."
                })


            response = client.models.generate_content(

                model="gemini-3.6-flash",

                contents=soru

            )


        # --------------------------------
        # CEVAP
        # --------------------------------

        return jsonify({

            "cevap": response.text

        })


    except Exception as e:

        print("HATA:", e)

        return jsonify({

            "cevap": "❌ Hata: " + str(e)

        }), 500


# --------------------------------
# SITEMAP
# --------------------------------

@app.route("/sitemap.xml")
def sitemap():

    return """<?xml version="1.0" encoding="UTF-8"?>

<urlset
xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

<url>

<loc>
https://al-bq0g.onrender.com/
</loc>

<priority>1.0</priority>

</url>

</urlset>
""", 200, {
        "Content-Type": "application/xml"
    }


# --------------------------------
# ROBOTS
# --------------------------------

@app.route("/robots.txt")
def robots():

    return """User-agent: *
Allow: /

Sitemap: https://al-bq0g.onrender.com/sitemap.xml
""", 200, {
        "Content-Type": "text/plain"
    }


# --------------------------------
# ÇALIŞTIR
# --------------------------------

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
