# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 5432 available to the world outside this container
EXPOSE 5432

# Define environment variable
ENV FLASK_PORT=5432
ENV COINBASE_API_SECRET=your_api_secret_here

# Run the application
CMD ["python", "app.py"]
