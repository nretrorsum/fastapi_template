from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/items/")
async def create_item(item: str):
    return item

@app.delete("/items/delete")
async def delete_item(item: str):
    return {"message": f"Item '{item}' deleted successfully"}

@app.get("/cheburnya")
async def root():
    return {"message": "parasha cheburnya"}

@app.post('/auth')
async def return_password(password: str):
    return {"password": password}