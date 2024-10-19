# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory for the bot
WORKDIR /bot_interactor

# Copy the requirements file to install dependencies
COPY bot_requirements.txt .

# Install any Python dependencies for the bot
RUN pip install --no-cache-dir -r bot_requirements.txt

# Copy the bot manager code to the working directory
COPY . .

# Set environment variables if needed
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run the bot manager script
CMD ["python", "bot_manager.py"]
