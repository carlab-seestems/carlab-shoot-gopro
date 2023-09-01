# Use the latest Rust image as the base
FROM rust:latest

# Set the working directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-venv \
    python3-pip

# Copy the local requirements.txt file into the container
COPY requirements.txt ./

# Install the Python packages from requirements.txt
# Create a virtual environment
RUN python3 -m venv /app/venv

# Activate virtual environment for subsequent commands
ENV PATH="/app/venv/bin:$PATH"

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

