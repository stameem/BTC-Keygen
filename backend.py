# backend_nosql.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
import io, requests, bitcoin, qrcode
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from datetime import datetime

app = FastAPI()

# in-memory storage instead of MySQL
addresses = []   # list of {"id": int, "address": str, "generated_at": str}

@app.post("/generate")
def generate_keys():
    private_key = bitcoin.random_key()
    public_key = bitcoin.pubtoaddr(bitcoin.privtopub(private_key))
    addresses.append({
        "id": len(addresses) + 1,
        "address": public_key,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "private": private_key
    })
    return {"private": private_key, "public": public_key}

@app.get("/count")
def get_count():
    return {"count": len(addresses)}

@app.get("/balance/{address}")
def check_balance(address: str):
    try:
        url = f"https://blockchain.info/balance?active={address}"
        response = requests.get(url, timeout=10)
        data = response.json()
        balance = data[address]["final_balance"] / 1e8
        return {"address": address, "balance": balance}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/history/{page}")
def history(page: int = 0):
    page_size = 100
    start = page * page_size
    end = start + page_size
    return {"rows": addresses[start:end]}

@app.get("/download/{private}/{public}")
def download_pdf(private: str, public: str):
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

    c.setFont("Helvetica", 10)
    c.drawString(50, 80, f"Public Key: {public}")
    c.drawString(50, 65, f"Private Key: {private}")

    c.save()
    buffer.seek(0)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"bitcoin_keys_{timestamp}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

