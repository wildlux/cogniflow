FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for PyQt6 and OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-glx0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libfontconfig1 \
    libfreetype6 \
    libharfbuzz0b \
    libpcre2-16-0 \
    libpng16-16 \
    libjpeg62-turbo \
    libtiff5 \
    libwebp6 \
    libwebpmux3 \
    libwebpdemux2 \
    libavcodec58 \
    libavformat58 \
    libavutil56 \
    libswscale5 \
    libv4l-0 \
    v4l-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port (if needed for web interface)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

# Run the application
CMD ["python", "main_00_launcher.py"]