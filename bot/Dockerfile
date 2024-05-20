FROM python:3.9

WORKDIR /bot

COPY . .
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y gcc libpq-dev python3-pip
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./bot.py"]