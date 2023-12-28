from flask import Flask, render_template, request
import pickle
import numpy as np
import json
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Replace with your Azure Storage Blob credentials
account_name = 'pklfilestore'
account_key = 'qHPCySxXIpA1IyIJz1FrZCTbmBEYT+s+SZbV9BLBZmSMzolSPQvhBGcRNQGYGl4JQWyJNkmyZEf/+AStK3GzSw=='
container_name = 'pklstore'
blob_name = 'pune_home_prices_model.pickle'

# Initialize Azure Storage Blob client
blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net", credential=account_key)
container_client = blob_service_client.get_container_client(container_name)
blob_client = container_client.get_blob_client(blob_name)

# Download the model from Azure Storage Blob
with open('pune_home_prices_model.pickle', 'wb') as model_file:
    model_file.write(blob_client.download_blob().readall())

# Load the model
model = pickle.load(open('pune_home_prices_model.pickle', 'rb'))

# Load data columns
with open('columns.json') as f:
    __data_columns = json.load(f)['data_columns']

__locations = __data_columns[3:]

def get_estimated_price(input_json):
    try:
        loc_index = __data_columns.index(input_json['location'].lower())
    except ValueError:
        loc_index = -1
    x = np.zeros(len(__data_columns))
    x[0] = input_json['sqft']
    x[1] = input_json['bath']
    x[2] = input_json['bhk']
    if loc_index >= 0:
        x[loc_index] = 1
    result = round(model.predict([x])[0], 2)
    return result

@app.route('/')
def index():
    return render_template('index.html', locations=__locations)

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        input_json = {
            "location": request.form['sLocation'],
            "sqft": request.form['Squareft'],
            "bhk": request.form['uiBHK'],
            "bath": request.form['uiBathrooms']
        }
        result = get_estimated_price(input_json)

        if result > 100:
            result = round(result / 100, 2)
            result = str(result) + ' Crore'
        else:
            result = str(result) + ' Lakhs'

    return render_template('predict.html', result=result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
