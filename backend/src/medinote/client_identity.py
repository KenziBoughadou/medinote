import hashlib
import hmac
import ipaddress
from datetime import UTC, datetime

from medinote.errors import ServiceError


def normalize_client_ip(value):
    if not value or "%" in value:
        raise ValueError("Adresse IP invalide")
    address = ipaddress.ip_address(value)
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.compressed


def derive_client_key(secret, date_utc, ip):
    return hmac.new(
        bytes.fromhex(secret), (date_utc + normalize_client_ip(ip)).encode(), hashlib.sha256
    ).hexdigest()


def request_client_key(request):
    settings = request.app.state.settings
    # Les headers de proxy ne sont jamais une identité en développement.
    if settings.env != "production":
        raise ServiceError(
            "CLIENT_ADDRESS_UNAVAILABLE", "Relances publiques désactivées en mode local.", 503
        )
    try:
        key = settings.quota_hmac_key.get_secret_value() if settings.quota_hmac_key else ""
        if not key:
            raise ValueError("clé absente")
        return derive_client_key(
            key, datetime.now(UTC).date().isoformat(), request.headers.get("x-medinote-client-ip")
        )
    except ValueError:
        raise ServiceError(
            "CLIENT_ADDRESS_UNAVAILABLE", "Adresse visiteur Cloudflare indisponible.", 503
        ) from None
