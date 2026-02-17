"""
qz_signing_backend.py
=====================
QZ Tray Silent-Print — Python Signing Backend
==============================================

This module does TWO things:

  1.  Flask micro-server  (run_signing_server)
      ─────────────────────────────────────────
      Exposes a tiny signing endpoint:
          GET  /sign?request=<timestamp_string>
          → returns plain-text base64 SHA-512 signature

      The endpoint is called by the JavaScript in the browser every time QZ
      Tray requests a signature.  Because the signature matches the trusted
      certificate, QZ Tray skips the allow/deny popup entirely.

  2.  Helper functions used by voter_search_app.py
      ───────────────────────────────────────────────
      load_private_key()        – loads the RSA key from env / file
      load_public_cert_pem()    – loads the certificate PEM string
      sign_request(message)     – signs a UTF-8 string, returns base64

Architecture inside Streamlit
─────────────────────────────────────────────────────────────────────────────
  Streamlit runs on port 8501.
  The Flask signing server runs on port 8502 (same machine, different port).
  The QZ Tray JS in the browser calls http://localhost:8502/sign?request=...
  CORS headers allow the browser to reach the signing server cross-origin.

  Start the signing server once at app startup with start_signing_thread().
  It runs as a daemon thread — it dies automatically when Streamlit exits.

How to configure (choose ONE method)
─────────────────────────────────────────────────────────────────────────────
  Method A – file path in .env  (recommended for local dev)
      QZ_PRIVATE_KEY_PATH=qz_private_key.pem
      QZ_PUBLIC_CERT_PATH=qz_certificate.pem

  Method B – inline PEM in .env  (recommended for Streamlit Cloud)
      QZ_PRIVATE_KEY_PEM=-----BEGIN RSA PRIVATE KEY-----\\n...
      QZ_PUBLIC_CERT_PEM=-----BEGIN CERTIFICATE-----\\n...

  Method C – Streamlit Secrets  (st.secrets, same key names as above)

Requirements:
    pip install cryptography flask flask-cors
"""

from __future__ import annotations

import base64
import logging
import os
import threading
from typing import Optional

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers: credential loading
# ─────────────────────────────────────────────────────────────────────────────

def _get_env(key: str) -> str:
    """Read from os.environ, falling back to Streamlit secrets if available."""
    value = os.getenv(key, "")
    if value:
        return value.strip()
    try:
        import streamlit as st          # noqa: PLC0415
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return ""


