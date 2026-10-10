def safe_serialize(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple, set)):
        return [safe_serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): safe_serialize(item) for key, item in value.items()}
    if hasattr(value, "to_dict"):
        return safe_serialize(value.to_dict())
    if hasattr(value, "__dict__"):
        return safe_serialize(vars(value))
    return str(value)
