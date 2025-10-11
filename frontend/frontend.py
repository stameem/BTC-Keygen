from nicegui import ui
import requests, io, base64, qrcode
from datetime import datetime
import os
from fastapi import FastAPI
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

API_URL = os.getenv("API_URL", "http://backend:8000")


@ui.page('/')
def home():
    state = {"private": None, "public": None}

    # --- FUNCTIONS ---
    def generate():
        resp = requests.post(f"{API_URL}/generate").json()
        state["private"] = resp["private"]
        state["public"] = resp["public"]

        # update QR codes + text
        buf_pub = io.BytesIO()
        qrcode.make(state["public"]).save(buf_pub, format='PNG')
        pub_qr.set_source(f"data:image/png;base64,{base64.b64encode(buf_pub.getvalue()).decode()}")
        pub_label.text = f"Public Key: {state['public']}"

        buf_priv = io.BytesIO()
        qrcode.make(state["private"]).save(buf_priv, format='PNG')
        priv_qr.set_source(f"data:image/png;base64,{base64.b64encode(buf_priv.getvalue()).decode()}")
        priv_label.text = f"Private Key: {state['private']}"

        # blockchain link
        blockchain_link.content = (
            f'<a href="https://www.blockchain.com/btc/address/{state["public"]}" '
            f'target="_blank" style="color:blue; text-decoration:underline;">'
            f'🔗 View on Blockchain.com</a>'
        )
        blockchain_link.visible = True
        blockchain_link.update()

        # update counter
        count = requests.get(f"{API_URL}/count").json()["count"]
        counter_label.text = f"Total Addresses Generated: {count}"

        balance_label.text = "Balance: Not checked"

    def check_balance():
        if not state["public"]:
            ui.notify("Generate keys first!")
            return
        resp = requests.get(f"{API_URL}/balance/{state['public']}").json()
        balance = resp.get("balance", "Error")
        balance_label.text = f"Balance: {balance} BTC"

    def download_pdf():
        if not state["private"] or not state["public"]:
            ui.notify("Generate keys first!")
            return

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            pdf_filename = f"bitcoin_keys_{timestamp}.pdf"

            # Create PDF directly in frontend
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            # Title
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width / 2, height - 80, "BITCOIN KEYPAIR")
            y = height - 140

            # Public Key Section
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, "PUBLIC KEY:")
            qr_pub = qrcode.make(state["public"])
            buf_pub = io.BytesIO()
            qr_pub.save(buf_pub, format="PNG")
            buf_pub.seek(0)
            c.drawImage(ImageReader(buf_pub), 200, y - 250, width=250, height=250)

            c.setFont("Helvetica", 10)
            text_x = 225
            text_y = y - 270
            for line in [state["public"][i:i+70] for i in range(0, len(state["public"]), 70)]:
                c.drawString(text_x, text_y, line)
                text_y -= 12

            # Private Key Section
            y -= 310
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, "PRIVATE KEY:")
            qr_priv = qrcode.make(state["private"])
            buf_priv = io.BytesIO()
            qr_priv.save(buf_priv, format="PNG")
            buf_priv.seek(0)
            c.drawImage(ImageReader(buf_priv), 200, y - 250, width=250, height=250)

            c.setFont("Helvetica", 10)
            text_x = 160
            text_y = y - 270
            for line in [state["private"][i:i+70] for i in range(0, len(state["private"]), 70)]:
                c.drawString(text_x, text_y, line)
                text_y -= 12

            # Footer
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 70, "BITCOIN account holder: _______________________________")

            c.save()
            buffer.seek(0)

            ui.download(buffer.getvalue(), filename=pdf_filename)
        except Exception as e:
            ui.notify(f"Error generating PDF: {e}")

    # --- UI Layout ---
    with ui.column().classes('w-full items-center'):
        ui.label('Bitcoin Private Key Generator').classes('text-3xl font-bold mb-6 text-center')

        with ui.row().classes('mb-4 justify-center'):
            ui.button('Generate Keys', on_click=generate).classes('bg-purple-500 text-white')
            ui.button('Check Balance', on_click=check_balance).classes('bg-blue-500 text-white')
            ui.button('Download PDF', on_click=download_pdf).classes('bg-green-500 text-white')

        blockchain_link = ui.html('', sanitize=False).classes('mb-4').style(
            'font-size:14px; padding:6px; border:1px solid #ccc; border-radius:4px; text-align:center;'
        )
        blockchain_link.visible = False

        with ui.row().classes('mb-6 justify-center'):
            with ui.column().classes('items-center'):
                pub_qr = ui.image().style('width:220px; height:220px;').classes('border p-2')
                ui.label('Public Key QR').classes('mt-1 text-center')
                pub_label = ui.label('').classes('text-sm mt-2 break-all text-center')
            with ui.column().classes('items-center'):
                priv_qr = ui.image().style('width:220px; height:220px;').classes('border p-2')
                ui.label('Private Key QR').classes('mt-1 text-center')
                priv_label = ui.label('').classes('text-sm mt-2 break-all text-center')

        balance_label = ui.label('Balance: —').classes('text-lg mb-2 font-semibold text-green-600')

        try:
            count = requests.get(f"{API_URL}/count").json()["count"]
        except Exception:
            count = 0
        counter_label = ui.label(f"Total Addresses Generated: {count}")

        ui.button('Show History', on_click=lambda: ui.navigate.to('/history')).classes('bg-gray-500 text-white mt-4')


@ui.page('/history')
def history():
    ui.label('Address History').classes('text-2xl font-bold mb-6')
    resp = requests.get(f"{API_URL}/history/0").json()
    ui.table(columns=[
        {'name': 'id', 'label': 'ID', 'field': 'id'},
        {'name': 'address', 'label': 'Address', 'field': 'address'},
        {'name': 'generated_at', 'label': 'Generated At', 'field': 'generated_at'},
    ], rows=resp['rows'])
    ui.button('Back to Home', on_click=lambda: ui.navigate.to('/')).classes('mt-4')


ui.run(title="Bitcoin Private Key Generator", host="0.0.0.0", port=8081)

