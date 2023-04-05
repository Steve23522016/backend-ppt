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

            if (inputType == 'summarization'):
                outputSummarization = 'This is sample of summarization text'
            else:
                outputSummarization = None

            randomNumber = random.randint(1, 10)
            if (randomNumber <= 5):
                outputLabel = 'hoax'
            else:
                outputLabel = 'not hoax'
            
            cursor = mysql.connection.cursor()
            cursor.execute(''' INSERT INTO hoax_detection_results(input_text, process_category, summarization_result, output_label) VALUES (%s, %s, %s, %s) ''', (inputText, inputType, outputSummarization, outputLabel))
            mysql.connection.commit()
            cursor.close()

            return (jsonify({
                "message": "Success insert hoax detection result into DB",
                "inputText": inputText,
                "inputType": inputType,
                "summarizationResult": outputSummarization,
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
    
@app.route("/history_label", methods=['POST'])
def history_label():
    if (request.method == 'POST'):
        try:
            inputKeyword = request.form.get('inputKeyword')
            inputDetectionType = request.form.get('inputDetectionType')
            inputResultType = request.form.get('inputResultType')
            
            # CONSTRUCT SELECT QUERY WITH/WITHOUT FILTER
            queryString = 'SELECT * FROM hoax_detection_results '
            queryWhereCondition = []
            valueWhereCondition = ()
            if inputKeyword:
                queryWhereCondition.append('input_text LIKE %s')
                valueWhereCondition += (f"%{inputKeyword}%",)
            if inputDetectionType:
                queryWhereCondition.append('process_category = %s')
                valueWhereCondition += (inputDetectionType,)
            if inputResultType:
                queryWhereCondition.append('output_label = %s')
                valueWhereCondition += (inputResultType,)
            queryWhereCondition = ' AND '.join(queryWhereCondition)
            if queryWhereCondition:
                queryWhereCondition = ' WHERE ' + queryWhereCondition
            queryString = queryString + queryWhereCondition + ' ORDER BY date DESC'

            # EXECUTE QUERY SELECT ABOVE
            cursor = mysql.connection.cursor()
            cursor.execute(queryString, valueWhereCondition)
            row_headers=[x[0] for x in cursor.description]
            data = cursor.fetchall()
            json_data = []
            for result in data:
                json_data.append(dict(zip(row_headers,result)))
            mysql.connection.commit()
            cursor.close()

            return (jsonify({
                "message": "Success fetching hoax detection history from DB",
                "data": json_data,
                "status": 200
            }), 200)
        except Exception as e:
            return (jsonify({
                "message": "Failed to fetch hoax detection history from DB : " + str(e),
                "status": 409
            }), 409)
    else:
        return (jsonify({
            "message": "resource not found",
            "status": 404
        }), 404)

@app.route("/delete_history/<string:id>", methods=['DELETE'])
def delete_history(id):
    if (request.method == 'DELETE'):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute(""" DELETE FROM hoax_detection_results WHERE id = %s """, (id,))
            mysql.connection.commit()
            cursor.close()

            return (jsonify({
                "message": "Success delete detection history from DB",
                "status": 200
            }), 200)
        except Exception as e:
            return (jsonify({
                "message": "Failed to delete detection history from DB : " + str(e),
                "status": 409
            }), 409)
    else:
        return (jsonify({
            "message": "resource not found",
            "status": 404
        }), 404)

if __name__ == "__main__":
    app.run()