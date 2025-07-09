from datetime import datetime
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
from django.views.decorators.csrf import csrf_exempt
from app.models import MasterInterval, MeasurementData, Parameter_Settings, ParameterFactor,part_retrived, ComportSetting, Data_Shift,User_Data, master_data, paraTableData
import serial.tools.list_ports
from collections import defaultdict
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.db.models import Max


def get_available_com_ports():
    return [port.device for port in serial.tools.list_ports.comports()]


@csrf_exempt  # Add CSRF exemption only if not handling with CSRF token
def measurement(request):

    if request.method == 'POST':

        part_model_get = request.POST.get('part_model', '')
        print("part_model_get:", part_model_get)

        parameter_settings = Parameter_Settings.objects.filter(part_model=part_model_get).first()

        if parameter_settings is None:
            # Handle the case when no matching record is found
            return HttpResponse("No parameter settings found.", status=400)

        # Proceed with accessing the attributes
        part_name_value = parameter_settings.part_name
        char_lock_value = parameter_settings.char_lock
        char_lock_limit_value = parameter_settings.char_lock_limit
        punch_no_value = parameter_settings.punch_no


       

        related_data = paraTableData.objects.filter(parameter_settings__part_model=part_model_get).select_related('parameter_settings').order_by('id')

        
        # Extract and prepare data for response
        parameter_name_array = []
        channel_no_array = []
        low_master_array = []
        high_master_array = []
        nominal_array = []
        lsl_array = []
        usl_array = []
        ltl_array = []
        utl_array = []
        step_no_array = []
        auto_man_array = []
        timer_array = []
        digits_array = []
        single_double_array = []

        for data in related_data:
            parameter_name_array.append(data.parameter_name)
            channel_no_array.append(data.channel_no)
            low_master_array.append(data.low_master)
            high_master_array.append(data.high_master)
            nominal_array.append(data.nominal)
            lsl_array.append(data.lsl)
            usl_array.append(data.usl)
            ltl_array.append(data.ltl)
            utl_array.append(data.utl)
            step_no_array.append(data.step_no)
            auto_man_array.append(data.auto_man)
            timer_array.append(data.timer)
            digits_array.append(data.digits)
            single_double_array.append(data.single_double)

        parameter_factor_values = ParameterFactor.objects.filter(part_model=part_model_get).values('parameter_name','method','value').order_by('id')


        filtered_data = Parameter_Settings.objects.filter(
            part_model=part_model_get
        ).order_by('id')  # Ensures the order is by 'id'

        print('Filtered data from Parameter_Settings:', filtered_data)

        # Step 2: Get all `parameter_name` values from `paraTableData` related to `filtered_data`
        probe_no = paraTableData.objects.filter(
            parameter_settings__in=filtered_data
        ).values_list('channel_no', flat=True).distinct().order_by('parameter_settings__id')

        print('probe_no from paraTableData:', list(probe_no))


       


        # Convert probe_no list to integers (if they are strings)
        probe_no = list(map(int, probe_no))

        # Get the last stored `id` for each `probe_number`
        last_probes = (
            master_data.objects.filter(part_model=part_model_get, probe_number__in=probe_no)
            .values('probe_number')
            .annotate(last_id=Max('id'))  # Get the latest ID for each probe_number
        )
        existing_probe_nos = {entry['probe_number'] for entry in last_probes}
        missing_probe_nos = [p for p in probe_no if p not in existing_probe_nos]

        # Fetch complete details of the last stored entry for each `probe_number`
        last_probe_dict = {}
        for entry in last_probes:
            probe_number = entry['probe_number']
            last_id = entry['last_id']
            
            # Retrieve full record with this last_id
            last_record = master_data.objects.filter(id=last_id).values('id', 'probe_number', 'e', 'd', 'o1','a1','b1','b').first()
            
            if last_record:
                last_probe_dict[probe_number] = last_record


        # Format the data
        parameter_values = [
            {
                "probe_number": f"{probe_number}",
                "id": values.get("id"),
                "e": values.get("e"),
                "d": values.get("d"),
                "o1": values.get("o1"),
                "a1": values.get("a1"),
                "b1": values.get("b1"),
                "b" : values.get("b"), 
            }
            for probe_number, values in last_probe_dict.items()
        ]

         # Print values in the terminal
        for param in parameter_values:
            print(f"Probe Name: {param['probe_number']}, ID: {param['id']}, e: {param['e']}, d: {param['d']}, o1: {param['o1']}, a1: {param['a1']}, b1: {param['b1']}")

        # 1. Get the list of distinct parameter names related to the current part model
        parameter_name_val = paraTableData.objects.filter(
            parameter_settings__in=filtered_data
        ).values_list('parameter_name', flat=True).distinct().order_by('parameter_settings__id')

        print('parameter_name_val from paraTableData:', list(parameter_name_val))

        # 2. Get the last `id` for each parameter_name in MeasurementData
        latest_measurements = (
            MeasurementData.objects.filter(
                part_model=part_model_get,
                parameter_name__in=parameter_name_val
            )
            .values('parameter_name')
            .annotate(last_id=Max('id'))
        )

        # 3. Build a dictionary of last records with required fields
        last_measurement_dict = {}
        for entry in latest_measurements:
            param_name = entry['parameter_name']
            last_id = entry['last_id']

            last_record = MeasurementData.objects.filter(id=last_id).values(
                'id', 'parameter_name', 'output', 'max_value', 'min_value', 'tir_value'
            ).first()

            if last_record:
                last_measurement_dict[param_name] = last_record

        # 4. Format and print the result
        for param_name, values in last_measurement_dict.items():
            print(
                f"Parameter: {param_name}, ID: {values['id']}, "
                f"Output: {values['output']}, Max: {values['max_value']}, "
                f"Min: {values['min_value']}, TIR: {values['tir_value']}"
            )

        # Format the parameter_name values
        measurement_values = [
            {
                "parameter_name": param_name,
                "id": values.get("id"),
                "output": values.get("output"),
                "max_value": values.get("max_value"),
                "min_value": values.get("min_value"),
                "tir_value": values.get("tir_value"),
            }
            for param_name, values in last_measurement_dict.items()
        ]



        # Sending data in JSON format
        return JsonResponse({
            'part_name_value':part_name_value,
            'char_lock_value':char_lock_value,
            'char_lock_limit_value':char_lock_limit_value,
            'punch_no_value':punch_no_value,
            'parameter_name_array': parameter_name_array,
            'channel_no_array': channel_no_array,
            'low_master_array': low_master_array,
            'high_master_array': high_master_array,
            'nominal_array': nominal_array,
            'lsl_array': lsl_array,
            'usl_array': usl_array,
            'ltl_array': ltl_array,
            'utl_array': utl_array,
            'step_no_array': step_no_array,
            'auto_man_array': auto_man_array,
            'timer_array': timer_array,
            'digits_array': digits_array,
            'single_double_array':single_double_array,
            'parameter_values':parameter_values,
            'parameter_factor_values':list(parameter_factor_values),
             'missing_probes': missing_probe_nos,
             "measurement_data": measurement_values,
        })
    
    elif request.method == 'GET':
        ports_string = ''
        comport_com_port = ComportSetting.objects.values_list('com_port', flat=True).first()
        comport_baud_rate = ComportSetting.objects.values_list('baud_rate', flat=True).first()
        comport_parity = ComportSetting.objects.values_list('parity', flat=True).first()
        comport_stopbit = ComportSetting.objects.values_list('stop_bit', flat=True).first()
        comport_databit = ComportSetting.objects.values_list('data_bit', flat=True).first()


        print('Your baud_rate is this:', comport_baud_rate)
        print('Your COM port is:', comport_com_port)

        com_ports = get_available_com_ports()
        print('Your available COM ports are:', com_ports)

        if com_ports:
            if comport_com_port in com_ports:
                ports_string = comport_com_port
                print('Matching COM port found:', ports_string)
            else:
                ports_string = ', '.join(com_ports)
                print('No matching COM port found. Sending all available ports:', ports_string)
        else:
            ports_string = 'No COM ports available'
            print(ports_string)

        part_model = list(Parameter_Settings.objects.order_by('id').values_list('part_model', flat=True).distinct())
        print('Your part names from database:', part_model)


        try:
            part_model_name = part_retrived.objects.values_list('part_name', flat=True).distinct().get()
            print("part_model:", part_model)
        except part_retrived.DoesNotExist:
            part_model_name = None
            print("No part model found.")
        except part_retrived.MultipleObjectsReturned:
            print("Multiple part models found.")

        if part_model_name:
            
            # Filter Master_settings for the specific part_model
            latest_entry = master_data.objects.filter(part_model=part_model_name).order_by('-date_time').first()
            
            if latest_entry:
                # Extract and format the latest date_time
                last_stored_dates = latest_entry.date_time.strftime("%m-%d-%Y %I:%M:%S %p")
                print("Latest date_time jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj:", last_stored_dates)
            else:
                print("No entries found for the given part_model jjjjjjjjjjjjjjjjjjjjjjjjj.")


        user_name = list(User_Data.objects.all().values())
        print('your username is this from databse:',user_name)

        shift_time = list(Data_Shift.objects.all().order_by('id').values())
        print('Your received shift time is this:', shift_time)

        # Fetch all stored values
        new_part = part_retrived.objects.filter(id=1).values('part_name').first()  # Get part_name only

        if new_part:  # Check if data exists
            part_name = new_part['part_name']  # Extract part_name
            print('Part name:', part_name)  # Print only part_name

            # Check if part_name exists in part_model and move it to the first position
            if part_name in part_model:
                part_model.remove(part_name)  # Remove the part_name from its current position
                part_model.insert(0, part_name)  # Insert the part_name at index 0
                print('Updated part_model with part_name at first index:', part_model)
            else:
                print('Part name not found in part_model. No update made.')
        else:
            print('No data found!')  # Handle empty database

        

        username = request.session.get('username', 'Unknown User')

        # Log the username in the console
        print(f'Logged-in User: {username}')



        master_interval_settings = MasterInterval.objects.all()
        print("master_interval_settings:",master_interval_settings)

        for setting in master_interval_settings:
           
            print("Hour:", setting.hour)
            print("Minute:", setting.minute)
           
        # Convert the queryset to a list of dictionaries
        interval_settings_list = list(master_interval_settings.values())

        # Serialize the list to JSON
        interval_settings_json = json.dumps(interval_settings_list)




        


        

        context = {
            'part_model': part_model,
            'comport_com_port': comport_com_port,
            'ports_string': ports_string,
            'comport_baud_rate': comport_baud_rate,
            'comport_parity': comport_parity,
            'comport_stopbit': comport_stopbit,
            'comport_databit': comport_databit,
            'shift_time': json.dumps(shift_time),  # Pass serialized JSON data
            'user_name': json.dumps(user_name),
            'username':username,
            'last_stored_dates':last_stored_dates,
            'interval_settings_json':interval_settings_json,
        }

        return render(request, 'app/measurement.html', context)
