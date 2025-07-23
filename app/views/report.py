import json
from django.http import JsonResponse
from django.shortcuts import render
import pandas as pd
from app.models import Data_Shift, MeasurementData, Parameter_Settings, paraTableData
import json
import pandas as pd
from django.http import JsonResponse
from app.models import MeasurementData, paraTableData ,Customer


def report(request):
    if request.method == 'POST':
        raw_data = request.POST.get('data')
        print("raw_data", raw_data)
        if raw_data:
            data = json.loads(raw_data)

            from_date = data.get('from_date')
            part_model = data.get('part_model')
            mode = data.get('mode')
            to_date = data.get('to_date')
            shift = data.get('shift')
            status = data.get('status')

            if not all([from_date, to_date, part_model]):
                return JsonResponse({'error': 'Missing required fields: from_date, to_date, or part_model'}, status=400)

            filter_kwargs = {
                'date__range': (from_date, to_date),
                'part_model': part_model,
            }

            if shift != "ALL":
                filter_kwargs['shift'] = shift

            if status != "ALL":
                filter_kwargs['overall_status'] = status

            filtered_data = MeasurementData.objects.filter(**filter_kwargs).order_by('date')

            if not filtered_data.exists():
                return JsonResponse({'error': 'NO DATA FOUND '}, status=404)

            data_dict = {
                'Date': [],
                'Job Numbers': [],
                'Shift': [],
                'Operator': [],
                'Status': [],
            }

            parameter_data = paraTableData.objects.filter(
                parameter_settings__part_model=part_model
            ).values('parameter_name', 'usl', 'lsl', 'utl', 'ltl').order_by('id')

            for param in parameter_data:
                param_name = param['parameter_name']
                usl = param['usl']
                lsl = param['lsl']
                key = f"{param_name} <br>{usl} <br>{lsl}"
                data_dict[key] = []

            unique_dates = set()
            grouped_data = {}
            for record in filtered_data:
                date = record.date.strftime('%d-%m-%Y %I:%M:%S %p')
                unique_dates.add(date)
                if date not in grouped_data:
                    grouped_data[date] = {
                        'Job Numbers': set(),
                        'Shift': record.shift,
                        'Operator': record.operator,
                        'Status': record.overall_status,
                        'Parameters': {
                            key: set() for key in data_dict if key not in ['Date', 'Shift', 'Operator', 'Status', 'Job Numbers']
                        }
                    }

                if record.comp_sr_no:
                    grouped_data[date]['Job Numbers'].add(record.comp_sr_no)

                for param in parameter_data:
                    param_name = param['parameter_name']
                    usl = param['usl']
                    lsl = param['lsl']
                    utl = param['utl']
                    ltl = param['ltl']
                    key = f"{param_name} <br>{usl} <br>{lsl}"

                    parameter_values = MeasurementData.objects.filter(
                        comp_sr_no=record.comp_sr_no,
                        date=record.date,
                        parameter_name=param_name
                    )

                    for pv in parameter_values:
                        value = None
                        if mode == 'max':
                            value = pv.max_value
                        elif mode == 'min':
                            value = pv.min_value
                        elif mode == 'tir':
                            value = pv.tir_value
                        elif mode == 'readings':
                            value = pv.output

                        value_to_display = value

                        
                        # Range-based coloring for 'max' or 'min' mode
                        if mode in ['max', 'min','readings'] and value is not None:
                            try:
                                value_float = float(value)
                                ltl = float(ltl)
                                lsl = float(lsl)
                                usl = float(usl)
                                utl = float(utl)

                                if value_float < ltl:
                                    bg_color = "red"
                                elif ltl <= value_float < lsl:
                                    bg_color = "yellow"
                                elif lsl <= value_float <= usl:
                                    bg_color = "#00ff00"
                                elif usl < value_float <= utl:
                                    bg_color = "yellow"
                                elif value_float > utl:
                                    bg_color = "red"
                                else:
                                    bg_color = "white"

                                value_to_display = f'<span style="background-color: {bg_color}; padding: 5px; border-radius: 3px;">{value}</span>'
                            except (ValueError, TypeError):
                                value_to_display = f'<span>{value}</span>'

                        grouped_data[date]['Parameters'][key].add(value_to_display)
            

            for date, group in grouped_data.items():
                data_dict['Date'].append(date)
                job_numbers_combined = "<br>".join(sorted(group['Job Numbers']))
                data_dict['Job Numbers'].append(job_numbers_combined)
                data_dict['Shift'].append(group['Shift'])
                data_dict['Operator'].append(group['Operator'])

                if mode in ['max', 'min', 'readings']:
                    status_final = 'ACCEPT'

                    for key, values in group['Parameters'].items():
                        for val in values:
                            if 'background-color: red' in val:
                                status_final = 'REJECT'
                                break
                            elif 'background-color: yellow' in val:
                                if status_final != 'REJECT':
                                    status_final = 'REWORK'
                        if status_final == 'REJECT':
                            break

                    status_colors = {
                        'ACCEPT': '#00ff00',
                        'REWORK': 'yellow',
                        'REJECT': 'red',
                    }
                    status_color = status_colors.get(status_final, 'transparent')
                    status_display = f'<span style="background-color: {status_color}; color: black; padding: 5px; border-radius: 3px;">{status_final}</span>'
                    data_dict['Status'].append(status_display)

                else:
                    # Leave status blank for 'tir' mode
                    data_dict['Status'].append('')



                for key, values in group['Parameters'].items():
                    data_dict[key].append("<br>".join(sorted(map(str, values))))

            df = pd.DataFrame(data_dict)
            df.index = df.index + 1
            table_html = df.to_html(index=True, escape=False, classes='table table-striped')

            return JsonResponse({
                'table_html': table_html,
                'total_count': len(unique_dates),
            })

    
    elif request.method == 'GET':
        shift_values = Data_Shift.objects.order_by('id').values_list('shift', 'shift_time').distinct()
        shift_name_queryset = Data_Shift.objects.order_by('id').values_list('shift', flat=True).distinct()
        shift_name = list(shift_name_queryset)
        print ("shift_name",shift_name)

        # Convert the QuerySet to a list of lists
        shift_values_list = list(shift_values)
        
        # Serialize the list to JSON
        shift_values_json = json.dumps(shift_values_list)
        print("shift_values_json",shift_values_json)

        customer = Customer.objects.first()
        primary_email = customer.primary_email if customer else ''
        secondary_email = customer.secondary_email if customer else ''
        print("Primary Email:", primary_email)
        print("Secondary Email:", secondary_email)

         # Create a context dictionary to pass the data to the template
        context = {
            'shift_values': shift_values_json,
            'shift_name':shift_name,
            'primary_email': primary_email,
            'secondary_email': secondary_email,
        }
    return render(request,'app/report.html',context)