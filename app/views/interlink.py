from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import pytz

from app.models import InterlinkData

@csrf_exempt  # Optional if you're passing CSRF token properly
def interlink(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Extract the date string
            date_str = data.get('date')  # e.g. '28/07/2025 10:12:00 AM'
            print("Original date string:", date_str)

            try:
                # Convert to datetime object
                date_obj = datetime.strptime(date_str, '%d/%m/%Y %I:%M:%S %p')

                # Make it timezone-aware (Asia/Kolkata)
                timezone = pytz.timezone('Asia/Kolkata')
                date_obj_aware = timezone.localize(date_obj)

                # Remove timezone info if needed
                date_obj_naive = date_obj_aware.replace(tzinfo=None)

                print("Timezone-aware date:", date_obj_aware)
                print("Naive date:", date_obj_naive)

            except ValueError as e:
                return JsonResponse({'status': 'error', 'message': f"Invalid date format: {str(e)}"}, status=400)

            # Get the other fields
            punch_no = data.get('punchNo')
            part_model = data.get('partModel')
            overall_status = data.get('overallStatusInput')

            print("INTERLINK DATA:", date_obj_naive, punch_no, part_model, overall_status)

              # ✅ Save to database
            InterlinkData.objects.create(
                Date_Time=date_obj_naive,
                PartModel=part_model,
                CompSrNo=punch_no,
                CompResultStatus=overall_status
            )

            return JsonResponse({'message': 'Data received successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST allowed'}, status=405)
