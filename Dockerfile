FROM python:3.7-slim

WORKDIR /root/
COPY . .
RUN pip3.7 install -r requirements.txt

ENTRYPOINT [ "python3.7",  "./prom_bot.py"]
