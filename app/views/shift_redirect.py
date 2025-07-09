from django.http import JsonResponse
from django.utils import timezone
from app.models import ShiftRedirectLog

def shift_redirect_status(request):
    shift_name = request.GET.get('shift')
    today = timezone.now().date()
    
    redirected = ShiftRedirectLog.objects.filter(shift_name=shift_name, date=today, redirected=True).exists()
    
    return JsonResponse({'redirected': redirected})


import json
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.http import JsonResponse


@csrf_exempt
def save_shift_redirect(request):
    if request.method == "POST":
        data = json.loads(request.body)
        shift_name = data.get('shift')
        today = timezone.now().date()
        print('your datais this from frontend is this to redirect :',data)

        log, created = ShiftRedirectLog.objects.get_or_create(
            shift_name=shift_name, date=today,
            defaults={'redirected': True}
        )

        if not created:
            log.redirected = True
            log.save()

        return JsonResponse({'status': 'ok'})