import aiohttp

import config


_session = None


def get_session() -> aiohttp.ClientSession:
    """Return one pooled HTTP session for the lifetime of the application."""
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(
            total=config.TIMEOUT,
            connect=config.CONNECT_TIMEOUT,
        )
        connector = aiohttp.TCPConnector(ttl_dns_cache=config.DNS_CACHE_TTL)
        _session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    return _session


async def close_session():
    global _session
    if _session is not None and not _session.closed:
        await _session.close()
    _session = None
