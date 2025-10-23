from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests, bitcoin, mysql.connector, os
from datetime import datetime

# Initialising API
app = FastAPI()

# Connect to Database with its credentials
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mysql"),
        user=os.getenv("DB_USER", "btcuser"),
        password=os.getenv("DB_PASS", "btcpass"),
        database=os.getenv("DB_NAME", "btcdb"),
    )

# Generate bitcoin keys and store in Database
@app.post("/generate")
def generate_keys():
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


# It returns the count of public address generated
@app.get("/count")
def get_count():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM public_addresses")
    (count,) = cur.fetchone()
    cur.close()
    conn.close()
    return {"count": count}


# Shows history of last 100 public address generated
@app.get("/history/{page}")
def history(page: int = 0):
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

# It fetches bitcoin balance using API from blockchain.info
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

# Check wether Database is connected
@app.get("/health")
def health():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db_error": str(e)}

