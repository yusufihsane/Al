from flask import Flask, request, jsonify, render_template
from google import genai
import os

app = Flask(__name__)

# Gemini API anahtarını ortam değişkeninden al
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sor", methods=["POST"])
def sor():
    try:
        soru = request.json.get("soru")

        if not soru:
            return jsonify({
                "cevap": "Lütfen bir soru yaz."
            }), 400

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
