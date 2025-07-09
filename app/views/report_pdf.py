from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
import os
from datetime import datetime
import textwrap
from pathlib import Path



from django.core.mail import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import smtplib
from app.models import MailSettings  # Adjust to your actual app name


# def get_save_directory():
#     usb_base_path = '/media'
#     downloads_path = str(Path.home() / 'Downloads')

#     # Check if any user folder exists inside /media
#     if os.path.exists(usb_base_path):
#         for user_folder in os.listdir(usb_base_path):
#             user_path = os.path.join(usb_base_path, user_folder)
#             if os.path.isdir(user_path):
#                 # Now check if any device inside user folder
#                 for device_folder in os.listdir(user_path):
#                     device_path = os.path.join(user_path, device_folder)
#                     if os.path.ismount(device_path):
#                         return device_path, 'USB'

#     # No USB found
#     return downloads_path, 'Downloads'


# @csrf_exempt
# def report_pdf(request):
#     if request.method == 'POST':
#         from_date = request.POST.get('from_date', '')
#         to_date = request.POST.get('to_date', '')
#         mode = request.POST.get('mode', '')
#         part_model = request.POST.get('part_model', '')
#         shift = request.POST.get('shift', '')
#         status = request.POST.get('status', '')
#         total_count = request.POST.get('total_count', '')
#         table_html = request.POST.get('table_html')

#         if table_html:
#             soup = BeautifulSoup(table_html, 'html.parser')
#             rows = soup.find_all('tr')

#             if not rows:
#                 return JsonResponse({'success': False, 'message': 'No table rows found.'})

#             first_row = rows[0].find_all(['th', 'td'])
#             col_count = len(first_row)

#             current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
#             file_name = f'report_data_{current_datetime}.pdf'

#             save_dir, save_location = get_save_directory()

#             # Make sure the folder exists
#             os.makedirs(save_dir, exist_ok=True)

#             file_path = os.path.join(save_dir, file_name)

#             c = canvas.Canvas(file_path, pagesize=landscape(letter))
#             width, height = landscape(letter)

#             c.setFont("Helvetica-Bold", 8)

#             # First Row (4 values)
#             c.drawString(30, height - 40, f'From Date: {from_date}')
#             c.drawString(200, height - 40, f'To Date: {to_date}')
#             c.drawString(400, height - 40, f'Mode: {mode}')
#             c.drawString(600, height - 40, f'Part Model: {part_model}')

#             # Second Row (3 values)
#             c.drawString(30, height - 60, f'Shift: {shift}')
#             c.drawString(200, height - 60, f'Status: {status}')
#             c.drawString(400, height - 60, f'Total Count: {total_count}')

#             sr_no_width = 40  
#             remaining_width = width - 60 - sr_no_width
#             other_col_count = col_count - 1  
#             col_width = remaining_width / other_col_count if other_col_count > 0 else remaining_width

#             x_offset = 30
#             y_offset = height - 75

#             # Process headers
#             c.setFont("Helvetica-Bold", 4)
#             header_cells = rows[0].find_all(['th', 'td'])
#             wrapped_headers = [textwrap.wrap(th.text.strip(), width=10) for th in header_cells]
#             max_header_height = max(len(w) for w in wrapped_headers) * 5

#             row_height = max_header_height + 12

#             for i, wrapped_text in enumerate(wrapped_headers):
#                 col_w = sr_no_width if i == 0 else col_width
#                 x_text_offset = x_offset + (col_w / 2)

#                 total_text_height = len(wrapped_text) * 5
#                 y_text_offset = y_offset - ((row_height - total_text_height) / 2) - 5

#                 for line in wrapped_text:
#                     text_width = c.stringWidth(line, "Helvetica-Bold", 4)
#                     c.drawString(x_text_offset - (text_width / 2), y_text_offset, line)
#                     y_text_offset -= 5

#                 c.rect(x_offset, y_offset - row_height, col_w, row_height)
#                 x_offset += col_w

#             y_offset -= row_height

#             # Process table rows
#             row_limit = 30
#             row_count = 0
#             c.setFont("Helvetica", 4)

