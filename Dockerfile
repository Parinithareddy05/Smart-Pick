FROM python:3.10-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget curl git \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libexpat1 libxcb1 libxkbcommon0 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium firefox
RUN playwright install-deps chromium firefox

# Copy project files
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/
COPY data/ ./data/

# Create results directory
RUN mkdir -p results

# Run the pipeline once to generate initial ranked_output.csv
RUN cd /app && python src/main.py || echo "Pipeline will run on first request"

# Expose port (HuggingFace uses port 7860)
EXPOSE 7860

# Start Flask on port 7860
ENV FLASK_PORT=7860
CMD ["python", "src/app.py", "--port", "7860"]
