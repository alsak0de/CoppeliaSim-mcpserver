# Dockerfile for CoppeliaSim MCP Server
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (if any needed, e.g., for ZeroMQ)
RUN apt-get update && apt-get install -y \
    gcc \
    libzmq3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the default server port (can be overridden at runtime)
EXPOSE 8000

# Use an environment variable for the port (default: 8000)
ENV MCP_PORT=8000

# Set entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"] 