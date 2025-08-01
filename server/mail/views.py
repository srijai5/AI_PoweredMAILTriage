from django.shortcuts import render
from .utils import fetch_unread_emails

def inbox_view(request):
    urgent_emails = []
    normal_emails = []

    if request.method == "POST":
        urgent_emails, normal_emails = fetch_unread_emails()

    return render(request, 'mail/inbox.html', {
        'urgent_emails': urgent_emails,
        'normal_emails': normal_emails
    })
