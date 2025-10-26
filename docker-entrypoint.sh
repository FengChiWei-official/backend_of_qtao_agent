until mysql -h smai_db -uappuser -pCoS_fa_au_23mi -e "select 1" tstDB; do
  echo "Waiting for MySQL to be ready..."
  sleep 2
done
export PYTHONPATH=/app
# Check if there are any model changes before creating a revision
if ! conda run -n app alembic -c /app/config/alembic.ini check | grep -q "No new upgrade operations found"; then
    conda run -n app alembic -c /app/config/alembic.ini revision --autogenerate -m "Auto migration"
fi
conda run -n app alembic -c /app/config/alembic.ini upgrade head
conda run --no-capture-output -n app python ./main.py