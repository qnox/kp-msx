import json
import logging
import re
from collections import OrderedDict, deque
from datetime import datetime, timezone
from time import monotonic


_logger = logging.getLogger('uvicorn.error')
_recent_events = deque(maxlen=200)
_rate_windows = OrderedDict()
_url_pattern = re.compile(r'https?://\S+', re.IGNORECASE)
_text_fields = {'event', 'session', 'detail', 'type'}
_number_fields = {'ready_state', 'network_state', 'current_time', 'duration', 'code'}
_boolean_fields = {'fatal'}


def allow_client_event(client_ip, limit=120, window_seconds=60):
    key = client_ip or 'unknown'
    now = monotonic()
    timestamps = _rate_windows.pop(key, deque())
    while timestamps and now - timestamps[0] >= window_seconds:
        timestamps.popleft()
    allowed = len(timestamps) < limit
    if allowed:
        timestamps.append(now)
    _rate_windows[key] = timestamps
    while len(_rate_windows) > 256:
        _rate_windows.popitem(last=False)
    return allowed


def _clean_text(value, limit):
    if value is None:
        return None
    value = _url_pattern.sub('[url]', str(value))
    return value[:limit]


def record_client_event(payload, client_ip=None, user_agent=None):
    if not isinstance(payload, dict):
        raise ValueError('Payload must be an object')

    event_name = _clean_text(payload.get('event'), 64)
    if not event_name:
        raise ValueError('Event name is required')

    event = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': event_name,
    }

    for key in _text_fields - {'event'}:
        if key in payload:
            event[key] = _clean_text(payload[key], 500 if key == 'detail' else 64)

    for key in _number_fields:
        value = payload.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            event[key] = value

    for key in _boolean_fields:
        value = payload.get(key)
        if isinstance(value, bool):
            event[key] = value

    if client_ip:
        event['client_ip'] = _clean_text(client_ip.split(',')[0].strip(), 64)
    if user_agent:
        event['user_agent'] = _clean_text(user_agent, 200)

    _recent_events.append(event)
    _logger.info('client_event %s', json.dumps(event, separators=(',', ':'), ensure_ascii=False))
    return event


def recent_client_events(limit=50):
    limit = max(1, min(int(limit), 200))
    return list(_recent_events)[-limit:]
