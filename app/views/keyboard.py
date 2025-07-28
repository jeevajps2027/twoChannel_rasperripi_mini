
from django.shortcuts import render
from django.http import JsonResponse
# from app.models import InterlinkData
from django.db import OperationalError
import json


def keyboard(request):
    # if request.method == 'GET':    
        
 
    #     data_list = InterlinkData.objects.using('client_db').filter(comp_sr_no='12345')

    #     print('data JJJJJJJJJJJJJJJJJJJJJJJJJ',data_list)

    #     if data_list.exists():
    #         data = data_list.first()
    #         # Prepare data dict to return
    #         data_dict = {
    #             'comp_sr_no': data.comp_sr_no,
    #             # add other fields you want to return
    #         }
    #         print('data',data_dict)

    return render(request,'app/keyboard.html')
        
        
