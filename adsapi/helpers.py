import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config

def send_forgot_password_email(request,token,email):
    subject='Your forgot Password link from EYE OF ECOM'
    domain=request.META['HTTP_HOST']
    mail_content=f'Hi,click on the link to change your password {config("front_end")}/auth/update_password/?token={token}'
    
    msg = MIMEMultipart()
    msg["Subject"]=subject
    msg["From"]=config('from_email_fp')
    msg["To"]=email
    msg.attach(MIMEText(mail_content, 'plain'))

    server=smtplib.SMTP(config("SMTP_server"), int(config("SMTP_port")))
    server.starttls()
    server.login(config("from_email_fp"),config("password_fp"))
    
    text = msg.as_string()
    server.sendmail(config('from_email_fp'), email, text)
    server.quit()
    return True

def send_activation_email(request,token,email):
    subject='Your account activation link from EYE OF ECOM'
    domain=request.META['HTTP_HOST']
    mail_content=f'Hi,click on the link to verify your account {config("front_end")}/auth/verify_email/?token={token}'
    
    msg = MIMEMultipart()
    msg["Subject"]=subject
    msg["From"]=config('from_email_fp')
    msg["To"]=email
    msg.attach(MIMEText(mail_content, 'plain'))
    
    server=smtplib.SMTP(config("SMTP_server"), int(config("SMTP_port")))
    server.starttls()
    server.login(config("from_email_fp"),config("password_fp"))
    
    text = msg.as_string()
    server.sendmail(config('from_email_fp'), email, text)
    server.quit()
    return True

def send_support_email(email,name,message):

    MSG = f"Sender Name :- {name}\n\nMessage     :- {message} \n\nreply back to {email}"
    REPLY_TO_ADDRESS = email

    msg = MIMEMultipart()
    msg["Subject"]='Contact Support'
    msg.add_header('reply-to', REPLY_TO_ADDRESS)
    msg.attach(MIMEText(MSG, 'plain'))

    server=smtplib.SMTP(config("SMTP_server"), int(config("SMTP_port")))
    server.starttls()
    server.login(config("from_email_fp"),config("password_fp"))
    
    text = msg.as_string()
    server.sendmail(config('from_email_fp'), config('from_email_fp'), text)
    server.quit()
    return True