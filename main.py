# command to start server `uvicorn main:app --reload`
import json
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from pydantic import BaseModel

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="phone"
)

mycursor = mydb.cursor()

app = FastAPI()

# for CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],allow_headers=["*"])
# for CORS

class login_user(BaseModel):
    aadhaar_number: str
    password: str


class linked_devices(BaseModel):
    user_aadhaar_number: str


@app.post("/login")
def root(request_body: login_user):
    mycursor.execute("SELECT * FROM user_login")
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    for credentials in result:
        if request_body.aadhaar_number == credentials['aadhaar_number']:
            if request_body.password == credentials['password']:
                return {'statusCode': 0, 'message': 'Login Successful'}
            else:
                return {'statusCode': 1, 'message': 'Password does not match'}
    else:
        return {'statusCode': 2, 'message': 'Aadhaar not registered'}


@app.post("/get-linked-devices")
def root(request_body: linked_devices):
    mycursor.execute("SELECT * FROM phone_ownership WHERE owner_aadhaar = {}".format(request_body.user_aadhaar_number))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    return result


@app.post("/get-user-name")
def root(request_body: linked_devices):
    mycursor.execute("SELECT * FROM user_details WHERE aadhaar_number = {}".format(request_body.user_aadhaar_number))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    # print(result)
    return result

@app.get("/fetch-device-details/{IMEI}")
def fetch_phone_details(IMEI: str):
    mycursor.execute("SELECT * FROM phone_ownership WHERE IMEI = {}".format(IMEI))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    return result
