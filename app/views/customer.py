import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app.models import Customer, MailSettings, MasterInterval

@csrf_exempt
def customer(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            form_type = body.get("formType")
            form_data = body.get("formData")

            print("form_data",form_data)

            if form_type == 'customer':
                # Always fetch the single existing customer (if any)
                customer = Customer.objects.first()

                if customer:
                    # Update the existing customer
                    customer.customer_name = form_data.get("customer_name")
                    customer.primary_contact_person = form_data.get("primary_contact_person")
                    customer.secondary_contact_person = form_data.get("secondary_contact_person")
                    customer.primary_email = form_data.get("primary_email")
                    customer.secondary_email = form_data.get("secondary_email")
                    customer.primary_phone_no = form_data.get("primary_phone_no")
                    customer.secondary_phone_no = form_data.get("secondary_phone_no")
                    customer.primary_dept = form_data.get("primary_dept")
                    customer.secondary_dept = form_data.get("secondary_dept")
                    customer.address = form_data.get("address")
                    customer.save()
                else:
                    # Create a new customer
                    Customer.objects.create(
                        customer_name=form_data.get("customer_name"),
                        primary_contact_person=form_data.get("primary_contact_person"),
                        secondary_contact_person=form_data.get("secondary_contact_person"),
                        primary_email=form_data.get("primary_email"),
                        secondary_email=form_data.get("secondary_email"),
                        primary_phone_no=form_data.get("primary_phone_no"),
                        secondary_phone_no=form_data.get("secondary_phone_no"),
                        primary_dept=form_data.get("primary_dept"),
                        secondary_dept=form_data.get("secondary_dept"),
                        address=form_data.get("address")
                    )


            elif form_type == 'mail':
                # Only allow one MailSettings record
                mail = MailSettings.objects.first()
                if mail:
                    mail.sender_email = form_data.get("sender_email")
                    mail.sender_password = form_data.get("sender_password")
                    mail.smtp_server = form_data.get("smtp_server")
                    mail.smtp_port = form_data.get("smtp_port")
                    mail.save()
                else:
                    MailSettings.objects.create(
                        sender_email=form_data.get("sender_email"),
                        sender_password=form_data.get("sender_password"),
                        smtp_server=form_data.get("smtp_server"),
                        smtp_port=form_data.get("smtp_port")
                    )
           


            else:
                return JsonResponse({"error": "Invalid formType"}, status=400)

            return JsonResponse({"message": "Data saved successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'GET':
        try:
            customer_data = Customer.objects.last()
            mail_data = MailSettings.objects.first()  # Only one expected



            return render(request, "app/customer.html", {
                "customer": customer_data,
                "mail": mail_data
            })
        
        

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
