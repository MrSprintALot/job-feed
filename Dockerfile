FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Railway provides PORT env var
ENV PORT=5000
EXPOSE 5000

# Install production server
RUN pip install --no-cache-dir gunicorn

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
