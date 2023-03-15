from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def hello_world():
    return (jsonify({
        "hello": "message",
        "status":200
    }), 201)

if __name__ == "__main__":
    app.run()