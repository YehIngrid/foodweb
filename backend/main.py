from fastapi import FastAPI

app = FastAPI()

#login, signup
@app.get("/account")
def getAccount(email, password, name):
    return
