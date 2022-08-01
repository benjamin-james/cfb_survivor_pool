release: flask db upgrade
web: gunicorn cfb_survivor_pool.app:create_app\(\) -b 0.0.0.0:$PORT -w 3
