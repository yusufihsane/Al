
from flask import Flask, request, jsonify, render_template, session
from groq import Groq
import os

app = Flask(__name__)

# ==========================================
# SESSION GİZLİ ANAHTARI
# ==========================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "shmart-ai-gizli-anahtar-2026"
)

# ==========================================
# GROQ API
# ==========================================

API_KEY = os.environ.get("GROQ_API_KEY")

if not API_KEY:
    print("UYARI: GROQ_API_KEY bulunamadı!")

client = Groq(
    api_key=API_KEY
)

# Güncel Groq modeli
MODEL = "openai/gpt-oss-120b"


# ==========================================
# TOKEN TASARRUF AYARLARI
# ==========================================

# Modele her seferinde gönderilecek son mesaj sayısı
SON_MESAJ_SAYISI = 8

# Eski konuşmaların özetinde tutulabilecek maksimum karakter
MAKS_OZET_UZUNLUGU = 4000

# Dosya için maksimum karakter
MAKS_DOSYA_UZUNLUGU = 40000


# ==========================================
# ANA SAYFA
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# SOHBET GEÇMİŞİNİ AL
# ==========================================

def sohbet_gecmisi_al():

    if "sohbet_gecmisi" not in session:
        session["sohbet_gecmisi"] = []

    return session["sohbet_gecmisi"]


# ==========================================
# SOHBET ÖZETİNİ AL
# ==========================================

def sohbet_ozeti_al():

    return session.get(
        "sohbet_ozeti",
        ""
    )


# ==========================================
# SOHBET ÖZETİNİ KAYDET
# ==========================================

def sohbet_ozeti_kaydet(ozet):

    # Özet aşırı büyümesin
    if len(ozet) > MAKS_OZET_UZUNLUGU:
        ozet = ozet[-MAKS_OZET_UZUNLUGU:]

    session["sohbet_ozeti"] = ozet
    session.modified = True


# ==========================================
# GEÇMİŞE MESAJ EKLE
# ==========================================

def mesaji_kaydet(rol, mesaj):

    gecmis = sohbet_gecmisi_al()

    gecmis.append({
        "rol": rol,
        "mesaj": mesaj
    })

    session["sohbet_gecmisi"] = gecmis
    session.modified = True


# ==========================================
# ESKİ MESAJLARI ÖZETLE
# ==========================================

def eski_mesajlari_ozetle():

    gecmis = sohbet_gecmisi_al()

    # Yeterince mesaj yoksa özetleme yapma
    if len(gecmis) <= SON_MESAJ_SAYISI:
        return

    # Son 8 mesaj dışındaki eski mesajlar
    eski_mesajlar = gecmis[:-SON_MESAJ_SAYISI]

    # Zaten özetlenmiş eski mesajları tekrar özetlememek için
    # mevcut özeti alıyoruz.
    mevcut_ozet = sohbet_ozeti_al()

    eski_metin = ""

    for mesaj in eski_mesajlar:

        if mesaj["rol"] == "kullanici":

            eski_metin += (
                "Kullanıcı: "
                + mesaj["mesaj"]
                + "\n"
            )

        elif mesaj["rol"] == "ai":

            eski_metin += (
                "Shmart AI: "
                + mesaj["mesaj"]
                + "\n"
            )

    # Eski mesajlar çok uzunsa burada da sınırla
    if len(eski_metin) > 12000:

        eski_metin = eski_metin[-12000:]

    # ==========================================
    # ÖZETLEME İÇİN AYRI GROQ İSTEĞİ
    # ==========================================

    try:

        ozet_prompt = f"""
Sen Shmart AI'ın sohbet hafızasını yöneten yardımcı sistemsin.

Aşağıdaki eski konuşmayı kısa ve faydalı bir hafızaya dönüştür.

Özette özellikle şunları koru:

- Kullanıcının yaptığı proje ve önemli teknik bilgiler
- Kullanıcının verdiği önemli tercihler
- Devam eden sorunlar
- Daha önce konuşulan önemli konular
- Kodlama konusunda önemli kararlar
- Kullanıcının sorduğu ve gelecekte tekrar gerekli olabilecek bilgiler

Gereksiz selamlaşmaları ve tekrarları çıkar.

Mevcut eski özet:
{mevcut_ozet}

Yeni eski konuşmalar:
{eski_metin}

En fazla yaklaşık 300-500 kelimelik kısa bir hafıza özeti oluştur.
""".strip()

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content":
                    "Kısa ve bilgi yoğun sohbet özeti oluştur."
                },
                {
                    "role": "user",
                    "content": ozet_prompt
                }
            ],

            temperature=0.2,

            max_tokens=800
        )

        yeni_ozet = response.choices[0].message.content

        if yeni_ozet:

            sohbet_ozeti_kaydet(
                yeni_ozet
            )

        # Sadece son mesajları sakla
        session["sohbet_gecmisi"] = (
            gecmis[-SON_MESAJ_SAYISI:]
        )

        session.modified = True

    except Exception as e:

        print(
            "ÖZETLEME HATASI:",
            repr(e)
        )

        # Özetleme başarısız olursa geçmişi silme
        # sadece son mesajları tut
        session["sohbet_gecmisi"] = (
            gecmis[-SON_MESAJ_SAYISI:]
        )

        session.modified = True


