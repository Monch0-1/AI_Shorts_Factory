# Use Python 3.12 slim image for a smaller footprint
FROM python:3.12-slim

# Install system dependencies
# - imagemagick: Required for MoviePy TextClip
# - ffmpeg: Required for video processing
# - fonts-liberation: Provides standard fonts for text generation
RUN apt-get update && apt-get install -y \
    imagemagick \
    ffmpeg \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow text processing (often disabled by default in Linux)
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml || true

# Set the working directory inside the container
WORKDIR /app

# Copy requirements from the Docker folder (relative to build context root)
COPY Docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from project root
COPY . .

# Set PYTHONPATH so Python can find your modules
ENV PYTHONPATH=/app

# Default command: Run the main script
CMD ["python", "CreateShorts/Create_Short_Service/Create_New_Short.py"]