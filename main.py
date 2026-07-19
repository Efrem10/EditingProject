from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()


origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:3001",
    "http://localhost:3003",
    "https://editingpro.netlify.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "title": "EditingPro",
        "message": "Welcome to EditingPro!"
    }


@app.get("/about")
def about():
    return {
        "about": "We provide professional editing services."
    }


@app.get("/services")
def services():
    return {
        "services": [
            "Photo Editing",
            "Logo Design",
            "Banner Design",
            "Background Removal"
        ]
    }


@app.get("/contact")
def contact():
    return {
        "phone": "+251900000000",
        "email": "info@editpro.com",
        "address": "Addis Ababa, Ethiopia"
    }


