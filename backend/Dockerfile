# Start with the Python 3.11.4 image based on Debian Bullseye (slim variant)
FROM python:3.11.4-slim-bullseye as install-browser

# Install system dependencies including browsers, drivers, and document processing tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       chromium \
       chromium-driver \
       firefox-esr \
       git \
       wget \
    && chromium --version && chromedriver --version \
    && wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz \
    && tar -xvzf geckodriver* \
    && chmod +x geckodriver \
    && mv geckodriver /usr/local/bin/ \
    && rm -rf /var/lib/apt/lists/*

# Define the reach-install stage that builds on the install-browser stage
FROM install-browser as magi-install

# Set an environment variable to ignore root user actions with pip
ENV PIP_ROOT_USER_ACTION=ignore

# Create and set the working directory
RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# Copy the Python requirements file and install Python dependencies
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Define the final stage, "reach", based on the reach-install stage
FROM magi-install AS reach

# Create a non-root user for running the application
RUN useradd -ms /bin/bash reach \
    && chown -R reach:reach /usr/src/app

# Switch to the non-root user
USER magi

# Copy the application code with appropriate ownership
COPY --chown=reach:reach ./ ./

# Expose the application port
EXPOSE 8000

# Set the default command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
