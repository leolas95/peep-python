#!/bin/bash

# Step 1: Install OS dependencies

# Update
sudo apt update && sudo apt upgrade -y

# PPA for Python3.10
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install all deps
sudo apt install python3.10 python3-pip python3-dev nginx postgresql libpq-dev -y

# Step 2: Create database and user, and install extensions
DB_USER="peep_user"
DB_PASSWORD="peep_password"
DB_NAME="peep_python"

echo "Creating DB user"
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"

echo "Creating DB"
sudo -u postgres psql -c "create database ${DB_NAME} with owner ${DB_USER};"
sudo -u postgres psql -c "grant all privileges on database ${DB_NAME} to ${DB_USER};"
sudo -u postgres psql -c "alter user ${DB_USER} createdb;"
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

UBUNTU_USER_HOME_DIR=/home/ubuntu/

# Create virtualenv
python3 -m venv ${UBUNTU_USER_HOME_DIR}/.venv

# Step 3: Configure nginx to run as reverse proxy
NGINX_SITE=fastapi_nginx
cat << 'EOF' > /etc/nginx/sites-enabled/${NGINX_SITE}
server {
        listen 80;
        server_name ~.;
        location / {
                proxy_pass http://127.0.0.1:8080;
        }
}
EOF
sudo service nginx restart

# Step 4: create startup script
cat << EOF > ${UBUNTU_USER_HOME_DIR}/startup.sh
cd ${UBUNTU_USER_HOME_DIR}

echo "Activating environment"
source .venv/bin/activate

PROJECT_NAME="./peep-python"
REPO_URL="https://github.com/leolas95/peep-python.git"
# Clone repo if it's not here
if [ -d "${PROJECT_NAME}" ]; then
    echo "Project directory does not exists. Creating it and cloning repository from remote"
    git clone $REPO_URL
fi

echo "cd to ${PROJECT_NAME}"
cd ${PROJECT_NAME}

echo "Updating repo..."
git pull

echo "Running uvicorn..."
export PEEP_ENV=live
export DB_USER=${DB_USER}
export DB_PASSWORD=${DB_PASSWORD}
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=${DB_NAME}
uvicorn lambdas.main:app --host=0.0.0.0 --port=8080

echo "ok" > /tmp/ok.txt
EOF

# Step 5: Set up systemd service to run the uvicorn server on each instance start/reboot
SYSTEMD_SERVICE_NAME=peep.service
cat << 'EOF' > /etc/systemd/system/${SYSTEMD_SERVICE_NAME}
[Unit]
Description=Run startup script for Peep
After=network.target

[Service]
Type=simple
ExecStart=/bin/su -c "/home/ubuntu/startup.sh" - ubuntu

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable ${SYSTEMD_SERVICE_NAME}
sudo systemctl start ${SYSTEMD_SERVICE_NAME}
