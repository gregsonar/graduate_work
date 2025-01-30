from django.http import JsonResponse
from django.db import connection

def healthcheck(request):
    try:
        return JsonResponse({"status": "ok"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)