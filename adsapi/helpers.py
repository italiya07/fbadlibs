import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config
from email.message import EmailMessage

port = int(config('SMTP_port'))
smtp_server = config('smtp')
username=config('smtp_username')
smtp_from=config('smtp_from')

def send_forgot_password_email(request,token,email):
    subject='Your forgot Password link from EYE OF ECOM'
    mail_content=f'Hi,click on the link to change your password {config("front_end")}/auth/update_password/?token={token}'
    
    msg = EmailMessage()
    msg["Subject"]=subject
    msg["From"]=smtp_from
    msg["To"]=email
    msg.set_content(mail_content)

    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(username, config('forgot_password'))
                server.send_message(msg)
        elif port == 587:
            with smtplib.SMTP(smtp_server, port) as server:
                server.starttls()
                server.login(username, config('forgot_password'))
                server.send_message(msg)
        else:
            print ("use 465 / 587 as port value")
        print ("successfully sent")

    except Exception as e:
        print (str(e))
    
    return True

def send_activation_email(request,token,email):
    subject='Your account activation link from EYE OF ECOM'
    mail_content=f'Hi,click on the link to verify your account {config("front_end")}/auth/verify_email/?token={token}'
  
    msg = EmailMessage()
    msg["Subject"]=subject
    msg["From"]=smtp_from
    msg["To"]=email
    msg.set_content(mail_content)

    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(username, config('email_verification_password'))
                server.send_message(msg)
        elif port == 587:
            with smtplib.SMTP(smtp_server, port) as server:
                server.starttls()
                server.login(username, config('email_verification_password'))
                server.send_message(msg)
        else:
            print ("use 465 / 587 as port value")
        print ("successfully sent")

    except Exception as e:
        print (str(e))
    
    return True

def send_support_email(email,name,message):

    MSG = f"Sender Name :- {name}\n\nMessage     :- {message} \n\nreply back to {email}"
    REPLY_TO_ADDRESS = email

    msg = EmailMessage()
    msg["Subject"]='Contact Support'
    msg.add_header('reply-to', REPLY_TO_ADDRESS)
    msg.set_content(MSG)

    server=smtplib.SMTP(config("SMTP_server"), int(config("SMTP_port")))
    server.starttls()
    server.login(config("from_email_fp"),config("password_fp"))
    
    text = msg.as_string()
    server.sendmail(config("from_email_fp"), config("from_email_fp"), text)
    server.quit()
    return True