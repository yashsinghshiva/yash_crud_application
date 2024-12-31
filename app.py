from flask import Flask, request, render_template, redirect, url_for, jsonify
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import boto3
import json
from botocore.exceptions import ClientError

app = Flask(__name__)

# Helper function to retrieve secrets from AWS Secrets Manager
def get_secret():
    secret_name = "yash/crud"  # Update this to match your actual secret name
    region_name = "us-east-2"

    # Create a Secrets Manager client
    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        # Retrieve the secret value
        response = client.get_secret_value(SecretId=secret_name)

        # Parse the secret value based on its format (String or Binary)
        if "SecretString" in response:
            secret = json.loads(response["SecretString"])
        else:
            secret = json.loads(response["SecretBinary"])

        return secret
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        return None

# Get database credentials from Secrets Manager
db_secret = get_secret()

# Database connection settings using secrets from Secrets Manager
if db_secret:
    DB_SETTINGS = {
        'dbname': db_secret.get('dbname'),
        'user': db_secret.get('user'),
        'password': db_secret.get('password'),
        'host': db_secret.get('host'),
        'port': db_secret.get('port')
    }
else:
    print("Failed to retrieve database credentials from Secrets Manager.")

# Helper function to get a database connection
def get_db_connection():
    return psycopg2.connect(**DB_SETTINGS)

# Create necessary table if it doesn't exist
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            post TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );
        ''')
        conn.commit()

@app.route('/')
def home():
    # Render the home page with the form
    return render_template('index.html')

@app.route('/add_post', methods=['POST'])
def add_post():
    # Get the data from the form
    user_name = request.form.get('name')
    user_post = request.form.get('post')

    # Insert the post into the database
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO posts (name, post) VALUES (%s, %s)',
                (user_name, user_post)
            )
            conn.commit()

    return redirect(url_for('home'))  # Redirect to the home route

@app.route('/view_posts', methods=['GET'])
def view_posts():
    # Fetch all posts from the database
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM posts ORDER BY created_at DESC')
            posts = cur.fetchall()

    # Render a new page that lists all posts
    return render_template('view_posts.html', posts=posts)

@app.route('/update_post/<int:post_id>', methods=['POST'])
def update_post(post_id):
    # Get the updated post content
    updated_post = request.form.get('updated_post')

    # Update the post in the database
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE posts SET post = %s, updated_at = %s WHERE id = %s',
                (updated_post, datetime.now(), post_id)
            )
            conn.commit()

    return redirect(url_for('view_posts'))  # Redirect to the view_posts route

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    # Remove the post from the database
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM posts WHERE id = %s', (post_id,))
            conn.commit()

    return redirect(url_for('view_posts'))  # Redirect to the view_posts route

@app.route('/health', methods=['GET'])
def health_check():
    # Return the health status of the application
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')  # Simple query to check connection
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
