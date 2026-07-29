from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine

from models.user import User
from models.course import Course
from models.lesson import Lesson
from models.enrollment import Enrollment
from models.payment import Payment
from models.progress import Progress
from models.certificate import Certificate
from models.review import Review 
from models.live_class import LiveClass
from models.settings import Settings
from models.purchase import Purchase

from routers.auth import router as auth_router
from routers.course import router as course_router
from routers.lesson import router as lesson_router
from routers.enrollment import router as enrollment_router
from routers.payment import router as payment_router
from routers.progress import router as progress_router
from routers.certificate import router as certificate_router
from routers.dashboard import router as dashboard_router
from routers.admin_dashboard import router as admin_dashboard_router
from routers.review import router as review_router
from routers.admin import router as admin_router
from routers.live_class import router as live_class_router 
from routers.settings import router as settings_router 
from routers.student_lessons import router as student_router
from routers.student_courses import router as student_courses_router
from routers.purchases import router as purchases_router

from fastapi.staticfiles import StaticFiles


app = FastAPI(title="EditingPro API")

app.include_router(auth_router)
app.include_router(course_router)
app.include_router(lesson_router)
app.include_router(enrollment_router)
app.include_router(payment_router)
app.include_router(progress_router)
app.include_router(certificate_router)
app.include_router(dashboard_router)
app.include_router(admin_dashboard_router)
app.include_router(review_router)
app.include_router(admin_router)
app.include_router(live_class_router)
app.include_router(settings_router)
app.include_router(student_router)
app.include_router(student_courses_router)
app.include_router(purchases_router)

Base.metadata.create_all(bind=engine)


app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:3001",
    "http://localhost:3003",   # Vite
    "http://localhost:5680",
    "https://editingpro.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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