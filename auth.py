"""NutriCoach — Autenticazione locale del nutrizionista.

Credenziali (username + password) salvate come hash PBKDF2-SHA256
(salt + 200k iterazioni) nella tabella `settings` del DB SQLite locale.
Nessun cloud, nessuna rete.
Il nutrizionista imposta username e password al primo avvio; poi deve
loggarsi con entrambi.
"""

import os
import sqlite3
import hashlib
import secrets
import db

PBKDF2_ITERS = 200_000


def _ensure_settings():
    conn = sqlite3.connect(db.DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)""")
    conn.commit()
    return conn


def get_username():
    conn = _ensure_settings()
    row = conn.execute("SELECT value FROM settings WHERE key='username'").fetchone()
    conn.close()
    return row[0] if row else ""


def has_account():
    conn = _ensure_settings()
    row = conn.execute("SELECT value FROM settings WHERE key='pw_hash'").fetchone()
    conn.close()
    return bool(row)


def set_account(username, password):
    """Crea/aggiorna l'account (username + password hash)."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERS)
    store = salt.hex() + "$" + dk.hex()
    conn = _ensure_settings()
    conn.execute("INSERT INTO settings(key,value) VALUES('username',?) "
                 "ON CONFLICT(key) DO UPDATE SET value=?", (username, username))
    conn.execute("INSERT INTO settings(key,value) VALUES('pw_hash',?) "
                 "ON CONFLICT(key) DO UPDATE SET value=?", (store, store))
    conn.commit(); conn.close()


def verify_password(username, password):
    conn = _ensure_settings()
    row = conn.execute("SELECT value FROM settings WHERE key='pw_hash'").fetchone()
    conn.close()
    if not row:
        return False
    # se e' stato impostato un username, deve coincidere
    stored_user = get_username()
    if stored_user and username and username != stored_user:
        return False
    salt_hex, dk_hex = row[0].split("$", 1)
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERS)
    return secrets.compare_digest(dk.hex(), dk_hex)


def clear_account():
    """Rimuove le credenziali (username + password). I dati clienti restano."""
    conn = _ensure_settings()
    conn.execute("DELETE FROM settings WHERE key IN ('username','pw_hash')")
    conn.commit(); conn.close()
