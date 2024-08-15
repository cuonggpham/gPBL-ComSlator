set -o errexit

pip install -r backend/requirements.txt

python3 manage.py collectstatic --no-input
python3 manage.py migrate