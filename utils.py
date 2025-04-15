from flask_mail import Message
from flask import current_app as app

def send_email(to, subject, body):
    try:
        msg = Message(subject, recipients=[to], body=body)
        app.mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def notify_appointment(user, appointment, action):
    service = appointment.service.name
    date_time = appointment.date_time.strftime('%Y-%m-%d %H:%M')
    subject = f"Appointment {action}"
    body = f"Dear {user.username},\n\nYour appointment for {service} on {date_time} has been {action}.\n\nBest regards,\nSalon Team"
    send_email(user.email, subject, body)