#             for row in rows[1:]:
#                 cells = row.find_all(['td', 'th'])
#                 x_offset = 30

#                 wrapped_texts = [textwrap.wrap(cell.text.strip(), width=10) for cell in cells]
#                 max_line_count = max(len(w) for w in wrapped_texts)

#                 row_height = max_line_count * 5 + 12

#                 for i, wrapped_text in enumerate(wrapped_texts):
#                     col_w = sr_no_width if i == 0 else col_width
#                     x_text_offset = x_offset + (col_w / 2)

#                     total_text_height = len(wrapped_text) * 5
#                     y_text_offset = y_offset - ((row_height - total_text_height) / 2) - 5

#                     for line in wrapped_text:
#                         text_width = c.stringWidth(line, "Helvetica", 4)
#                         c.drawString(x_text_offset - (text_width / 2), y_text_offset, line)
#                         y_text_offset -= 5

#                     c.rect(x_offset, y_offset - row_height, col_w, row_height)
#                     x_offset += col_w

#                 row_count += 1
#                 y_offset -= row_height

#                 if row_count >= row_limit:
#                     c.showPage()
#                     row_count = 0
#                     y_offset = height - 50
#                     c.setFont("Helvetica", 4)

#             c.save()
#             export_type = request.POST.get('export_type')
#             recipient_email = request.POST.get('recipient_email')

#             print("recipient_email:", recipient_email)
#             print("export_type:", export_type)

#             if export_type == 'send_mail' and recipient_email:
#                 try:
#                     with open(file_path, 'rb') as f:
#                         pdf_data = f.read()
#                     send_mail_with_pdf(pdf_data, recipient_email, file_name)
#                     return JsonResponse({'success': True, 'message': f'✅ PDF sent to {recipient_email} successfully.'})
#                 except Exception as e:
#                     return JsonResponse({'success': False, 'message': f'❌ Failed to send PDF: {str(e)}'})
#             else:
#                 return JsonResponse({'success': True, 'message': f'📁 PDF saved to {save_location}: {file_path}'})

#         else:
#             return JsonResponse({'success': False, 'message': 'No table data provided.'})

#     return JsonResponse({'success': False, 'message': 'Invalid request method.'})


from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.colors import red, yellow, black, HexColor
import textwrap
from app.models import MeasurementData, paraTableData
from datetime import datetime
import os
from pathlib import Path
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import pandas as pd

from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.colors import red, yellow, black, HexColor
import textwrap
from app.models import MeasurementData, paraTableData
from datetime import datetime
import os
from pathlib import Path
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import pandas as pd

bright_green = HexColor('#00ff00')

def get_save_directory():
    usb_base_path = '/media'
    downloads_path = str(Path.home() / 'Downloads')
    if os.path.exists(usb_base_path):
        for user_folder in os.listdir(usb_base_path):
            user_path = os.path.join(usb_base_path, user_folder)
            if os.path.isdir(user_path):
                for device_folder in os.listdir(user_path):
                    device_path = os.path.join(user_path, device_folder)
                    if os.path.ismount(device_path):
                        return device_path, 'USB'
    return downloads_path, 'Downloads'

