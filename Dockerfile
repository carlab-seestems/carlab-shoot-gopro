# Use an official Python runtime as the base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run your FastAPI app with Uvicorn when the container launches
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
