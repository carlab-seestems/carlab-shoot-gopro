# Use the latest Rust image as the base
FROM rust:latest

# Set the working directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip

# Copy the local requirements.txt file into the container
COPY requirements.txt ./

# Install the Python packages from requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

