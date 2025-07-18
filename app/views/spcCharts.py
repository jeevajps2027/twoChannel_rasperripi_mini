import json
from django.http import JsonResponse
import numpy as np
import pandas as pd

from django.shortcuts import render
import matplotlib.pyplot as plt
import io
import base64

from app.models import Customer, Data_Shift, MeasurementData, Parameter_Settings, paraTableData


def encode_chart_to_base64(fig):
    """Encodes a Matplotlib figure to a base64 image string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)  # Close the figure to free memory
    return image_base64


def generate_r_chart(readings, sample_size):
    """Generates an X-bar and R chart and returns the image as a base64 string."""
    subgroups = [readings[i:i + sample_size] for i in range(0, len(readings), sample_size)]
    x_bar = [np.mean(group) for group in subgroups]
    r_values = [np.max(group) - np.min(group) for group in subgroups]

    fig, axs = plt.subplots(2, 1, figsize=(12, 6), dpi=100)
    fig.patch.set_facecolor('gray')  # Light gray background for full chart

    # Set background color for each subplot
    for ax in axs:
        ax.set_facecolor("#b1aeae")  # Slightly darker gray for individual plots


    # === X-bar Chart ===
    axs[0].plot(x_bar, marker='o', label='X-bar', linewidth=3.5, color='blue')
    axs[0].set_title('X-bar Chart', fontsize=20, fontweight='bold')
    axs[0].set_xlabel('Subgroup', fontsize=18, fontweight='bold')
    axs[0].set_ylabel('X-bar', fontsize=16, fontweight='bold')
    axs[0].tick_params(axis='both', labelsize=16)  # Tick font size
    axs[0].legend(fontsize=14)

    # === R Chart ===
    axs[1].plot(r_values, marker='o', color='red', label='Range', linewidth=3.5)
    axs[1].set_title('R Chart', fontsize=20, fontweight='bold')
    axs[1].set_xlabel('Subgroup', fontsize=18, fontweight='bold')
    axs[1].set_ylabel('Range', fontsize=16, fontweight='bold')
    axs[1].tick_params(axis='both', labelsize=16)
    axs[1].legend(fontsize=14)

    plt.tight_layout()
    return encode_chart_to_base64(fig)

def generate_readings_table(subgroups, x_bars, ranges):
    """
    Generates an HTML table for subgroup readings with sum, mean, and range rows.
    Limits to 20 columns, and shows alert if more data is present.
    """
    max_columns = 20
    df = pd.DataFrame(subgroups).transpose()

    alert_message = ""
    if df.shape[1] > max_columns:
        df = df.iloc[:, :max_columns]
        alert_message = """
        <script>
            alert("Only the first 20 subgroups are displayed. Some data is hidden.");
        </script>
        """

    df.columns = [f'X{i + 1}' for i in range(df.shape[1])]
    df.loc['Sum'] = df.sum()
    df.loc['X̄ (Mean)'] = x_bars[:max_columns]
    df.loc['R̄ (Range)'] = ranges[:max_columns]

    style = """
    <style>
    .table-wrapper {
        max-height: 70vh;  /* Adjust as needed */
        overflow-x: auto;
        overflow-y: auto;
        border: 1px solid #ccc;
    }

    table.table {
        font-size: 1.4vw;
        width: max-content; /* ensures horizontal scroll when needed */
        height: 100%;
        border-collapse: collapse;
    }

    table.table th, table.table td {
        padding: 2px;
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        border: 1px solid #ccc;
    }

    table.table th {
        background-color: black;
        color: white;
        border: 1px solid white;
    }
