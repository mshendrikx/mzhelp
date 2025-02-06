# Use Debian bullseye-slim base image
FROM debian:bullseye-slim

# Update package lists
RUN apt-get update && apt-get install -y python3 python3-pip wget chromium cron libxml2-dev libxslt-dev nano

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

# Expose port 7010 for web traffic
EXPOSE 7010

# Start pyhton app in the foreground
CMD ["python3", "/app/app.py"]