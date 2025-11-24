FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg portaudio19-dev gcc libc-dev && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot code
COPY . .

# Expose nothing (Discord bots are outbound only)

# Entrypoint
CMD ["python", "bot.py"]