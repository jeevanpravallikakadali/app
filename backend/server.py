from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import logging
import aiofiles
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security setup
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback_secret_key')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# File upload setup
UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', '/app/backend/uploads'))
UPLOAD_DIR.mkdir(exist_ok=True)

# AI Chat setup
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Mount static files for uploaded documents
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    full_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class FamilyMember(BaseModel):
    name: str
    age: int
    gender: str
    relationship: str
    education: Optional[str] = None
    occupation: Optional[str] = None
    disability: bool = False

class Family(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    family_head_name: str
    age: int
    gender: str
    caste_category: str
    occupation: str
    annual_income: float
    education_level: str
    disability: bool
    family_members: List[FamilyMember]
    documents: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FamilyCreate(BaseModel):
    family_head_name: str
    age: int
    gender: str
    caste_category: str
    occupation: str
    annual_income: float
    education_level: str
    disability: bool
    family_members: List[FamilyMember]

class SchemeApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    family_id: str
    scheme_name: str
    status: str = "Not Applied"  # Not Applied, Applied, Approved, Rejected
    application_data: Dict[str, Any] = {}
    ai_reasoning: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    type: str = "info"  # info, success, warning, error
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

# Government schemes eligibility checker using AI
async def check_scheme_eligibility(family_data: Dict, scheme_name: str) -> Dict:
    """Use AI to check eligibility for a specific scheme"""
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"eligibility_{family_data['id']}_{scheme_name}",
        system_message="""You are an expert in Indian government schemes eligibility. 
        Analyze the family data against the specific scheme requirements and provide:
        1. Whether the family is eligible (true/false)
        2. Detailed reasoning explaining why
        3. Missing documents or criteria if not eligible
        4. Application data that can be auto-filled
        
        Respond in JSON format: {
            "eligible": boolean,
            "reasoning": "detailed explanation",
            "missing_requirements": ["list of missing items"],
            "application_data": {"key": "value pairs for auto-filling"}
        }"""
    ).with_model("openai", "gpt-4o")
    
    schemes_info = {
        "PM-KISAN": """
        Eligibility: All landholding farmer families regardless of landholding size
        Income: No specific limit but excludes income tax payers
        Exclusions: Government employees (except Class IV), MPs/MLAs, professionals (doctors, engineers, lawyers, CAs)
        Required: Aadhaar-linked bank account, land ownership documents
        """,
        "MGNREGA": """
        Eligibility: Rural households willing to do unskilled manual work
        Age: Adult members (18+ years)
        Work: Minimum 100 days wage employment per year
        Required: Rural residence proof, job card registration
        """,
        "PM-JAY": """
        Eligibility: Based on SECC 2011 data, economically vulnerable families
        Criteria: SC/ST households, landless laborers, female-headed households without adult males (16-59), 
        households with disabled members, single room kutcha houses
        Exclusions: Government employees, professionals, higher income groups
        Coverage: Health insurance up to ₹5 lakh per family per year
        """,
        "PMAY-Gramin": """
        Eligibility: Families without pucca house or living in kutcha houses
        Income: Monthly income not exceeding ₹15,000
        Land: Up to 2.5 acres irrigated or 5 acres unirrigated land
        Exclusions: Owners of vehicles, government employees, tax payers
        """,
        "Jan Aushadhi": """
        Eligibility: All citizens can access generic medicines at affordable prices
        Special eligibility for opening centers: State govts, NGOs, doctors, pharmacists, entrepreneurs
        Requirements: B.Pharma/D.Pharma qualified pharmacist
        """
    }
    
    scheme_info = schemes_info.get(scheme_name, "General government scheme")
    
    user_message = UserMessage(
        text=f"""
        Analyze this family data for {scheme_name} scheme eligibility:
        
        Family Head: {family_data['family_head_name']}, Age: {family_data['age']}, Gender: {family_data['gender']}
        Caste/Category: {family_data['caste_category']}
        Occupation: {family_data['occupation']}
        Annual Income: ₹{family_data['annual_income']}
        Education: {family_data['education_level']}
        Disability: {family_data['disability']}
        Family Members: {len(family_data['family_members'])} total
        
        Family Members Details:
        {[f"{member['name']} (Age: {member['age']}, {member['gender']}, {member['relationship']}, Occupation: {member.get('occupation', 'Not specified')}, Education: {member.get('education', 'Not specified')}, Disability: {member['disability']})" for member in family_data['family_members']]}
        
        Scheme Information for {scheme_name}:
        {scheme_info}
        
        Provide eligibility analysis in the requested JSON format.
        """
    )
    
    try:
        response = await chat.send_message(user_message)
        # Parse AI response (assuming it returns valid JSON)
        import json
        result = json.loads(response)
        return result
    except Exception as e:
        logging.error(f"AI eligibility check failed: {str(e)}")
        return {
            "eligible": False,
            "reasoning": f"Error in AI analysis: {str(e)}",
            "missing_requirements": ["AI analysis unavailable"],
            "application_data": {}
        }

