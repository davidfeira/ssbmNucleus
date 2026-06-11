"""Encrypted-at-rest storage for the OpenRouter API key.

Windows: DPAPI (CryptProtectData) with user scope — the blob can only be
decrypted by this Windows account on this machine, no passphrase to manage.
Elsewhere: base64 obfuscation fallback (still better than the old plaintext
localStorage, but marked so the UI could warn someday).

File: STORAGE_PATH/openrouter.key — '<scheme>:<base64>' on one line.
Precedence for consumers: stored key, then the OPENROUTER_API_KEY env var.
"""
import base64
import logging
import os

from core.config import STORAGE_PATH

logger = logging.getLogger(__name__)

KEY_PATH = STORAGE_PATH / 'openrouter.key'


def _dpapi(data, encrypt):
    import ctypes
    import ctypes.wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [('cbData', ctypes.wintypes.DWORD),
                    ('pbData', ctypes.POINTER(ctypes.c_char))]

    buf = ctypes.create_string_buffer(data, len(data))
    blob_in = DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    fn = (ctypes.windll.crypt32.CryptProtectData if encrypt
          else ctypes.windll.crypt32.CryptUnprotectData)
    if not fn(ctypes.byref(blob_in), None, None, None, None, 0,
              ctypes.byref(blob_out)):
        raise OSError('DPAPI call failed')
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def save_key(key):
    """Persist (or clear, when empty) the OpenRouter key."""
    key = (key or '').strip()
    if not key:
        clear_key()
        return
    raw = key.encode('utf-8')
    if os.name == 'nt':
        try:
            payload = 'dpapi:' + base64.b64encode(_dpapi(raw, True)).decode('ascii')
        except OSError as e:
            logger.warning(f'[keystore] DPAPI encrypt failed ({e}); '
                           'falling back to obfuscation')
            payload = 'b64:' + base64.b64encode(raw).decode('ascii')
    else:
        payload = 'b64:' + base64.b64encode(raw).decode('ascii')
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    KEY_PATH.write_text(payload, encoding='utf-8')


def load_key():
    """The stored key, or None. Corrupt/undecryptable files read as None."""
    try:
        payload = KEY_PATH.read_text(encoding='utf-8').strip()
    except OSError:
        return None
    scheme, _, b64 = payload.partition(':')
    try:
        raw = base64.b64decode(b64)
        if scheme == 'dpapi':
            raw = _dpapi(raw, False)
        elif scheme != 'b64':
            return None
        return raw.decode('utf-8') or None
    except Exception as e:
        logger.warning(f'[keystore] could not read stored key: {e}')
        return None


def clear_key():
    KEY_PATH.unlink(missing_ok=True)


def get_openrouter_key():
    """The effective key: encrypted store first, env var fallback."""
    return load_key() or os.environ.get('OPENROUTER_API_KEY') or None
