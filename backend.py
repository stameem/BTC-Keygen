from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
import io, requests, bitcoin, qrcode, mysql.connector, os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from datetime import datetime

app = FastAPI()

# --- Database helper ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mysql"),      # "mysql" will be the K8s Service name
        user=os.getenv("DB_USER", "btcuser"),
        password=os.getenv("DB_PASS", "btcpass"),
        database=os.getenv("DB_NAME", "btcdb"),
    )

# --- Routes ---

@app.post("/generate")
def generate_keys():
    """Generate Bitcoin keypair and store in DB."""
    private_key = bitcoin.random_key()
    public_key = bitcoin.pubtoaddr(bitcoin.privtopub(private_key))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO public_addresses (address, private_key) VALUES (%s, %s)",
        (public_key, private_key),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"private": private_key, "public": public_key}


@app.get("/count")
def get_count():
    """Return total number of addresses stored."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM public_addresses")
    (count,) = cur.fetchone()
    cur.close()
    conn.close()
    return {"count": count}


@app.get("/history/{page}")
def history(page: int = 0):
    """Fetch paginated history of generated addresses."""
    page_size = 100
    offset = page * page_size

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, address, generated_at
        FROM public_addresses
        ORDER BY generated_at ASC
        LIMIT %s OFFSET %s
    """, (page_size, offset))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {"rows": rows}


@app.get("/balance/{address}")
def check_balance(address: str):
    """Fetch balance of a Bitcoin address from blockchain.info API."""
    try:
        url = f"https://blockchain.info/balance?active={address}"
        response = requests.get(url, timeout=10)
        data = response.json()
        balance = data[address]["final_balance"] / 1e8
        return {"address": address, "balance": balance}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/download/{private}/{public}")
def download_pdf(private: str, public: str):
    """Generate a PDF with QR codes and key details."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # HEADER
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 80, "BITCOIN KEYPAIR")
    y = height - 140

    # PUBLIC KEY QR
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y + 29, "PUBLIC KEY:")
    qr_pub = qrcode.make(public)
    buf_pub = io.BytesIO(); qr_pub.save(buf_pub, format="PNG"); buf_pub.seek(0)
    c.drawImage(ImageReader(buf_pub), 180, y - 230, width=250, height=250)

    # PUBLIC KEY text
    text_obj = c.beginText(200, y - 250)
    text_obj.setFont("Helvetica", 10)
    for line in [public[i:i+70] for i in range(0, len(public), 70)]:
        text_obj.textLine(line)
    c.drawText(text_obj)

    y -= 260

    # PRIVATE KEY QR
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y - 20, "PRIVATE KEY:")
    y -= 25
    qr_priv = qrcode.make(private)
    buf_priv = io.BytesIO(); qr_priv.save(buf_priv, format="PNG"); buf_priv.seek(0)
    c.drawImage(ImageReader(buf_priv), 180, (y - 20) - 230, width=250, height=250)

    # PRIVATE KEY text
    text_obj = c.beginText(132, (y - 20) - 250)
    text_obj.setFont("Helvetica", 10)
    for line in [private[i:i+70] for i in range(0, len(private), 70)]:
        text_obj.textLine(line)
    c.drawText(text_obj)

    # FOOTER
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 100, "BITCOIN account holder: _____________________________________________")

    c.save()
    buffer.seek(0)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"bitcoin_keys_{timestamp}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/health")
def health():
    """Check DB connectivity."""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db_error": str(e)}
