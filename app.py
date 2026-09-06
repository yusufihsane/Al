from flask import Flask, request, jsonify, render_template
from google import genai
import os
import tempfile

app = Flask(__name__)

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sor", methods=["POST"])
def sor():
    try:
        soru = request.form.get("soru", "")
        dosya = request.files.get("dosya")

        # Dosya varsa
        if dosya and dosya.filename:

            # Geçici olarak kaydet
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(dosya.filename)[1]
            ) as temp:

                dosya.save(temp.name)
                dosya_yolu = temp.name

            # Gemini'ye dosyayı yükle
            gemini_dosyasi = client.files.upload(
                file=dosya_yolu
            )

            # Gemini'ye soruyu ve dosyayı gönder
            response = client.models.generate_content(
                model="gemini-3.7-flash",
                contents=[
                    soru or "Bu dosyayı incele ve açıkla.",
                    gemini_dosyasi
                ]
            )

            # Geçici dosyayı sil
            os.remove(dosya_yolu)

        else:
            # Normal mesaj
            response = client.models.generate_content(
                model="gemini-3.7-flash",
                contents=soru
            )

        return jsonify({
            "cevap": response.text
        })

    except Exception as e:

        return jsonify({
            "cevap": f"Hata: {str(e)}"
        }), 500


@app.route("/sitemap.xml")
def sitemap():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://al-bq0g.onrender.com/</loc>
    <priority>1.0</priority>
  </url>
</urlset>''', 200, {
    'Content-Type': 'application/xml'
}


@app.route("/robots.txt")
def robots():
    return '''User-agent: *
Allow: /
Sitemap: https://al-bq0g.onrender.com/sitemap.xml
''', 200, {
    'Content-Type': 'text/plain'
}


if __name__ == "__main__":
    app.run(debug=True)
