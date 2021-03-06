import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config

def send_forgot_password_email(request,token,email):
    subject='Your forgot Password link from servicepack'
    domain=request.META['HTTP_HOST']
    mail_content=f'Hi,click on the link to change your password {domain}/api/change_password/{token}'
    msg = MIMEMultipart()
    msg["Subject"]=subject
    msg["From"]=config('From_email_fp')
    msg["To"]=email
    msg.attach(MIMEText(mail_content, 'plain'))
    # server=smtplib.SMTP('smtp.gmail.com', 587)
    server=smtplib.SMTP("smtp.zoho.in", 587)
    server.starttls()
    server.login(config("From_email_fp"),config("password_fp"))
    text = msg.as_string()
    server.sendmail(config('From_email_fp'), email, text)
    server.quit()
    return True