# crabfarm-backend
Backend server for crabfarm web application, that utiliize container  and FastAPI frameworks

Note: Please Install requirement.txt

## Alembic command

''' alembic revision --autogenerate -m "Initial migration"
''' alembic upgrade head

## Run Application
''' uvicorn App:app --reload --host=192.168.100.11 --port=4572

or

''' uvicorn App:app --reload --port=4572

### To see the list of endpoints
''' http://127.0.0.1:4572/docs