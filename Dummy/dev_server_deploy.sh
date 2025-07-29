#!/bin/bash
branchname=$1
git pull origin
if [ $? -ne 0 ];
then
  exit
fi
echo "Took pull for latest changes"

git checkout $branchname
if [ $? -ne 0 ];
then
  exit
fi
echo "Checkout to branch "

source ../env/bin/activate
if [ $? -ne 0 ];
then
  exit
fi
echo "Activated vitual environment"

poetry install
if [ $? -ne 0 ];
then
  exit
fi
echo "Run command poetry install"

alembic upgrade head
if [ $? -ne 0 ];
then
  exit
fi
echo "Run alembic migrations"

sudo -i -u ubuntu bash << EOF
sudo supervisorctl stop fedrisk
fuser -k 4001/tcp
sudo supervisorctl start fedrisk
EOF
echo "Restart the server"