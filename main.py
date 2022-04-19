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
    password="password",
    database="phone"
)

mycursor = mydb.cursor()

app = FastAPI()

# for CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])


# for CORS

class LoginUser(BaseModel):
    aadhaar_number: str
    password: str


class UserAadhaar(BaseModel):
    user_aadhaar_number: str


class EmailIMEI(BaseModel):
    seller_aadhaar: str
    IMEI: str


class BookPickupSchema(BaseModel):
    IMEI: str
    address: str
    state: str
    city: str
    pincode: int
    landmark: str

class updateDeviceOwnershipSchema(BaseModel):
    IMEI: str
    buyer_aadhaar: str


@app.post("/login")
def root(request_body: LoginUser):
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
def root(request_body: UserAadhaar):
    mycursor.execute("SELECT * FROM phone_ownership WHERE owner_aadhaar = {}".format(request_body.user_aadhaar_number))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    mycursor.execute("SELECT * FROM lost_record")
    columns = mycursor.description
    lost_result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    lost_list=[]
    for device in lost_result:
        lost_list.append(device['IMEI'])
    res = [i for i in result if not (i['IMEI'] in lost_list)]
    return res


@app.post("/get-user-name")
def root(request_body: UserAadhaar):
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


@app.post("/verify-owner")
def root(request_body: EmailIMEI):
    mycursor.execute("SELECT * FROM phone_ownership WHERE IMEI = {}".format(request_body.IMEI))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    if not result:
        result = [{"status_code": 1,
                   "details": "No such Device exists",
                   "owner_aadhaar": "NONE",
                   "IMEI": "NONE",
                   "manufacturer": "NONE",
                   "model_name": "NONE"}]
        return result
    if result[0]['owner_aadhaar'] == request_body.seller_aadhaar:
        result[0]['status_code'] = 0
        result[0]['details'] = "Owner verified successfully"
    return result


@app.get("/get-all-states")
def root():
    mycursor.execute("SELECT DISTINCT state FROM indian_cities")
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    result[0]['status_code'] = 0
    result[0]['details'] = "All states fetched successfully"
    return result


@app.post("/book-pickup-entry")
def root(request_body: BookPickupSchema):
    mycursor.execute(
        "INSERT INTO pickup_requests (IMEI, address, state, city, pincode, landmark) VALUES ({},{},{},{},{},{})".format(
            "\"" + request_body.IMEI + "\"", "\"" + request_body.address + "\"", "\"" + request_body.state + "\"",
            "\"" + request_body.city + "\"", request_body.pincode, "\"" + request_body.landmark + "\""))
    mydb.commit()
    result = [{}]
    result[0]['status_code'] = 0
    result[0]['details'] = "Successfully placed pickup request"
    return result


@app.get("/book-pickup-status/{IMEI}")
def root(IMEI: str):
    mycursor.execute("SELECT * FROM pickup_requests where IMEI={}".format("\"" + IMEI + "\""))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    if len(result) == 1:
        return {"status_code": 0,
                "message": "Found IMEI={} in pickup request database".format(IMEI)}
    elif len(result) == 0:
        return {"status_code": 1,
                "message": "Not found IMEI={} in pickup request database".format(IMEI)}


@app.post("/fetch-transfer-requests")
def root(request_body: UserAadhaar):
    mycursor.execute(
        "SELECT * FROM transfer_requests WHERE transfer_from_aadhaar = {}".format(request_body.user_aadhaar_number))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    return result


@app.post("/check-owner")
def root(IMEI: str):
    mycursor.execute("SELECT * FROM phone_ownership WHERE IMEI = {}".format(IMEI))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    if len(result) == 0:
        result = [{}]
        result[0]['status_code'] = 1
        result[0]['message'] = 'Device not found in Database'
    else:
        result[0]['status_code'] = 0
        result[0]['message'] = 'Device found in Database'
    return result


@app.post("/report-theft")
def root(IMEI: str):
    mycursor.execute(
        "INSERT INTO lost_record (IMEI) VALUES ({})".format(
            "\"" + IMEI + "\""))
    mydb.commit()
    result = [{}]
    result[0]['status_code'] = 0
    result[0]['details'] = "Successfully reported device as lost"
    return result

@app.get("/check-lost-status/{IMEI}")
def root(IMEI: str):
    mycursor.execute("SELECT * FROM lost_record where IMEI={}".format("\"" + IMEI + "\""))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    if len(result) == 1:
        return [{"status_code": 0,
                "message": "Found IMEI={} in lost_record database".format(IMEI)}]
    elif len(result) == 0:
        return [{"status_code": 1,
                "message": "Not found IMEI={} in lost_record database".format(IMEI)}]


@app.post("/update-device-ownership")
def root(request_body: updateDeviceOwnershipSchema):
    mycursor.execute(
        "UPDATE phone_ownership SET owner_aadhaar = {}  WHERE IMEI = {}".format("\"" +request_body.buyer_aadhaar + "\"", "\"" + request_body.IMEI + "\""))
    mydb.commit()
    mycursor.execute(
        "SELECT * FROM phone_ownership WHERE IMEI = {}".format("\"" + request_body.IMEI + "\""))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    result[0]['status_code'] = 0
    result[0]['details'] = "Successfully updated owner"
    return result

@app.post("/detete-transfer-request")
def root(IMEI: str):
    mycursor.execute(
        "DELETE FROM transfer_requests WHERE IMEI = {}".format("\"" + IMEI + "\""))
    mydb.commit()
    result = [{}]
    result[0]['status_code'] = 0
    result[0]['details'] = "Successfully removed the transfer request from database"
    return result

@app.post("/get-transfer-request-by-IMEI/{IMEI}")
def root(IMEI: str):
    mycursor.execute("SELECT * FROM transfer_requests where IMEI={}".format("\"" + IMEI + "\""))
    columns = mycursor.description
    result = [{columns[index][0]: column for index, column in enumerate(value)} for value in mycursor.fetchall()]
    if len(result) == 1:
        return [{"status_code": 0,
                 "message": "Found IMEI={} in transfer_requests database".format(IMEI)}]
    elif len(result) == 0:
        return [{"status_code": 1,
                 "message": "Not found IMEI={} in transfer_requests database".format(IMEI)}]