def _unescape_pem(raw: str) -> str:
    """
    .env files store multi-line values as single-line with literal \\n.
    Convert them back to real newlines so the PEM parser is happy.
    """
    return raw.replace("\\n", "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Public: load key / certificate
# ─────────────────────────────────────────────────────────────────────────────

def load_private_key():
    """
    Load the RSA private key.

    Priority:
        1. QZ_PRIVATE_KEY_PEM  (inline PEM text)
        2. QZ_PRIVATE_KEY_PATH (path to .pem file)
        3. qz_private_key.pem  (default filename in CWD)

    Returns:
        cryptography RSAPrivateKey object, or None if not found.
    """
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.backends import default_backend

    # -- inline PEM --
    pem_text = _get_env("QZ_PRIVATE_KEY_PEM")
    if pem_text:
        pem_text = _unescape_pem(pem_text)
        try:
            key = load_pem_private_key(pem_text.encode(), password=None, backend=default_backend())
            log.info("QZ signing key loaded from QZ_PRIVATE_KEY_PEM env var.")
            return key
        except Exception as exc:
            log.error("Failed to parse QZ_PRIVATE_KEY_PEM: %s", exc)

    # -- file path --
    path = _get_env("QZ_PRIVATE_KEY_PATH") or "qz_private_key.pem"
    if os.path.isfile(path):
        try:
            with open(path, "rb") as fh:
                key = load_pem_private_key(fh.read(), password=None, backend=default_backend())
            log.info("QZ signing key loaded from file: %s", path)
            return key
        except Exception as exc:
            log.error("Failed to load private key from %s: %s", path, exc)

    log.warning(
        "QZ private key not found.  Silent printing will be disabled.\n"
        "Run:  python generate_qz_certs.py  then set QZ_PRIVATE_KEY_PATH in .env"
    )
    return None


def load_public_cert_pem() -> str:
    """
    Load the public certificate PEM string (injected into the JS page).

    Priority:
        1. QZ_PUBLIC_CERT_PEM  (inline PEM text)
        2. QZ_PUBLIC_CERT_PATH (path to .pem file)
        3. qz_certificate.pem  (default filename in CWD)

    Returns:
        PEM string (with real newlines), or empty string if not found.
    """
    # -- inline PEM --
    pem_text = _get_env("QZ_PUBLIC_CERT_PEM")
    if pem_text:
        return _unescape_pem(pem_text)

    # -- file path --
    path = _get_env("QZ_PUBLIC_CERT_PATH") or "qz_certificate.pem"
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    log.warning("QZ public cert not found — JS will not inject trusted certificate.")
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Public: sign a request message
# ─────────────────────────────────────────────────────────────────────────────

def sign_request(message: str, private_key=None) -> Optional[str]:
    """
    Sign a UTF-8 message string with RSA/SHA-512 (PKCS1v15).

    This is exactly what QZ Tray expects:
        QZ sends a timestamp string → backend signs it → JS passes sig to qz.sign().

    Args:
        message:     The raw string QZ Tray sent (e.g. "2024-01-15T12:34:56.789Z")
        private_key: Optional pre-loaded key; loads from env/file if None.

    Returns:
        Base-64 encoded signature string, or None on failure.
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    if private_key is None:
        private_key = load_private_key()

    if private_key is None:
        log.error("Cannot sign: no private key available.")
        return None

    try:
        signature = private_key.sign(
            message.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA512(),
        )
        return base64.b64encode(signature).decode("ascii")
    except Exception as exc:
        log.error("Signing failed: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Flask signing server
# ─────────────────────────────────────────────────────────────────────────────

SIGNING_SERVER_PORT = 8502  # change if 8502 is taken on your machine

# Singleton: we only start the server once per process
_server_started = False
_server_lock    = threading.Lock()


def run_signing_server(port: int = SIGNING_SERVER_PORT) -> None:
    """
    Start the Flask signing server (blocking — call in a background thread).

    Endpoint:
        GET  /sign?request=<message>
        → 200 plain-text base64 signature
        → 500 if key is missing

        GET  /health
        → 200  {"status": "ok", "key_loaded": true/false}
    """
    try:
        from flask import Flask, request, jsonify
        from flask_cors import CORS
    except ImportError:
        log.error(
            "Flask / flask-cors not installed.\n"
            "Install with:  pip install flask flask-cors"
        )
        return

    app = Flask(__name__)
    CORS(app)  # allow the browser (localhost:8501) to call localhost:8502

    # Pre-load the key once when the server starts
    _key = load_private_key()

    @app.route("/sign")
    def sign_endpoint():
        """
        QZ Tray JS calls this URL:
            fetch(`http://localhost:${SIGNING_PORT}/sign?request=${encodedMsg}`)
        """
        raw_msg = request.args.get("request", "")
        if not raw_msg:
            return "Missing 'request' query parameter", 400

        sig = sign_request(raw_msg, private_key=_key)
        if sig is None:
            return "Signing failed — private key not loaded", 500

        # Return plain text, not JSON — QZ Tray expects raw base64
        return sig, 200, {"Content-Type": "text/plain; charset=utf-8"}

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "key_loaded": _key is not None})

    log.info("QZ signing server starting on port %d …", port)
    # use_reloader=False is critical inside a thread
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def start_signing_thread(port: int = SIGNING_SERVER_PORT) -> bool:
    """
    Start the Flask signing server in a daemon background thread.
    Safe to call multiple times — only starts once per process.

    Returns:
        True  if the server was (or already was) started.
        False if the key is missing (server won't help without a key).
    """
    global _server_started

    with _server_lock:
        if _server_started:
            return True

        if load_private_key() is None:
            log.warning(
                "QZ signing server NOT started — private key is missing.\n"
                "Run generate_qz_certs.py and configure QZ_PRIVATE_KEY_PATH."
            )
            return False

        t = threading.Thread(
            target=run_signing_server,
            args=(port,),
            daemon=True,      # thread dies when the main process exits
            name="qz-signing-server",
        )
        t.start()
        _server_started = True
        log.info("QZ signing thread started (port %d).", port)
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Quick self-test (python qz_signing_backend.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    key = load_private_key()
    if key is None:
        print("\n❌  Private key not found.")
        print("    Run:  python generate_qz_certs.py")
    else:
        test_msg = "2024-01-15T12:34:56.789Z"
        sig = sign_request(test_msg, private_key=key)
        print(f"\n✅  Sign test OK")
        print(f"    Input   : {test_msg}")
        print(f"    Signature (first 60 chars): {sig[:60]}…")

        cert_pem = load_public_cert_pem()
        if cert_pem:
            print(f"\n✅  Certificate loaded ({len(cert_pem)} bytes)")
        else:
            print("\n⚠️   Certificate PEM not found — run generate_qz_certs.py")

        print("\nStarting signing server on port 8502 (Ctrl-C to stop)…")
        run_signing_server()
