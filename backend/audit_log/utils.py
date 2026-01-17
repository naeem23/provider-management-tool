from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


def serialize_for_json(data):
    """
    Recursively convert non-JSON-serializable objects
    (datetime, date, Decimal, UUID) into safe values.
    """
    if isinstance(data, dict):
        return {k: serialize_for_json(v) for k, v in data.items()}

    if isinstance(data, list):
        return [serialize_for_json(v) for v in data]

    if isinstance(data, UUID):
        return str(data)

    if isinstance(data, (datetime, date)):
        return data.isoformat()

    if isinstance(data, Decimal):
        return float(data)

    return data
