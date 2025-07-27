#!/bin/bash

# 执行 Alembic 迁移
alembic -c /app/config/alembic.ini upgrade head

echo "Database setup complete."