# ==========================================
# GROQ İÇİN MESAJLARI OLUŞTUR
# ==========================================

def mesajlari_olustur():

    gecmis = sohbet_gecmisi_al()

    ozet = sohbet_ozeti_al()

    messages = [

        {
            "role": "system",
            "content": """
Sen Shmart AI adlı yardımcı bir yapay zekasın.

Kullanıcıyla Türkçe ve anlaşılır şekilde konuş.

KODLAMA SORULARINDA:

- Kodu dikkatlice analiz et.
- Hataları bul.
- Kullanıcı tam kod isterse eksiksiz kod ver.
- Kodları Markdown kod blokları içerisinde göster.
- Gereksiz yere kodu kısaltma.
- Kullanıcı bir dosya gönderirse dosyanın içeriğini dikkatlice incele.

NORMAL SORULARDA:

- Açık ve anlaşılır cevap ver.
- Gereksiz yere aşırı uzun cevap verme.
- Kullanıcının seviyesine uygun anlat.

SOHBET HAFIZASI:

Aşağıdaki özet eski konuşmalardan kalan önemli bilgileri içerir.
Gerekli olduğunda bu bilgileri kullan.

Sen Shmart AI'sın.
""".strip()
        }

    ]

    # ==========================================
    # ESKİ SOHBET ÖZETİ
    # ==========================================

    if ozet:

        messages.append({

            "role": "system",

            "content":
            "Eski sohbetlerden kalan hafıza özeti:\n\n"
            + ozet

        })

    # ==========================================
    # SON MESAJLAR
    # ==========================================

    for mesaj in gecmis:

        if mesaj["rol"] == "kullanici":

            messages.append({

                "role": "user",

                "content":
                mesaj["mesaj"]

            })

        elif mesaj["rol"] == "ai":

            messages.append({

                "role": "assistant",

                "content":
                mesaj["mesaj"]

            })

    return messages


# ==========================================
# /TEST
# ==========================================

@app.route("/test")
def test():

    try:

        if not API_KEY:

            return jsonify({

                "durum": "HATA",

                "mesaj":
                "GROQ_API_KEY Render'da bulunamadı."

            }), 500

        response = client.chat.completions.create(

            model=MODEL,

            messages=[

                {
                    "role": "user",
                    "content":
                    "Merhaba! Sadece TEST yaz."
                }

            ],

            max_tokens=20

        )

        cevap = response.choices[0].message.content

        return jsonify({

            "durum": "OK",

            "cevap": cevap

        })

    except Exception as e:

        print(
            "TEST HATASI:",
            repr(e)
        )

        return jsonify({

            "durum": "HATA",

            "mesaj": str(e)

        }), 500


# ==========================================
# /SOR
# ==========================================

