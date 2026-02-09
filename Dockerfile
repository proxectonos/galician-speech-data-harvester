FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data and logs
RUN mkdir -p /app/data/downloads /app/logs

# Make scraper executable
RUN chmod +x /app/scraper

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV PATH="/app:${PATH}"

# Create entrypoint script
RUN printf '#!/bin/bash\n'\
'if [ $# -eq 0 ]; then\n'\
'  /app/scraper help\n'\
'  echo "=========================================="\n'\
'  echo -e "\\033[0;33mPodes saír do modo interactivo co comando \\033[0;32mexit\\033[0m"\n'\
'  exec /bin/bash --rcfile <(echo "PS1='"'"'\\[\\033[0;32m\\]> \\[\\033[0m\\]'"'"'")\n'\
'else\n'\
'  exec /app/scraper "$@"\n'\
'fi\n' > /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
