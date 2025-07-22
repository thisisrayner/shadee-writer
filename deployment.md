      
# Deployment Guide: D.O.R.A. API & Writer's Assistant

This guide provides a detailed, step-by-step process for deploying the **D.O.R.A. Research API** to a DigitalOcean Droplet and connecting it to the **Shadee.Care Writer's Assistant**, which is hosted on Streamlit Community Cloud.

## Architecture Overview

This project uses a microservice architecture:

1.  **Backend (D.O.R.A. API):** A FastAPI application that handles all heavy research tasks (searching, scraping, AI analysis). It will be deployed on a DigitalOcean Droplet using Gunicorn as the application server and Nginx as a reverse proxy.
2.  **Frontend (Writer's Assistant):** A Streamlit application that provides the user interface. It will remain deployed on Streamlit Community Cloud for ease of use and zero maintenance. It acts as a client, making HTTP requests to the D.O.R.A. API.

---

## Phase 1: Prepare the D.O.R.A. Project for API Deployment

Before deploying, ensure the D.O.R.A. project is structured as an API.

### 1.1. Finalize Project Structure

Confirm your D.O.R.A. project follows this structure:

    

IGNORE_WHEN_COPYING_START
Use code with caution. Markdown
IGNORE_WHEN_COPYING_END

/project-zhenghe/
├── api/
│ ├── main.py # FastAPI server
│ ├── models.py # Pydantic data models
│ └── security.py # API key authentication
├── core_engine/ # The research logic (formerly 'modules/')
│ └── ... (all your .py files)
├── requirements.txt # Must include FastAPI and Uvicorn
└── ... (other project files)
Generated code

      
### 1.2. Configure Secrets

The D.O.R.A. API needs its own secret key to protect its endpoint. Create a `.streamlit/secrets.toml` file within the D.O.R.A. project folder *on the server*.

**Example `secrets.toml` for D.O.R.A. API:**
```toml
# Google, LLM, and other secrets for D.O.R.A.
# ...

[dora_api]
# Generate a strong, random string for this key
API_KEY = "your_super_secret_dora_api_key"

    

IGNORE_WHEN_COPYING_START
Use code with caution.
IGNORE_WHEN_COPYING_END
Phase 2: Deploy the D.O.R.A. API to the DigitalOcean Droplet

This phase covers setting up the server environment and running the API as a persistent service.
2.1. Initial Server Setup (One-Time)

Log in to your Droplet via SSH:
Generated bash

      
ssh root@your_droplet_ip

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END

Update your server and install necessary tools:
Generated bash

      
sudo apt update && sudo apt upgrade -y
sudo apt install python3-venv python3-pip git nginx -y

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END
2.2. Clone and Prepare the Application

Navigate to your home directory (or a preferred location like /var/www) and clone your D.O.R.A. project.
Generated bash

      
cd ~
git clone <url_to_your_dora_repo>
cd project-zhenghe

# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all required Python packages
pip install -r requirements.txt
pip install gunicorn  # Install the production server

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END
2.3. Configure and Test Gunicorn

Gunicorn will run your FastAPI application. From inside the project-zhenghe directory (with the venv active), test it:
Generated bash

      
# -w 4: Use 4 worker processes (a good starting point)
# -k uvicorn.workers.UvicornWorker: Use Uvicorn's high-performance worker class
# api.main:app: Look in the `api/main.py` file for the FastAPI object named `app`
# -b 0.0.0.0:8000: Bind to port 8000 on all available network interfaces
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app -b 0.0.0.0:8000

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END

The API should start. You can stop it with Ctrl+C. This confirms the application runs correctly.
2.4. Create a systemd Service File

To ensure the API runs continuously and restarts automatically, create a service file.
Generated bash

      
sudo nano /etc/systemd/system/dora-api.service

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END

Paste the following configuration. Adjust User and WorkingDirectory/ExecStart paths if you are not using the root user or cloned into a different directory.
Generated ini

      
[Unit]
Description=D.O.R.A. Research API Service
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/project-zhenghe
# The full path to gunicorn and the command from the test step
ExecStart=/root/project-zhenghe/venv/bin/gunicorn -w

    
