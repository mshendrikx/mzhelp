# Use Debian bullseye-slim base image
FROM debian:stable-slim

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y \
    wget \
    python3 \
    python3-pip \
    curl \
    nano \
    cron \
    unzip \
    chromium \
    chromium-driver \
    libxml2-dev \ 
    libxslt-dev \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    libxtst6 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Verify Chromium installation
RUN chromium --version

# Verify ChromeDriver installation
RUN chromedriver --version

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt --break-system-packages

COPY . .

# Expose port 7010 for web traffic
EXPOSE 7010

# Start pyhton app in the foreground
CMD ["python3", "/app/app.py"]