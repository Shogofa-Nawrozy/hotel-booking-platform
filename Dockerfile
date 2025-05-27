# Use a base image with Python
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy backend files into the container
COPY . .

RUN pip install pymongo flask faker

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose backend port
EXPOSE 5000

# Run the app (adjust based on your app)
CMD ["python", "app.py"]
