from nicegui import ui, app
import requests, io, base64, qrcode
from datetime import datetime
import os
#new
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import requests, io

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

        # Use the new proxy route instead of direct backend URL
        url = f"/download_proxy/{state['private']}/{state['public']}"

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ui.download(url, filename=f"bitcoin_keys_{timestamp}.pdf")

    #def download_pdf():
    #   if not state["private"] or not state["public"]:
    #        ui.notify("Generate keys first!")
    #        return
    #    url = f"{API_URL}/download/{state['private']}/{state['public']}"
    #    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #    ui.download(url, filename=f"bitcoin_keys_{timestamp}.pdf")

    # --- UI LAYOUT ---
    with ui.column().classes('w-full items-center'):
        # Title
        ui.label('Bitcoin Private Key Generator').classes('text-3xl font-bold mb-6 text-center')

        # Buttons row
        with ui.row().classes('mb-4 justify-center'):
            ui.button('Generate Keys', on_click=generate).classes('bg-purple-500 text-white')
            ui.button('Check Balance', on_click=check_balance).classes('bg-blue-500 text-white')
            ui.button('Download PDF', on_click=download_pdf).classes('bg-green-500 text-white')

        # Blockchain link (directly below buttons)
        blockchain_link = ui.html('').classes('mb-4').style(
            'font-size:14px; padding:6px; border:1px solid #ccc; border-radius:4px; text-align:center;'
        )
        blockchain_link.visible = False

        # QR codes with text under them
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

        # Counter (initialize with backend count)
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

@app.get("/download_proxy/{priv}/{pub}")
def download_proxy(priv: str, pub: str):
    """Proxy PDF download through frontend."""
    backend_url = f"http://backend:8000/download/{priv}/{pub}"
    response = requests.get(backend_url, stream=True)
    return StreamingResponse(
        io.BytesIO(response.content),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=bitcoin_keys.pdf"}
    )

ui.run(title="Bitcoin Private Key Generator", port=8081)


