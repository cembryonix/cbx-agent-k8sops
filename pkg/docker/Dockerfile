# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy k8sops_ai module (excluding compiled files)
COPY app/ ./




# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHAINLIT_APP_ROOT=/app/k8sops/chainlit_cfg
ENV PYTHONPATH=/app



# Expose port
EXPOSE 8000

# Run chainlit application

CMD ["chainlit", "run", "./main.py", "-h", "--host", "0.0.0.0", "--port", "8000"]