FROM python:3.11-slim

# Install system dependencies and PortAudio
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Run Flask application
CMD ["python", "app.py"]
