from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests, bitcoin, mysql.connector, os
from datetime import datetime

app = FastAPI()

# --- Database helper ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mysql"),      # "mysql" = service name in K8s
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


@app.get("/health")
def health():
    """Check DB connectivity."""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db_error": str(e)}
