from flask import Flask, request, jsonify, render_template
from groq import Groq
import os

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sor", methods=["POST"])
def sor():
    try:
        soru = request.json.get("soru")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": soru}]
        )
        return jsonify({"cevap": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"cevap": f"Hata: {str(e)}"}), 500

@app.route("/sitemap.xml")
def sitemap():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://al-bq0g.onrender.com/</loc>
    <priority>1.0</priority>
  </url>
</urlset>''', 200, {'Content-Type': 'application/xml'}

@app.route("/robots.txt")
def robots():
    return '''User-agent: *
Allow: /
Sitemap: https://al-bq0g.onrender.com/sitemap.xml
''', 200, {'Content-Type': 'text/plain'}

if __name__ == "__main__":
    app.run(debug=True)
