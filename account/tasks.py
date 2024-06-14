from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings



@shared_task
def confirmation_code_create(title, body, email):
    send_mail(title,
              body,
              settings.EMAIL_HOST_USER,
              [email],
              fail_silently=False)