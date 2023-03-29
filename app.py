from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'persija@2020OK'
app.config['MYSQL_DB'] = 'project-ppt'
 
mysql = MySQL(app)

@app.route("/calculate_label", methods=['POST'])
def calculate_label():
    if (request.method == 'POST'):
        try:
            inputText = request.form.get('inputText')
            inputType = request.form.get('inputType')
            randomNumber = random.randint(1, 10)
            if (randomNumber <= 5):
                outputLabel = 'hoax'
            else:
                outputLabel = 'not hoax'
            
            cursor = mysql.connection.cursor()
            cursor.execute(''' INSERT INTO hoax_detection_results(input_text, process_category, output_label) VALUES (%s, %s, %s) ''', (inputText, inputType, outputLabel))
            mysql.connection.commit()
            cursor.close()

            return (jsonify({
                "message": "Success insert hoax detection result into DB",
                "inputText": inputText,
                "inputType": inputType,
                "labelResult": outputLabel,
                "status": 201
            }), 201)
        except Exception as e:
            return (jsonify({
                "message": "Failed insert hoax detection result into DB : " + str(e),
                "status": 409
            }), 409)
    else:
        return (jsonify({
            "message": "resource not found",
            "status": 404
        }), 404)

if __name__ == "__main__":
    app.run()