@csrf_exempt
def report_pdf(request):
    if request.method == 'POST':
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        part_model = request.POST.get('part_model')
        mode = request.POST.get('mode')
        shift = request.POST.get('shift')
        status = request.POST.get('status')
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')

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
            return JsonResponse({'success': False, 'message': 'No data found for the given criteria'})

        data_dict = {
            'Date': [], 'Job Numbers': [], 'Shift': [], 'Operator': [], 'Status': [],
        }

        parameter_data = paraTableData.objects.filter(
            parameter_settings__part_model=part_model
        ).values('parameter_name', 'usl', 'lsl').order_by('id')

        for param in parameter_data:
            key = f"{param['parameter_name']} <br>{param['usl']} <br>{param['lsl']}"
            data_dict[key] = []

        grouped_data = {}
        unique_dates = set()

        for record in filtered_data:
            date = record.date.strftime('%d-%m-%Y %I:%M:%S %p')
            unique_dates.add(date)
            if date not in grouped_data:
                grouped_data[date] = {
                    'Job Numbers': set(), 'Shift': record.shift,
                    'Operator': record.operator, 'Status': record.overall_status,
                    'Parameters': {key: set() for key in data_dict if key not in ['Date', 'Job Numbers', 'Shift', 'Operator', 'Status']}
                }

            if record.comp_sr_no:
                grouped_data[date]['Job Numbers'].add(record.comp_sr_no)

            for param in parameter_data:
                param_name = param['parameter_name']
                usl = param['usl']
                lsl = param['lsl']
                key = f"{param_name} <br>{usl} <br>{lsl}"
                parameter_values = MeasurementData.objects.filter(
                    comp_sr_no=record.comp_sr_no,
                    date=record.date,
                    parameter_name=param_name
                )

                for pv in parameter_values:
                    value_to_display = getattr(pv, {
                        'max': 'max_value',
                        'min': 'min_value',
                        'tir': 'tir_value',
                        'readings': 'output'
                    }.get(mode, 'output'))

                    if mode == 'readings':
                        bg_color = {
                            'ACCEPT': '#00ff00',
                            'REWORK': 'yellow',
                            'REJECT': 'red'
                        }.get(pv.statusCell, 'white')
                        value_to_display = f'<span style="background-color: {bg_color}; padding: 5px;">{value_to_display}</span>'

                    grouped_data[date]['Parameters'][key].add(str(value_to_display))

        for date, group in grouped_data.items():
            data_dict['Date'].append(date)
            data_dict['Job Numbers'].append("<br>".join(sorted(group['Job Numbers'])))
            data_dict['Shift'].append(group['Shift'])
            data_dict['Operator'].append(group['Operator'])

            status_text = group['Status']
            status_color = {
                'ACCEPT': '#00ff00', 'REWORK': 'yellow', 'REJECT': 'red'
            }.get(status_text, 'transparent')
            status_display = f'<span style="background-color: {status_color}; padding: 5px;">{status_text}</span>'
            data_dict['Status'].append(status_display)

            for key, values in group['Parameters'].items():
                data_dict[key].append("<br>".join(sorted(values)))

        df = pd.DataFrame(data_dict)
        df.index += 1
        table_html = df.to_html(index=True, escape=False)

        soup = BeautifulSoup(table_html, 'html.parser')
        rows = soup.find_all('tr')
        if not rows:
            return JsonResponse({'success': False, 'message': 'No table rows found.'})

        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f'report_data_{current_datetime}.pdf'
        save_dir, save_location = get_save_directory()
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, file_name)

        c = canvas.Canvas(file_path, pagesize=landscape(letter))
        width, height = landscape(letter)

        c.setFont("Helvetica-Bold", 8)
        c.drawString(30, height - 40, f'From Date: {from_date}')
        c.drawString(200, height - 40, f'To Date: {to_date}')
        c.drawString(400, height - 40, f'Mode: {mode}')
        c.drawString(600, height - 40, f'Part Model: {part_model}')
        c.drawString(30, height - 60, f'Shift: {shift}')
        c.drawString(200, height - 60, f'Status: {status}')
        c.drawString(400, height - 60, f'Total Count: {len(unique_dates)}')

        sr_no_width = 40
        remaining_width = width - 60 - sr_no_width
        other_col_count = len(rows[0].find_all(['th', 'td'])) - 1
        col_width = remaining_width / other_col_count if other_col_count > 0 else remaining_width

        y_offset = height - 75
        c.setFont("Helvetica-Bold", 4)

        header_cells = rows[0].find_all(['th', 'td'])
        wrapped_headers = [textwrap.wrap(th.get_text(strip=True), width=10) for th in header_cells]
        max_header_height = max(len(w) for w in wrapped_headers) * 5
        row_height = max_header_height + 12
        x_offset = 30

        for i, wrapped in enumerate(wrapped_headers):
            col_w = sr_no_width if i == 0 else col_width
            x_text_offset = x_offset + (col_w / 2)
            y_text_offset = y_offset - ((row_height - len(wrapped) * 5) / 2) - 5
            for line in wrapped:
                text_width = c.stringWidth(line, "Helvetica-Bold", 4)
                c.drawString(x_text_offset - (text_width / 2), y_text_offset, line)
                y_text_offset -= 5
            c.rect(x_offset, y_offset - row_height, col_w, row_height)
            x_offset += col_w

        y_offset -= row_height
        c.setFont("Helvetica", 4)
        row_count = 0
        row_limit = 30

        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            x_offset = 30
            wrapped_texts = [textwrap.wrap(cell.get_text(strip=True), width=10) for cell in cells]
            row_height = max(len(w) for w in wrapped_texts) * 5 + 12

            for i, wrapped in enumerate(wrapped_texts):
                col_w = sr_no_width if i == 0 else col_width
                x_text_offset = x_offset + (col_w / 2)
                y_text_offset = y_offset - ((row_height - len(wrapped) * 5) / 2) - 5

                # ✅ Extract background color
                bg_color = None
                raw_html = str(cells[i])
                soup_cell = BeautifulSoup(raw_html, 'html.parser')
                span = soup_cell.find('span')
                if span and span.has_attr('style'):
                    style = span['style']
                    if 'background-color:' in style:
                        color_code = style.split('background-color:')[1].split(';')[0].strip()
                        if color_code == '#00ff00':
                            bg_color = bright_green
                        elif color_code == 'yellow':
                            bg_color = yellow
                        elif color_code == 'red':
                            bg_color = red

                for line in wrapped:
                    raw_html = str(cells[i])
                    soup_cell = BeautifulSoup(raw_html, 'html.parser')
                    span = soup_cell.find('span')

                    if span and span.has_attr('style'):
                        style = span['style']
                        bg_color = None
                        if 'background-color:' in style:
                            color_code = style.split('background-color:')[1].split(';')[0].strip()
                            if color_code == '#00ff00':
                                bg_color = bright_green
                            elif color_code == 'yellow':
                                bg_color = yellow
                            elif color_code == 'red':
                                bg_color = red

                        if bg_color:
                            text_width = c.stringWidth(line, "Helvetica", 4)
                            rect_x = x_text_offset - text_width / 2 - 3  # Left padding
                            rect_y = y_text_offset - 2  # Top padding
                            rect_width = text_width + 6  # Horizontal padding (3px each side)
                            rect_height = 7  # Height of the pill
                            c.saveState()
                            c.setFillColor(bg_color)
                            c.setStrokeColor(bg_color)  # Match fill color to prevent border contrast
                            c.roundRect(rect_x, rect_y, rect_width, rect_height, radius=2, fill=1, stroke=0)
                            c.restoreState()

                    c.setFillColor(black)  # Ensure text is readable
                    text_width = c.stringWidth(line, "Helvetica", 4)
                    c.drawString(x_text_offset - (text_width / 2), y_text_offset, line)
                    y_text_offset -= 5


                c.setStrokeColor(black)
                c.rect(x_offset, y_offset - row_height, col_w, row_height, fill=0)
                x_offset += col_w

            row_count += 1
            y_offset -= row_height
            if row_count >= row_limit:
                c.showPage()
                row_count = 0
                y_offset = height - 50
                c.setFont("Helvetica", 4)

        c.save()

        if export_type == 'send_mail' and recipient_email:
            try:
                with open(file_path, 'rb') as f:
                    pdf_data = f.read()
                send_mail_with_pdf(pdf_data, recipient_email, file_name)
                return JsonResponse({'success': True, 'message': f'✅ PDF sent to {recipient_email} successfully.'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'❌ Failed to send PDF: {str(e)}'})
        else:
            return JsonResponse({'success': True, 'message': f'📁 PDF saved to {save_location}: {file_path}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})







def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):
    try:
        mail_settings = MailSettings.objects.get(id=1)
    except MailSettings.DoesNotExist:
        print("Mail settings not configured.")
        return

    sender_email = mail_settings.sender_email
    sender_password = mail_settings.sender_password
    smtp_server = mail_settings.smtp_server
    smtp_port = mail_settings.smtp_port
    subject = "Report PDF"
    body = "Please find the attached PDF report."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print("✅ Email sent to:", recipient_email)
    except Exception as e:
        print(f"❌ Error sending email: {e}")


