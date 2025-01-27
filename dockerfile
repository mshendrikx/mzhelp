# Use Ubuntu 22.04 base image
FROM ubuntu:22.04

# Update package lists
RUN apt-get update

# Install software
RUN apt-get install -y python3 python3-pip wget

RUN install -d -m 0755 /etc/apt/keyrings

RUN wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O- | tee /etc/apt/keyrings/packages.mozilla.org.asc > /dev/null

RUN echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" | tee -a /etc/apt/sources.list.d/mozilla.list > /dev/null

RUN echo 'Package: * Pin: origin packages.mozilla.org Pin-Priority: 1000 ' | tee /etc/apt/preferences.d/mozilla

RUN apt-get update && apt-get install firefox-nightly -y

WORKDIR /app

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux64.tar.gz
RUN tar -xvzf geckodriver-v0.35.0-linux64.tar.gz
RUN chmod +x geckodriver
RUN mv geckodriver /usr/local/bin/

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

# Expose port 7005 for web traffic
EXPOSE 7005

# Start pyhton app in the foreground
CMD ["python3", "/app/app.py"]