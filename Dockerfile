# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Add current directory files to the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Give execution permissions to the script
RUN chmod +x start.sh

# Run start.sh when the container launches
CMD ["./start.sh"]
