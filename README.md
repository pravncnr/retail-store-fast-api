replace the database creds in the below url and use it in model.py
DATABASE_URL = "postgresql://postgres:root@localhost/pricing_db_2"

install pip dependency from requirements.txt

Ensure you have redis server and run the command
`redis-server`

Run Celery
`celery -A celery_worker worker --loglevel=info`

start the backend api
`uvicorn main:app --reload`
