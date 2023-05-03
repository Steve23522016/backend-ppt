from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import random

import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, T5Tokenizer, T5ForConditionalGeneration

hx_tokenizer_non_summarized = AutoTokenizer.from_pretrained("eiproject/IndoBERT-NotSummarized-HoaxDetection")
hx_model_non_summarized = AutoModelForSequenceClassification.from_pretrained("eiproject/IndoBERT-NotSummarized-HoaxDetection")

hx_tokenizer_summarized = AutoTokenizer.from_pretrained("eiproject/IndoBERT-Summarized-HoaxDetection")
hx_model_summarized = AutoModelForSequenceClassification.from_pretrained("eiproject/IndoBERT-Summarized-HoaxDetection")

summarization_tokenizer = T5Tokenizer.from_pretrained("panggi/t5-base-indonesian-summarization-cased")
summarization_model = T5ForConditionalGeneration.from_pretrained("panggi/t5-base-indonesian-summarization-cased")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
hx_model_summarized.to(device)

def predict_hoax(articles, tokenizer, model):
    tokenized = tokenizer(articles, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
    with torch.no_grad():
        logits = model(**tokenized).logits
    predicted_class_id = logits.argmax().item()
    return predicted_class_id


def get_token_length(input_ids):     
    return len(input_ids["input_ids"][0])


def get_summarization_length(token_length):
    long_min_length = 480
    mid_min_length = 300

    long_sum_max_length = long_min_length
    long_sum_min_length = 380

    mid_sum_max_length = mid_min_length
    mid_sum_min_length = 256

    short_length_ratio = 0.75

    if token_length > long_min_length:
        return long_sum_min_length, long_sum_max_length
    elif (token_length > mid_min_length) & (token_length <= long_min_length):
        return mid_sum_min_length, mid_sum_max_length
    elif token_length <= mid_min_length:
        return int(short_length_ratio * token_length), token_length
    else:
        return None, None


def generate_summaries(articles, tokenizer, model):
    input_ids = tokenizer(articles, return_tensors='pt', padding=True).to(device)
    token_length = get_token_length(input_ids)
    sum_min_length, sum_max_length = get_summarization_length(token_length)
    
    with torch.no_grad():
        summary_ids = model.generate(
            input_ids["input_ids"],
            min_length=sum_min_length,
            max_length=sum_max_length, 
            num_beams=2,
            repetition_penalty=2.5, 
            length_penalty=1.0, 
            early_stopping=True,
            no_repeat_ngram_size=2,
            use_cache=True)
        
    summary_text = tokenizer.batch_decode(summary_ids, skip_special_tokens=True)
    return summary_text


app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = '103.31.38.80'
app.config['MYSQL_USER'] = 'if5200'
app.config['MYSQL_PASSWORD'] = '@if5200PPT'
app.config['MYSQL_DB'] = 'if5200db'
 
mysql = MySQL(app)

@app.route("/calculate_label", methods=['POST'])
def calculate_label():
    if (request.method == 'POST'):
        try:
            inputText = request.form.get('inputText')
            inputType = request.form.get('inputType')

            if (inputType == 'summarization'):
                outputSummarization = generate_summaries(inputText, summarization_tokenizer, summarization_model)
            else:
                outputSummarization = None

            if outputSummarization:
                prediction_id = predict_hoax(outputSummarization, hx_tokenizer_summarized, hx_model_summarized)
            else:
                prediction_id = predict_hoax(inputText, hx_tokenizer_non_summarized, hx_model_non_summarized)

            if (prediction_id == 1):
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