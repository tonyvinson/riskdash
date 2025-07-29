#!/bin/bash

sudo yum update -y
sudo amazon-linux-extras install -y docker
sudo systemctl enable docker.service
sudo systemctl start docker.service
sudo usermod -a -G docker ec2-user
