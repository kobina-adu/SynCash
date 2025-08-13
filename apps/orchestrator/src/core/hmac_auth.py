import hmac
import hashlib
import time
import structlog
from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
from src.config.settings import get_settings
from src.core.redis_client import get_redis_client

logger = structlog.get_logger(__name__)

HMAC_HEADER = "X-Signature"
TIMESTAMP_HEADER = "X-Timestamp"
NONCE_HEADER = "X-Nonce"

async def verify_hmac_request(request: Request):
    settings = get_settings()
    hmac_secret = settings.hmac_secret.encode()
    window = settings.hmac_window_seconds

    # Extract headers
    signature = request.headers.get(HMAC_HEADER)
    timestamp = request.headers.get(TIMESTAMP_HEADER)
    nonce = request.headers.get(NONCE_HEADER)

    if not signature or not timestamp or not nonce:
        logger.warning("Missing HMAC headers")
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Missing HMAC headers")

    # Check timestamp window
    now = int(time.time())
    try:
        ts = int(timestamp)
    except Exception:
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Invalid timestamp")
    if abs(now - ts) > window:
        logger.warning("Stale timestamp", now=now, ts=ts)
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Stale timestamp")

    # Check nonce (prevent replay)
    redis = await get_redis_client()
    nonce_key = f"hmac_nonce:{nonce}"
    if await redis.get(nonce_key):
        logger.warning("Replay detected: nonce reused", nonce=nonce)
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Nonce already used")
    await redis.set(nonce_key, "1", ex=window)

    # Compute expected signature
    body = await request.body()
    msg = body + timestamp.encode() + nonce.encode()
    expected = hmac.new(hmac_secret, msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        logger.warning("Invalid HMAC signature", expected=expected, got=signature)
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Invalid HMAC signature")
    # Success
    logger.info("HMAC verified", nonce=nonce, ts=ts)