</style>
"""

    return alert_message + style + df.to_html(classes="table table-striped", index=True, header=True)


def generate_histogram(readings, usl=None, lsl=None):
    """Generates a histogram and returns the image and a summary table as HTML."""
    import numpy as np
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12,6), dpi=100)
    
    # Optional background color
    fig.patch.set_facecolor('gray')
    ax.set_facecolor('#b1aeae')

    # Plot histogram with thicker bars
    ax.hist(readings, bins=10, color='blue', edgecolor='black', linewidth=2.5)

    # Set bold, larger titles and labels
    ax.set_title('Histogram', fontsize=20, fontweight='bold')
    ax.set_xlabel('Readings', fontsize=18, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=18, fontweight='bold')
    ax.tick_params(axis='both', labelsize=16)

    # Plot USL and LSL as vertical dashed lines (thicker)
    if usl:
        try:
            ax.axvline(float(usl), color='red', linestyle='--', linewidth=3, label='USL')
        except ValueError:
            pass

    if lsl:
        try:
            ax.axvline(float(lsl), color='red', linestyle='--', linewidth=3, label='LSL')
        except ValueError:
            pass

    ax.legend(fontsize=12)
    plt.tight_layout()

    chart_img = encode_chart_to_base64(fig)
    


    # Prepare stats
    count = len(readings)
    usl_val = float(usl) if usl not in [None, '', 'N/A'] else None
    lsl_val = float(lsl) if lsl not in [None, '', 'N/A'] else None
    x_bar = np.mean(readings)
    std_dev = np.std(readings)

    cp = None
    cpk = None

    if usl_val is not None and lsl_val is not None and std_dev > 0:
        cp = (usl_val - lsl_val) / (6 * std_dev)
        cpk = min((usl_val - x_bar), (x_bar - lsl_val)) / (3 * std_dev)

    # Build HTML table (headings in one row, values in the next)
    table_html = f"""
    <table border="1" style="width: 80%; border-collapse: collapse; text-align: center;">
        <tr>
        <th style="background-color: black; color: white; border: 1px solid white;">Total Readings</th>
        <th style="background-color: black; color: white; border: 1px solid white;">USL</th>
        <th style="background-color: black; color: white; border: 1px solid white;">LSL</th>
        <th style="background-color: black; color: white; border: 1px solid white;">Mean</th>
        <th style="background-color: black; color: white; border: 1px solid white;">Std Dev</th>
        <th style="background-color: black; color: white; border: 1px solid white;">Cp</th>
        <th style="background-color: black; color: white; border: 1px solid white;">Cpk</th>
    </tr>
        <tr>
            <td>{count}</td>
            <td>{usl if usl is not None else 'N/A'}</td>
            <td>{lsl if lsl is not None else 'N/A'}</td>
            <td>{round(x_bar, 4)}</td>
            <td>{round(std_dev, 4)}</td>
            <td>{round(cp, 4) if cp is not None else 'N/A'}</td>
            <td>{round(cpk, 4) if cpk is not None else 'N/A'}</td>
        </tr>
    </table>
    """

    return chart_img, table_html


def generate_pie_chart(status, usl=None, lsl=None):
    """Generates a centered, styled pie chart and returns a base64 string."""

    import pandas as pd
    import matplotlib.pyplot as plt

    # Count the occurrences of each unique status
    status_series = pd.Series(status)
    status_counts = status_series.value_counts()

    # Map colors for the pie chart
    colors = {
        'accept': '#32CD32',  # Parrot green
        'reject': '#FF6347',  # Tomato red
        'rework': '#FFFF00',  # Yellow
    }
    pie_colors = [colors.get(key.lower(), '#808080') for key in status_counts.index]  # Default to gray

    # Create figure with increased size and background
    fig, ax = plt.subplots(figsize=(12,6), dpi=100)
    fig.patch.set_facecolor('gray')  # Light background

    # Generate the pie chart with increased font sizes
    wedges, texts, autotexts = ax.pie(
        status_counts,
        labels=status_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=pie_colors,
        textprops={'fontsize': 20, 'weight': 'bold'},     # Label font size and weight
        wedgeprops={'linewidth': 3.5, 'edgecolor': 'black'}  # Optional border
    )

    # Customize percentage labels
    for autotext in autotexts:
        autotext.set_fontsize(20)
        autotext.set_fontweight('bold')

    # Set bold title with increased size
    ax.set_title('Status Distribution', fontsize=20, fontweight='bold')

    # Equal aspect ratio ensures pie is circular
    ax.axis('equal')

    # Tight layout
    plt.tight_layout()

    # Encode chart as base64
    chart_img = encode_chart_to_base64(fig)
   


    # Calculate counts and percentages
    total_count = len(status)
    accept_count = (status_series.str.lower() == 'accept').sum()
    reject_count = (status_series.str.lower() == 'reject').sum()
    rework_count = (status_series.str.lower() == 'rework').sum()

    accept_pct = accept_count * 100 / total_count if total_count else 0
    reject_pct = reject_count * 100 / total_count if total_count else 0
    rework_pct = rework_count * 100 / total_count if total_count else 0

    # Build HTML table with all data in a single row
    table_html = f"""
    <table border="1" style="width: 80%; border-collapse: collapse; text-align: center;">
        <tr>
            <th style="background-color: black; color: white; border: 1px solid white;">Total Count</th>
            <th style="background-color: black; color: white; border: 1px solid white;">Accept Count</th>
            <th style="background-color: black; color: white; border: 1px solid white;">Accept %</th>
            <th style="background-color: black; color: white; border: 1px solid white;">Reject Count</th>
            <th style="background-color: black; color: white; border: 1px solid white;">Reject %</th>
            <th style="background-color: black; color: white; border: 1px solid white;">Rework Count</th>
            <th style="background-color: black; color: white; border: 1px solid white;">Rework %</th>
        </tr>
        <tr>
            <td>{total_count}</td>
            <td>{accept_count}</td>
            <td>{round(accept_pct, 2)}%</td>
            <td>{reject_count}</td>
            <td>{round(reject_pct, 2)}%</td>
            <td>{rework_count}</td>
            <td>{round(rework_pct, 2)}%</td>
        </tr>
    </table>
    """

    return chart_img, table_html

def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

def spcCharts(request):
    if request.method == 'POST':
        raw_data = request.POST.get('data')
        if raw_data:
            data = json.loads(raw_data)

            from_date = data.get('from_date')
            part_model = data.get('part_model')
            parameter_name = data.get('parameter_name')
            mode = data.get('mode')  # Can be 'r_chart', 'histogram', or 'piechart'
            sample_size = int(data.get('sample_size'))
            to_date = data.get('to_date')
            shift = data.get('shift')


            print("parameter_name kkkkkkkkkkkkkkkkkkkk",parameter_name)

            if not all([from_date, to_date, part_model]):
                return JsonResponse({'error': 'Missing required fields: from_date, to_date, or part_model'}, status=400)

            # Query filter setup
            filter_kwargs = {
                'date__range': (from_date, to_date),
                'part_model': part_model,
            }
            if shift != "ALL":
                filter_kwargs['shift'] = shift
            if parameter_name != "ALL":
                filter_kwargs['parameter_name'] = parameter_name

            filtered_data = MeasurementData.objects.filter(**filter_kwargs).order_by('date')
            print("")
            filtered_list = filtered_data.values('output')
            filtered_result = filtered_data.values('overall_status')

            # Get USL and LSL if specific parameter is selected
            usl = None
            lsl = None
            ltl = None
            utl = None

            if parameter_name != "ALL":
                try:
                    # Get matching Parameter_Settings
                    setting = Parameter_Settings.objects.get(part_model=part_model)

                    # Get matching paraTableData
                    para_data = paraTableData.objects.get(
                        parameter_settings=setting,
                        parameter_name=parameter_name
                    )

                    # Convert limits to float safely
                    usl = safe_float(para_data.usl)
                    lsl = safe_float(para_data.lsl)
                    utl = safe_float(para_data.utl)
                    ltl = safe_float(para_data.ltl)

                    print("USL:", usl, "LSL:", lsl, "UTL:", utl, "LTL:", ltl)

                except (Parameter_Settings.DoesNotExist, paraTableData.DoesNotExist):
                    usl = lsl = utl = ltl = None
                    print("Thresholds not found for the given parameter.")

            if not filtered_list:
                return JsonResponse({'error': 'No data found for the given criteria'}, status=404)

            # Extract readings
            readings = []
            for r in filtered_list:
                try:
                    readings.append(float(r['output']))
                except (ValueError, TypeError):
                    readings.append(None)

            # Evaluate status based on value_float and limits
            status = []
            for value_float in readings:
                if value_float is None or None in (ltl, lsl, usl, utl):
                    status.append("UNKNOWN")  # Missing value or thresholds
                elif value_float < ltl:
                    status.append("REJECT")
                elif ltl <= value_float < lsl:
                    status.append("REWORK")
                elif lsl <= value_float <= usl:
                    status.append("ACCEPT")
                elif usl < value_float <= utl:
                    status.append("REWORK")
                elif value_float > utl:
                    status.append("REJECT")
                else:
                    status.append("UNKNOWN")  # Fallback for edge cases

            print("Evaluated Status:", status)
            print("Status Length:", len(status))

            # Generate the chart based on mode
            chart_img = None
            table_html = None
            if mode == 'r_chart':
                chart_img = generate_r_chart(readings, sample_size)
                subgroups = [readings[i:i + sample_size] for i in range(0, len(readings), sample_size)]
                x_bars = [np.mean(group) for group in subgroups]
                ranges = [np.max(group) - np.min(group) for group in subgroups]
                table_html = generate_readings_table(subgroups, x_bars, ranges)
            elif mode == 'histogram':
               chart_img, table_html = generate_histogram(readings, usl=usl, lsl=lsl)

            elif mode == 'piechart':
                chart_img ,table_html= generate_pie_chart(status,usl=usl, lsl=lsl)

            # Return both chart and table if applicable
            return JsonResponse({
                'chart_img': chart_img,
                'table': table_html if table_html else '',
            })

        return render(request, 'app/spcCharts.html')
  
    

    elif request.method == 'GET':
        part_model = request.GET.get('part_model', '')
        print(f'Received part model: {part_model}')

        try:
            parameter_setting = Parameter_Settings.objects.get(part_model=part_model)
            
            # Get all related paraTableData
            parameter_names = list(
                paraTableData.objects.filter(parameter_settings=parameter_setting)
                .values_list('parameter_name', flat=True)
                .order_by('id')
            )
            print("parameter_names", parameter_names)

            error_message = None  # No error

        except Parameter_Settings.DoesNotExist:
            # If not found, set empty parameter_names and an error message
            print(f"No parameter settings found for part model: {part_model}")
            parameter_names = []
            error_message = f"No parameter settings found for part model: {part_model}"

        # Common context logic (this runs regardless of try/except above)
        shift_values = Data_Shift.objects.order_by('id').values_list('shift', 'shift_time').distinct()
        shift_name_queryset = Data_Shift.objects.order_by('id').values_list('shift', flat=True).distinct()
        shift_name = list(shift_name_queryset)
        print("shift_name", shift_name)

        shift_values_list = list(shift_values)
        shift_values_json = json.dumps(shift_values_list)
        print("shift_values_json", shift_values_json)

        customer = Customer.objects.first()
        primary_email = customer.primary_email if customer else ''
        secondary_email = customer.secondary_email if customer else ''
        print("Primary Email:", primary_email)
        print("Secondary Email:", secondary_email)

        # Context to pass into the template
        context = {
            'shift_values': shift_values_json,
            'shift_name': shift_name,
            'parameter_names': parameter_names,
            'primary_email': primary_email,
            'secondary_email': secondary_email,
            'error_message': error_message,
        }

        return render(request, 'app/spcCharts.html', context)