@app.route(
    "/sor",
    methods=["POST"]
)
def sor():

    try:

        print(
            "================================"
        )

        print(
            "SOR İSTEĞİ GELDİ"
        )

        print(
            "================================"
        )

        # ==================================
        # KULLANICI SORUSU
        # ==================================

        soru = request.form.get(
            "soru",
            ""
        ).strip()

        # ==================================
        # DOSYA
        # ==================================

        dosya = request.files.get(
            "dosya"
        )

        print(
            "Soru:",
            soru
        )

        if dosya and dosya.filename:

            print(
                "Dosya:",
                dosya.filename
            )

        else:

            print(
                "Dosya yok"
            )

        # ==================================
        # API KEY
        # ==================================

        if not API_KEY:

            return jsonify({

                "cevap":
                "❌ GROQ_API_KEY Render'da ayarlanmamış."

            }), 500

        # ==================================
        # BOŞ İSTEK
        # ==================================

        if not soru and not dosya:

            return jsonify({

                "cevap":
                "Lütfen bir mesaj yaz veya dosya gönder."

            })

        # ==================================
        # DOSYA VARSA
        # ==================================

        if dosya and dosya.filename:

            dosya_adi = dosya.filename

            print(
                "Dosya okunuyor..."
            )

            uzanti = os.path.splitext(
                dosya_adi
            )[1].lower()

            # ==================================
            # DESTEKLENEN DOSYALAR
            # ==================================

            desteklenen = [

                ".txt",
                ".py",
                ".html",
                ".htm",
                ".css",
                ".js",
                ".json",
                ".csv",
                ".md",
                ".xml",
                ".yml",
                ".yaml",
                ".java",
                ".c",
                ".cpp",
                ".cs",
                ".php",
                ".sql"

            ]

            if uzanti not in desteklenen:

                return jsonify({

                    "cevap":
                    f"❌ `{dosya_adi}` dosyasını "
                    "şu anda doğrudan okuyamıyorum.\n\n"
                    "Desteklenen dosyalar:\n"
                    "TXT, PY, HTML, CSS, JS, JSON, "
                    "CSV, MD, XML, YAML, Java, C, "
                    "C++, C#, PHP ve SQL."

                }), 400

            # ==================================
            # DOSYAYI OKU
            # ==================================

            try:

                dosya_icerigi = dosya.read().decode(
                    "utf-8",
                    errors="replace"
                )

            except Exception as e:

                return jsonify({

                    "cevap":
                    f"❌ Dosya okunamadı: {str(e)}"

                }), 400

            # ==================================
            # DOSYA SINIRI
            # ==================================

            if len(dosya_icerigi) > MAKS_DOSYA_UZUNLUGU:

                dosya_icerigi = (
                    dosya_icerigi[
                        :MAKS_DOSYA_UZUNLUGU
                    ]
                    +
                    "\n\n[Dosyanın devamı "
                    "çok uzun olduğu için kesildi.]"
                )

            # ==================================
            # SORU YOKSA
            # ==================================

            if not soru:

                soru = (
                    "Bu dosyayı incele. "
                    "İçeriğini Türkçe olarak açıkla. "
                    "Kod varsa ne yaptığını ve "
                    "varsa hatalarını belirt."
                )

            # ==================================
            # KULLANICI MESAJINI KAYDET
            # ==================================

            mesaji_kaydet(

                "kullanici",

                f"{soru}\n\n"
                f"[Dosya: {dosya_adi}]"

            )

            # ==================================
            # ESKİ MESAJLARI ÖZETLE
            # ==================================

            eski_mesajlari_ozetle()

            # ==================================
            # NORMAL MESAJLARI AL
            # ==================================

            messages = mesajlari_olustur()

            # ==================================
            # DOSYAYI SON MESAJ OLARAK EKLE
            # ==================================

            dosya_mesaji = f"""
Kullanıcı bir dosya gönderdi.

Dosya adı:
{dosya_adi}

Dosya içeriği:
--------------------
{dosya_icerigi}
--------------------

Kullanıcının sorusu:
{soru}

Dosyanın içeriğini dikkate alarak cevap ver.
""".strip()

            messages.append({

                "role": "user",

                "content":
                dosya_mesaji

            })

            print(
                "Groq dosya içeriği ile cevap oluşturuyor..."
            )

            response = client.chat.completions.create(

                model=MODEL,

                messages=messages,

                temperature=0.7,

                max_tokens=4096

            )

            print(
                "Groq cevap verdi."
            )

        # ==========================================
        # SADECE YAZI
        # ==========================================

        else:

            if not soru:

                return jsonify({

                    "cevap":
                    "Lütfen bir mesaj yaz."

                })

            # ==================================
            # MESAJI KAYDET
            # ==================================

            mesaji_kaydet(

                "kullanici",

                soru

            )

            # ==================================
            # ESKİ MESAJLARI ÖZETLE
            # ==================================

            eski_mesajlari_ozetle()

            # ==================================
            # MESAJLARI OLUŞTUR
            # ==================================

            messages = mesajlari_olustur()

            print(
                "Token tasarruflu sohbet ile "
                "Groq'a gönderiliyor..."
            )

            # ==================================
            # GROQ
            # ==================================

            response = client.chat.completions.create(

                model=MODEL,

                messages=messages,

                temperature=0.7,

                max_tokens=4096

            )

            print(
                "Groq cevap verdi."
            )

        # ==========================================
        # CEVAP
        # ==========================================

        cevap = response.choices[0].message.content

        if not cevap:

            cevap = (
                "❌ AI boş bir cevap döndürdü."
            )

        # ==========================================
        # AI CEVABINI KAYDET
        # ==========================================

        mesaji_kaydet(

            "ai",

            cevap

        )

        print(
            "Cevap:",
            cevap
        )

        return jsonify({

            "cevap":
            cevap

        })

    # ==========================================
    # HATA
    # ==========================================

    except Exception as e:

        print(
            "================================"
        )

        print(
            "GROQ / FLASK HATASI"
        )

        print(
            "================================"
        )

        print(
            repr(e)
        )

        print(
            "================================"
        )

        return jsonify({

            "cevap":
            "❌ Groq hatası:\n"
            + str(e)

        }), 500


# ==========================================
# SOHBETİ TEMİZLE
# ==========================================

@app.route(
    "/sohbet_temizle",
    methods=["POST"]
)
def sohbet_temizle():

    session.pop(
        "sohbet_gecmisi",
        None
    )

    session.pop(
        "sohbet_ozeti",
        None
    )

    return jsonify({

        "mesaj":
        "Sohbet geçmişi temizlendi."

    })


# ==========================================
# SITEMAP
# ==========================================

@app.route(
    "/sitemap.xml"
)
def sitemap():

    return """<?xml version="1.0" encoding="UTF-8"?>

<urlset
xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

<url>

<loc>
https://al-bq0g.onrender.com/
</loc>

<priority>
1.0
</priority>

</url>

</urlset>
""", 200, {

        "Content-Type":
        "application/xml"

    }


# ==========================================
# ROBOTS
# ==========================================

@app.route(
    "/robots.txt"
)
def robots():

    return """User-agent: *
Allow: /

Sitemap: https://al-bq0g.onrender.com/sitemap.xml
""", 200, {

        "Content-Type":
        "text/plain"

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

