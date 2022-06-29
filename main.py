from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from psycopg2 import Error
from typing import List
from minio import Minio
import uuid
import datetime
import psycopg2
import secrets
import json

bucket_name = datetime.datetime.today().strftime("%Y%m%d") #название корзины
app = FastAPI()

def get_request():
    conn = psycopg2.connect(dbname='Photos', user='postgres', 
                            password='1111', host='localhost')# подключение к бд
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(request_code) FROM inbox")
    result_last_record = cursor.fetchall()

    if len(result_last_record) != 0:
        if result_last_record[0][0] == None:
            req = 0
        else:
            req = result_last_record[0][0]
    cursor.close()
    conn.close()
    return req
        
        
try:
    client = Minio("localhost:9000", access_key = "admin", 
                   secret_key = "password", secure = False)  # Подключение к MIN.IO
except (Exception, Error) as error:
    print("Проблемы с подключением к min.io.", error)
    
        
found = client.bucket_exists(bucket_name)  # Проверка существавания корзины

if not found:
    client.make_bucket(bucket_name)  # Создаем корзину, если ее не существует
    print("Корзина была создана.")
else:
    print("Корзина существует.")

security = HTTPBasic(realm = "simple")
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "stanleyjobson")
    correct_password = secrets.compare_digest(credentials.password, "swordfish")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/users/me")
def read_current_user(username: str = Depends(get_current_username)):
    return {"username": username}

    
@app.delete("/frames/{request_code}")
async def delete(request_code, username: str = Depends(get_current_username)):
    try:
        conn = psycopg2.connect(dbname='Photos', user='postgres', 
                                password='1111', host='localhost')# подключение к бд
        cursor = conn.cursor()
        cursor.execute(f"SELECT file_name FROM inbox WHERE request_code = {request_code}")
        for row in cursor:
            client.remove_object(bucket_name, row[0])
            
        cursor.execute(f"DELETE FROM inbox WHERE request_code = {request_code}")
        conn.commit()
            
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("Соединение с PostgreSQL закрыто")
            


@app.get("/frames/{request_code}")
async def get_info(request_code, username: str = Depends(get_current_username)):
    try:
        conn = psycopg2.connect(dbname='Photos', user='postgres', 
                                password='1111', host='localhost')# подключение к бд
        cursor = conn.cursor()
        cursor.execute(f"SELECT file_name, date FROM inbox WHERE request_code ={request_code}")
        
    except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
    finally:
            if conn:
                return {f"{request_code}": [row for row in cursor]}
                cursor.close()
                conn.close()
                print("Соединение с PostgreSQL закрыто")

    

@app.post("/frames/")
async def create_upload_files(files: List[UploadFile] = File()):
    req = get_request() + 1
    data_set = []
    for i in files:
       if i.content_type == 'image/jpeg' and len(files) < 15:
           
        i.filename = str(uuid.uuid4()) + ".jpg"       
        client.fput_object(bucket_name, i.filename, i.file.fileno())  # Загружаем фотку в минио
        date = datetime.datetime.now().strftime("%d.%m.%Y/%H:%M")
        
        try:
            conn = psycopg2.connect(dbname='Photos', user='postgres', 
                                    password='1111', host='localhost')# подключение к бд
            cursor = conn.cursor()
            cursor.execute(
            f"INSERT INTO inbox (request_code, file_name, date) VALUES ({req},'{i.filename}','{date}')"
            )
            conn.commit()
            data_set.append({"Добавлено": i.filename})
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if conn:
                print("Запись успешна сделана")  
                cursor.close()
                conn.close()
                print("Соединение с PostgreSQL закрыто")
                return {"request_code:" + str(req) + json.dumps(data_set)}
       else:
            print("неправильное кол-во фотографий или иной формат")
            data_set.append({"Пропущено": i.filename})
            return {"request_code:" + str(req) + json.dumps(data_set)}

        



@app.get("/")
async def main():
    content = """
<body>
<form action="/frames/" enctype="multipart/form-data" method="post">
<input name="files" type="file" accept="image/jpeg" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)
