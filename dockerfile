# Use Debian bullseye-slim base image
FROM debian:stable-slim

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y \
    wget \
    curl \
#    gnupg \
    python3 \
    python3-pip \
#   curl \
    nano \
    cron \
 #   unzip \
 #   apt-transport-https \
 #   ca-certificates \
    chromium \
    chromium-driver \
    libxml2-dev \ 
    libxslt-dev \
#    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

#RUN install -d -m 0755 /etc/apt/keyrings

#RUN wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O- | tee /etc/apt/keyrings/packages.mozilla.org.asc > /dev/null
#RUN echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" | tee -a /etc/apt/sources.list.d/mozilla.list > /dev/null

#RUN apt-get update && apt-get install -y firefox-nightly \
#    && rm -rf /var/lib/apt/lists/*

# Create the new user and group
#ARG APP_USER=mzhelp  
#ARG APP_GROUP=mzhelp
#RUN groupadd -g 1001 $APP_GROUP && \  
#    useradd -u 1001 -g $APP_GROUP -ms /bin/bash $APP_USER && \
#    chown -R $APP_USER:$APP_GROUP /home/$APP_USER

WORKDIR /app

#RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux-aarch64.tar.gz \
#    && tar -xzf geckodriver-v0.35.0-linux-aarch64.tar.gz 

COPY requirements.txt .

RUN pip3 install -r requirements.txt --break-system-packages

RUN cp /usr/bin/chromedriver /usr/local/lib/python3.11/dist-packages/seleniumbase/drivers 
#    && mv geckodriver /usr/local/lib/python3.11/dist-packages/seleniumbase/drivers \
#    && rm geckodriver-v0.35.0-linux-aarch64.tar.gz

COPY . .

#RUN chown -R $APP_USER:$APP_GROUP /app && \
#    chmod -R 777 /var/run

ENV DISPLAY=:0

# Switch to the non-root user
#USER $APP_USER

# Expose port 7020 for web traffic
#ENTRYPOINT ["cron", "-f"]

EXPOSE 7020

# Start pyhton app in the foreground
CMD ["python3", "/app/app.py"]