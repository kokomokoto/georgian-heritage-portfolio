from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from Georgian Heritage Portfolio!"

@app.route('/health')
def health():
    return {"status": "ok", "message": "App is running"}

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)