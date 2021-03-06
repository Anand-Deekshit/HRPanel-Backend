# app.py

from flask import Flask, request
import json
from json import JSONEncoder
import pandas as pd
import numpy as np
from pickle import load
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/uploads'

ACCEPTED_ATTRIBUTES = ['enrollee_id', 'city', 'city_development_index', 'gender', 'relevent_experience',
                       'enrolled_university', 'education_level', 'major_discipline', 'experience', 'company_size',
                       'company_type', 'last_new_job', 'training_hours']

CATEGORICAL_ATTRIBUTES = ['city', 'gender', 'relevent_experience', 'enrolled_university',
                          'education_level', 'major_discipline', 'experience', 'company_size', 'company_type',
                          'last_new_job']

TRANSFORM_COL = load(open('transform_col.pkl', 'rb'))
app = Flask(__name__)

model = load(open('model.pkl', 'rb'))


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def transform_df(df):
    df = df.drop(columns=['Unnamed: 0', 'enrollee_id', 'city_development_index'])
    for col in CATEGORICAL_ATTRIBUTES:
        for i in range(df.shape[0]):
            df[col].iloc[i] = TRANSFORM_COL[col][df[col].iloc[i]]
    return df


def check_for_fields(df):
    df = df.drop(columns=['Unnamed: 0'])
    uploaded_attributes = df.columns.tolist()
    print(uploaded_attributes)
    if set(uploaded_attributes) == set(ACCEPTED_ATTRIBUTES):
        return True
    return False


@app.route("/upload", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        employee_data = request.files['csv_file']
        filename = secure_filename(employee_data.filename)
        employee_df = pd.read_csv(filename)
        enrollee_ids = employee_df['enrollee_id']
        employee_df.rename(columns={'relevant_experience': 'relevent_experience'}, inplace=True)
        is_valid_data = check_for_fields(employee_df)
        if not is_valid_data:
            return {'error_message': "Kindly take a look at the attributes required in our must read column"}
        city_development_index = employee_df['city_development_index']
        employee_df = transform_df(employee_df)
        employee_df['city_development_index'] = city_development_index
        predictions = model.predict_proba(employee_df)
        predictions = {'enrollee_id': enrollee_ids.to_numpy(), 'predictions': predictions}
        response = json.dumps(predictions, cls=NumpyArrayEncoder)
        return response


if __name__ == "__main__":
    app.run(debug=True)
