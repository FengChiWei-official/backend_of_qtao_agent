until mysql -h smai_db -uappuser -pappuserpwd -e "select 1" tstDB; do
  echo "Waiting for MySQL to be ready..."
  sleep 2
done
export PYTHONPATH=/app
conda run -n app alembic -c /app/config/alembic.ini upgrade head
conda run --no-capture-output -n app python ./src/main.py