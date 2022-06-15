#!/bin/bash

cd /home/ec2-user/fbadsfinal
source venv/bin/activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate --noinput
python manage.py collectstatic


sudo systemctl restart gunicorn
sudo systemctl daemon-reload
sudo systemctl restart gunicorn.socket gunicorn.service
sudo nginx -t && sudo systemctl restart nginx