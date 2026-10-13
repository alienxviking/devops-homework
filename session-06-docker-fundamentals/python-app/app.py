import platform
import socket

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return f"""
    <html>
      <head><title>Python App</title></head>
      <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 120px; background: #f3f7fb;">
        <h1 style="color: #306998;">Hello World from Python!</h1>
        <p>Flask app running inside a Docker container</p>
        <p>Container hostname: <b>{socket.gethostname()}</b> | Python {platform.python_version()}</p>
      </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
