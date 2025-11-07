# Neurula Health API - Postman Testing Guide

## Server Status
✅ **Server Running**: http://localhost:8000
✅ **API Docs (Swagger)**: http://localhost:8000/docs
✅ **Database**: SQLite (neurula_dev.db)

## Setup Postman

### 1. Import Collection
1. Open Postman
2. Click **Import** button
3. Select `Neurula_API_Postman_Collection.json`
4. Collection will appear in the left sidebar

### 2. Environment Variables (Auto-configured)
The collection includes environment variables:
- `baseUrl`: http://localhost:8000
- `accessToken`: (auto-populated after login)
- `refreshToken`: (auto-populated after login)

## Testing Workflow

### Step 1: Health Check
**Request**: `GET /health`
**Expected**: Status 200, application info

```json
{
  "status": "healthy",
  "app_name": "Neurula Health API",
  "version": "1.0.0"
}
```

### Step 2: Register a User
**Request**: `POST /api/v1/auth/register`

**Sample Body**:
```json
{
  "full_name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+971501234567",
  "password": "SecurePass123!",
  "registration_method": "manual",
  "date_of_birth": "1990-01-15",
  "gender": "Male",
  "nationality": "UAE",
  "height": 175,
  "weight": 70,
  "emirate": "Dubai"
}
```

**Expected Response**:
```json
{
  "message": "Registration successful. Please verify your email with the OTP sent.",
  "user_id": "...",
  "email": "john.doe@example.com",
  "otp_sent": true
}
```

**⚠️ IMPORTANT**:
- Since Redis is not running, OTP will be logged to console
- Check `server.log` file for the OTP:
  ```bash
  tail -f server.log | grep "OTP for"
  ```
- You'll see something like: `OTP for john.doe@example.com: 123456`

### Step 3: Verify OTP
**Request**: `POST /api/v1/auth/verify-otp`

**Body**:
```json
{
  "email": "john.doe@example.com",
  "otp": "123456"
}
```

**Note**: Replace `123456` with the actual OTP from the log file.

**Expected Response**:
```json
{
  "message": "Verification successful",
  "verified": true,
  "user": { ... },
  "tokens": {
    "access_token": "eyJ0eXAi...",
    "refresh_token": "eyJ0eXAi...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

### Step 4: Login (Alternative to OTP Verification)
**Request**: `POST /api/v1/auth/login`

**Body**:
```json
{
  "username": "john.doe@example.com",
  "password": "SecurePass123!",
  "remember_me": false
}
```

**Note**: Login only works AFTER OTP verification is complete.

**Expected**: Tokens will be automatically saved to environment variables.

### Step 5: Get Current User
**Request**: `GET /api/v1/auth/me`
**Headers**: `Authorization: Bearer {{accessToken}}`

**Expected**: User profile information

### Step 6: Get Patient Profile
**Request**: `GET /api/v1/patients/me`
**Headers**: `Authorization: Bearer {{accessToken}}`

**Expected**: Patient profile with completion percentage

### Step 7: Update Patient Profile
**Request**: `PUT /api/v1/patients/me`
**Headers**:
- `Authorization: Bearer {{accessToken}}`
- `Content-Type: application/json`

**Body**:
```json
{
  "height": 180,
  "weight": 75,
  "blood_group": "O+",
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_phone": "+971509876543"
}
```

### Step 8: Get Profile Completion
**Request**: `GET /api/v1/patients/me/profile-completion`
**Headers**: `Authorization: Bearer {{accessToken}}`

**Expected**:
```json
{
  "percentage": 75.5,
  "missing_fields": ["blood_group", "medical_conditions"]
}
```

### Step 9: Search Doctors (No Auth Required)
**Request**: `GET /api/v1/doctors?specialty=Cardiology&page=1&limit=10`

**Expected**:
```json
{
  "doctors": [],
  "total": 0,
  "page": 1,
  "limit": 10,
  "total_pages": 0
}
```

**Note**: Empty because no doctors are registered yet.

### Step 10: Get Specialties
**Request**: `GET /api/v1/doctors/specialties`

**Expected**: List of all specialties (empty initially)

## Common Issues & Solutions

### Issue 1: "Account not verified"
**Problem**: Trying to login before OTP verification
**Solution**: Complete OTP verification first (Step 3)

### Issue 2: "Invalid OTP"
**Problem**: Using wrong OTP or OTP expired (5 min expiry)
**Solution**: Check `server.log` for the correct OTP or request a new one with "Resend OTP"

### Issue 3: "Invalid credentials"
**Problem**: Wrong email/password or user doesn't exist
**Solution**: Verify email and password match registration

### Issue 4: "401 Unauthorized"
**Problem**: Missing or invalid access token
**Solution**: Login again to get fresh tokens

### Issue 5: "Rate limit exceeded"
**Problem**: Too many requests
**Solution**: Wait 60 seconds before retrying

## Password Requirements

✅ Minimum 8 characters
✅ At least one uppercase letter
✅ At least one lowercase letter
✅ At least one digit
✅ At least one special character

Example valid password: `SecurePass123!`

## Phone Number Format

✅ Must start with +971 (UAE country code)
✅ Followed by 9 digits
✅ Example: `+971501234567`

## Emirates ID Format

✅ Must start with 784
✅ Total 15 digits
✅ Format: `784-XXXX-XXXXXXX-X`
✅ Example: `784-1234-1234567-1`

## Viewing Server Logs

### Real-time logs:
```bash
tail -f /home/souravkundu721129/Neurula\ Health/neurula-patient-app/neurula-patient-backend/server.log
```

### Find OTP:
```bash
grep "OTP for" /home/souravkundu721129/Neurula\ Health/neurula-patient-app/neurula-patient-backend/server.log
```

### Latest errors:
```bash
grep "ERROR" /home/souravkundu721129/Neurula\ Health/neurula-patient-app/neurula-patient-backend/server.log | tail -10
```

## Stopping the Server

```bash
# Find the process
ps aux | grep uvicorn

# Kill by port
lsof -ti:8000 | xargs kill -9

# Or kill by process name
pkill -f "uvicorn app.main:app"
```

## Restarting the Server

```bash
cd "/home/souravkundu721129/Neurula Health/neurula-patient-app/neurula-patient-backend"
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
```

## Testing with cURL (Alternative to Postman)

### Register:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "phone": "+971509999999",
    "password": "TestPass123!",
    "registration_method": "manual",
    "gender": "Male"
  }'
```

### Health Check:
```bash
curl http://localhost:8000/health
```

### Get Swagger UI:
Open in browser: http://localhost:8000/docs

## Next Steps

1. ✅ Test all authentication endpoints
2. ✅ Test patient profile management
3. ✅ Create a doctor user (repeat registration with different email)
4. 🔄 Test appointment booking (future feature)
5. 🔄 Test payment integration (future feature)

## Support

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Server Log**: `server.log`
- **Database File**: `neurula_dev.db`

## Quick Reference

| Endpoint | Method | Auth Required |
|----------|--------|---------------|
| `/health` | GET | No |
| `/api/v1/auth/register` | POST | No |
| `/api/v1/auth/verify-otp` | POST | No |
| `/api/v1/auth/login` | POST | No |
| `/api/v1/auth/me` | GET | Yes |
| `/api/v1/patients/me` | GET | Yes |
| `/api/v1/patients/me` | PUT | Yes |
| `/api/v1/doctors` | GET | No |
| `/api/v1/doctors/specialties` | GET | No |

**Happy Testing! 🚀**
