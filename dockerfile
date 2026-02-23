# Use Debian bullseye-slim base image
FROM python:slim-bullseye

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y \
    wget \
    curl \
    build-essential \
    python3-dev \
    nano \
    cron \
    chromium \
    chromium-driver \
    libxml2-dev \ 
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip

RUN python3 -m pip config set global.break-system-packages true

WORKDIR /app

COPY requirements.txt .

#RUN pip3 install -r requirements.txt --break-system-packages
RUN pip3 install -r requirements.txt

COPY . .

RUN mkdir -p /logs

#RUN touch /app/logs/mzhelp.log

ENV DISPLAY=:0

EXPOSE 7020

# Start pyhton app in the foreground
CMD ["python3", "/app/app.py"]