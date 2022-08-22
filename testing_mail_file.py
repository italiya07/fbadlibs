
import smtplib, ssl
from email.message import EmailMessage
port = 587
smtp_server = "smtp.zeptomail.com"
username="emailapikey"
password = "wSsVR61/8xL2DqcrlDX5Je49nlkDUQ6gFk0sjQT1un+qFvmU/Mc5lhacAgX2FPAcFTRhETATrO8oyU9S0WZdjtgvm1gADSiF9mqRe1U4J3x17qnvhDzPXm5elhuKLYgKxAtonGdoF8An+g=="
message = "Test email sent successfully."
msg = EmailMessage()
msg['Subject'] = "Test Email"
msg['From'] = "noreply@app.eyeofecom.com"
msg['To'] = "support@eyeofecom.com"
msg.set_content(message)
try:
    if port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(username, password)
            server.send_message(msg)
    elif port == 587:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login("emailapikey", password)
            server.send_message(msg)
    else:
        print ("use 465 / 587 as port value")
        exit()
    print ("successfully sent")
except Exception as e:
    print (e)
