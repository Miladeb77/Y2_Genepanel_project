# Declare the base image with the correct Python version
FROM python:3.9

# Create the working directory inside the container
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

# If Conda dependencies are specified, handle environment setup
RUN if [ -f "environment.yml" ]; then \
    pip install conda && \
    conda env create -f environment.yml || conda env update -f environment.yml; \
    fi

# Copy configuration files to the container's home directory
COPY configuration/build_panelApp_database_config.json /root/.genepanel_config

# Ensure database folders exist and create them
RUN mkdir -p /app/databases /app/archive_databases /app/output

# Expose relevant ports if needed (future use)
EXPOSE 8080

# Set entrypoint for running the main script
ENTRYPOINT ["python", "panelgenemapper.py"]

# Set the default command (replace with your project's common entry point if applicable)
CMD ["--help"]
