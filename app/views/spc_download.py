import os
from django.http import JsonResponse
from weasyprint import HTML
from datetime import datetime
from pathlib import Path
from io import BytesIO
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import smtplib
from app.models import MailSettings  # Update with your actual app name
from django.views.decorators.csrf import csrf_exempt

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


@csrf_exempt
def spc_download(request):
    if request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email', '')

        table_html = request.POST.get('table_html', '')
        chart_html = request.POST.get('chart_html', '')

        from_date = request.POST.get('from_date', '')
        to_date = request.POST.get('to_date', '')
        part_model = request.POST.get('part_model', '')
        mode = request.POST.get('mode', '')
        shift = request.POST.get('shift', '')
        parameter_name = request.POST.get('parameter_name', '')
        sample_size = request.POST.get('sample_size', '')

        summary_table_html = f"""
        <table>
            <tr><th>From Date</th><td>{from_date}</td><th>To Date</th><td>{to_date}</td></tr>
            <tr><th>Part Model</th><td>{part_model}</td><th>Mode</th><td>{mode}</td></tr>
            <tr><th>Shift</th><td>{shift}</td><th>Sample Size</th><td>{sample_size}</td></tr>
            <tr><th>Parameter Name</th><td colspan="3">{parameter_name}</td></tr>
        </table>
        """

        full_html = f"""
        <html>
        <head>
            <style>
                @page {{
                    size: A4 landscape;
                    margin: 10mm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 9px;
                    margin: 0;
                    padding: 0;
                }}
                h2 {{
                    text-align: center;
                    margin: 4px 0 8px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 8px;
                    table-layout: fixed;
                    word-wrap: break-word;
                }}
                th, td {{
                    border: 1px solid #ccc;
                    padding: 2px;
                    text-align: center;
                }}
                img {{
                    max-width: 100%;
                    max-height: 300px;
                    height: auto;
                    display: block;
                    margin: 0 auto 10px auto;
                }}
                .section {{
                    page-break-inside: avoid;
                    max-height: 350px;
                    overflow: hidden;
                }}
            </style>
        </head>
        <body>
            <h2>SPC Report</h2>
            {summary_table_html}
            <div class="section">{chart_html}</div>
            <div class="section">{table_html}</div>
        </body>
        </html>
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{mode}_{timestamp}.pdf"

        # If email export
        if export_type == 'send_mail' and recipient_email:
            try:
                print(f"📥 export_type: {export_type}, recipient_email: {recipient_email}")
                print("🧾 Generating PDF for email...")
                pdf_buffer = BytesIO()
                HTML(string=full_html).write_pdf(pdf_buffer)
                pdf_data = pdf_buffer.getvalue()
                print("📦 PDF generated, sending via email...")
                send_mail_with_pdf(pdf_data, recipient_email, filename)
                return JsonResponse({'success': True, 'message': f'📧 PDF sent to {recipient_email}'})
            except Exception as e:
                print(f"❌ Exception while sending email: {e}")
                return JsonResponse({'success': False, 'message': f'❌ Failed to send email: {str(e)}'})
        else:
            # Save to USB or Downloads
            try:
                save_dir, source = get_save_directory()
                save_path = os.path.join(save_dir, filename)
                HTML(string=full_html).write_pdf(save_path)
                return JsonResponse({'success': True, 'message': f'📁 PDF saved to {source}: {save_path}'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'❌ Failed to save PDF: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})