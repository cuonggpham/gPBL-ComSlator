set -o errexit

pip install -r backend/requirements.txt

python3 backend/manage.py collectstatic --no-input
python3 backend/manage.py migrate