# Routes
@api_router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"$or": [{"email": user_data.email}, {"username": user_data.username}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    del user_dict['password']
    
    user = User(**user_dict)
    user_doc = user.dict()
    user_doc['hashed_password'] = hashed_password
    await db.users.insert_one(user_doc)
    return user

@api_router.post("/login", response_model=Token)
async def login_user(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.post("/family", response_model=Family)
async def create_family(family_data: FamilyCreate, current_user: User = Depends(get_current_user)):
    family_dict = family_data.dict()
    family_dict['user_id'] = current_user.id
    
    family = Family(**family_dict)
    await db.families.insert_one(family.dict())
    
    # Create notification
    notification = Notification(
        user_id=current_user.id,
        title="Family Profile Created",
        message="Your family profile has been successfully created. We'll now check for eligible schemes.",
        type="success"
    )
    await db.notifications.insert_one(notification.dict())
    
    return family

@api_router.get("/family", response_model=Optional[Family])
async def get_family(current_user: User = Depends(get_current_user)):
    family = await db.families.find_one({"user_id": current_user.id})
    if family:
        return Family(**family)
    return None

@api_router.put("/family", response_model=Family)
async def update_family(family_data: FamilyCreate, current_user: User = Depends(get_current_user)):
    family_dict = family_data.dict()
    family_dict['updated_at'] = datetime.now(timezone.utc)
    
    result = await db.families.update_one(
        {"user_id": current_user.id},
        {"$set": family_dict}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Family not found")
    
    family = await db.families.find_one({"user_id": current_user.id})
    return Family(**family)

@api_router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    # Generate unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{current_user.id}_{document_type}_{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Update family documents
    await db.families.update_one(
        {"user_id": current_user.id},
        {"$push": {"documents": unique_filename}}
    )
    
    return {"filename": unique_filename, "message": "Document uploaded successfully"}

@api_router.post("/check-eligibility")
async def check_eligibility(current_user: User = Depends(get_current_user)):
    # Get family data
    family = await db.families.find_one({"user_id": current_user.id})
    if not family:
        raise HTTPException(status_code=404, detail="Family profile not found")
    
    # Define government schemes to check
    schemes = ["PM-KISAN", "MGNREGA", "PM-JAY", "PMAY-Gramin", "Jan Aushadhi"]
    
    results = []
    for scheme_name in schemes:
        # Check if already analyzed
        existing_application = await db.scheme_applications.find_one({
            "family_id": family['id'],
            "scheme_name": scheme_name
        }, {"_id": 0})
        
        if not existing_application:
            # Run AI eligibility check
            eligibility_result = await check_scheme_eligibility(family, scheme_name)
            
            # Create scheme application record
            application = SchemeApplication(
                family_id=family['id'],
                scheme_name=scheme_name,
                status="Eligible" if eligibility_result['eligible'] else "Not Eligible",
                application_data=eligibility_result['application_data'],
                ai_reasoning=eligibility_result['reasoning']
            )
            await db.scheme_applications.insert_one(application.dict())
            results.append(application.dict())
        else:
            results.append(existing_application)
    
    # Create notification about eligibility check
    eligible_schemes = [r for r in results if r['status'] == 'Eligible']
    notification = Notification(
        user_id=current_user.id,
        title="Eligibility Check Complete",
        message=f"Found {len(eligible_schemes)} eligible schemes for your family.",
        type="info"
    )
    await db.notifications.insert_one(notification.dict())
    
    return {"schemes": results}

@api_router.get("/eligible-schemes")
async def get_eligible_schemes(current_user: User = Depends(get_current_user)):
    family = await db.families.find_one({"user_id": current_user.id})
    if not family:
        return {"schemes": []}
    
    schemes = await db.scheme_applications.find({"family_id": family['id']}, {"_id": 0}).to_list(length=None)
    return {"schemes": schemes}

@api_router.post("/apply-scheme/{scheme_name}")
async def apply_to_scheme(scheme_name: str, current_user: User = Depends(get_current_user)):
    family = await db.families.find_one({"user_id": current_user.id})
    if not family:
        raise HTTPException(status_code=404, detail="Family profile not found")
    
    # Update application status
    result = await db.scheme_applications.update_one(
        {"family_id": family['id'], "scheme_name": scheme_name},
        {"$set": {"status": "Applied", "updated_at": datetime.now(timezone.utc)}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Scheme application not found")
    
    # Create notification
    notification = Notification(
        user_id=current_user.id,
        title=f"Applied to {scheme_name}",
        message=f"Successfully applied to {scheme_name} scheme. You will be notified of updates.",
        type="success"
    )
    await db.notifications.insert_one(notification.dict())
    
    return {"message": f"Successfully applied to {scheme_name}"}

@api_router.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"user_id": current_user.id}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=50)
    return {"notifications": notifications}

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(get_current_user)):
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()