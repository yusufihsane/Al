from flask import Flask, request, jsonify, render_template
from groq import Groq
import os

app = Flask(__name__)
client = Groq(api_key=os.environ.get(""))

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

if __name__ == "__main__":
    app.run(debug=True)
