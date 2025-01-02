# Declare the base image with the correct Python version
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the entire project directory into the container's /app directory
COPY . /app

# Create a logging directory
RUN mkdir -p /usr/local/share/logs

# Update apt-get and install apt-managed software
RUN apt update && apt -y install \
    git \
    sqlite3 \
    libsqlite3-dev \
    gzip

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Copy configuration files to the container's home directory
COPY configuration/build_panelApp_database_config.json /root/.genepanel_config

# Ensure database folders exist and create them
RUN mkdir -p /app/databases /app/archive_databases /app/output

# Expose a port (if required for future networking needs)
EXPOSE 8080

# Set the entry point to the main script inside the PanelGeneMapper directory
WORKDIR /app/PanelGeneMapper
ENTRYPOINT ["python", "panelgenemapper.py"]

# Default command to display help if no arguments are provided
CMD ["--help"]
