# Use the official Python image as a base
FROM python:3.12

# Install Firefox and dependencies
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    && tar -xvzf geckodriver-v0.34.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.34.0-linux64.tar.gz

RUN chmod +x /usr/local/bin/geckodriver

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your app runs on
EXPOSE 4000

# Command to run your script
CMD ["python", "wikiETL.py"]
