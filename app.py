from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# In-memory storage for posts
user_posts = []

@app.route('/')
def home():
    # Render the home page with the form
    return render_template('index.html')

@app.route('/add_post', methods=['POST'])
def add_post():
    # Get the data from the form
    user_name = request.form.get('name')
    user_post = request.form.get('post')

    # Add post details with timestamps
    new_post = {
        'id': len(user_posts) + 1,
        'name': user_name,
        'post': user_post,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': None
    }

    # Add the post to the list
    user_posts.append(new_post)

    return redirect(url_for('home'))  # Redirect to the home route

@app.route('/view_posts', methods=['GET'])
def view_posts():
    # Render a new page that lists all posts
    return render_template('view_posts.html', posts=user_posts)

@app.route('/update_post/<int:post_id>', methods=['POST'])
def update_post(post_id):
    # Get the updated post content
    updated_post = request.form.get('updated_post')

    # Update the post in the user_posts list
    for post in user_posts:
        if post['id'] == post_id:
            post['post'] = updated_post
            post['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break

    return redirect(url_for('view_posts'))  # Redirect to the view_posts route

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    global user_posts
    # Remove the post with the matching ID
    user_posts = [post for post in user_posts if post['id'] != post_id]
    return redirect(url_for('view_posts'))  # Redirect to the view_posts route

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
