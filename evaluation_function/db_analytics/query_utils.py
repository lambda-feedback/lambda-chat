import os
import psycopg2

def connect():
    """ Connect to the PostgreSQL database server """
    try:
        DBusername = os.environ['DB_USERNAME']
        DBpassword = os.environ['DB_PASSWORD']
        DBhost = os.environ['DB_HOST']
        DBport = os.environ['DB_PORT']
        DBname = os.environ['DB_NAME']

        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(
            host=DBhost,
            port=DBport,
            database=DBname,
            user=DBusername,
            password=DBpassword
        )
        return conn
    except Exception as e:
        print(f'Error connecting to the database: {e}')
        return None
