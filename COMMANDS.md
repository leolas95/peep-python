# Usefull commands learned developing the project

## Connect through ssh to the EC2 instance

`ssh -i "fast api key.pem" ubuntu@ec2-18-205-116-118.compute-1.amazonaws.com`

## Copy a local file to the instance with `scp`

`scp -i "fast api key.pem" Music/dep.sh ubuntu@ec2-54-205-69-203.compute-1.amazonaws.com:/home/ubuntu/app/
dep.sh`

## Start the uvicorn server

`uvicorn lambdas.main:app --host=0.0.0.0 --port=8080`

## Create a `systemd` service that runs on startup

```text
[Unit]
Description=Run custom script at startup
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash /path/to/your-script.sh

[Install]
WantedBy=multi-user.target
```

Then start the service:

```shell
sudo systemctl enable myscript.service
sudo systemctl start myscript.service
```