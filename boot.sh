#!/bin/bash
echo "activate virtual environment"
source venv/bin/activate
# echo "list files in workdir"
# pwd
# ls . -al
# echo "database upgrade"
# flask db upgrade
echo "run as user"
who
echo "list files in workdir"
pwd
ls . -al
exec gunicorn -b :8080 --access-logfile - --error-logfile - app:app