from rest_framework.views import exception_handler
from rest_framework.response import Response


def api_exception_handler(exc, context):
    """
    Formato padronizado de erros para o app mobile:
    {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Descrição legível.",
            "detail": { ... }   <- campos com erros, quando aplicável
        }
    }
    """
    response = exception_handler(exc, context)

    if response is None:
        return None

    original_data = response.data

    # DRF retorna listas ou dicts com campos — normalizamos para o formato padrão
    if isinstance(original_data, list):
        detail = original_data
        message = original_data[0] if original_data else "Erro desconhecido."
    elif isinstance(original_data, dict):
        detail = original_data
        message = original_data.get("detail", "Erro na requisição.")
    else:
        detail = None
        message = str(original_data)

    code = _status_to_code(response.status_code, original_data)

    response.data = {
        "error": {
            "code": code,
            "message": str(message),
            "detail": detail if detail != {"detail": message} else None,
        }
    }

    return response


def _status_to_code(status_code: int, data) -> str:
    if status_code == 400:
        return "VALIDATION_ERROR"
    if status_code == 401:
        return "UNAUTHORIZED"
    if status_code == 403:
        return "FORBIDDEN"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 405:
        return "METHOD_NOT_ALLOWED"
    if status_code == 429:
        return "RATE_LIMIT_EXCEEDED"
    return f"HTTP_{status_code}"
