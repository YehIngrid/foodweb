from fastapi import FastAPI

app = FastAPI()

#sign up = add user
@app.post("/api/signup")
def getAccount(email, password, name):
    return {"email": email, "password": password, "name": name}

#log in
@app.post("/api/login")
def getAccount(email, password, name):
    return {"email": email, "password": password, "name": name}
