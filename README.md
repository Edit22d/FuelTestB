# FuelConnect Django Backend

Authentication backend for the FuelConnect Flutter app.

## Quick Start

```bash
# 1. Install dependencies
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers

# 2. Run migrations
python manage.py migrate

# 3. (Optional) Create admin superuser
python manage.py createsuperuser

# 4. Start dev server
python manage.py runserver 0.0.0.0:8000
```

The server runs on `http://0.0.0.0:8000`.  
Flutter Android emulator reaches it via `http://10.0.2.2:8000`.

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register/` | None | Register customer or driver |
| POST | `/api/v1/auth/login/` | None | Login with email or phone |
| POST | `/api/v1/auth/forgot-password/` | None | Send 6-digit OTP to email |
| POST | `/api/v1/auth/reset-password/` | None | Verify OTP & set new password |
| GET  | `/api/v1/auth/me/` | Bearer | Get current user profile |
| POST | `/api/v1/auth/token/refresh/` | None | Refresh access token |

---

## Request / Response Examples

### POST /api/v1/auth/register/ (customer)
```json
// Request
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone_number": "+256740000001",
  "password": "Test@1234",
  "confirm_password": "Test@1234",
  "user_type": "customer",
  "location": "Kampala"
}

// 201 Created
{
  "success": true,
  "message": "Account created successfully! Please log in.",
  "user": { "id": 1, "email": "...", "full_name": "...", ... },
  "tokens": { "access": "...", "refresh": "..." }
}
```

### POST /api/v1/auth/register/ (driver — extra fields)
```json
{
  ...same as customer...
  "user_type": "driver",
  "vehicle_type": "Motorcycle",
  "vehicle_number": "UAX 123A",
  "license_number": "DL123456"
}
```

### POST /api/v1/auth/login/
```json
// Request (email OR phone)
{ "email_or_phone": "john@example.com", "password": "Test@1234" }
{ "email_or_phone": "+256740000001",   "password": "Test@1234" }

// 200 OK
{ "success": true, "user": {...}, "tokens": { "access": "...", "refresh": "..." } }
```

### POST /api/v1/auth/forgot-password/
```json
// Request
{ "email": "john@example.com" }

// 200 OK (always, for security)
{
  "success": true,
  "message": "If that email exists in our system, a reset code has been sent.",
  "debug_token": "482910",          // ← only present when DEBUG=True
  "debug_note": "debug_token is only present when DEBUG=True"
}
```

### POST /api/v1/auth/reset-password/
```json
// Request
{
  "email": "john@example.com",
  "token": "482910",
  "new_password": "NewPass@5678",
  "confirm_new_password": "NewPass@5678"
}

// 200 OK
{ "success": true, "message": "Password reset successfully. You can now log in." }
```

### GET /api/v1/auth/me/
```
Authorization: Bearer <access_token>
```

---

## Bruno Testing

1. Open Bruno → **Open Collection** → select `bruno/FuelConnect_API/`
2. Select the **Local** environment (top-right)
3. Run requests in order: Register → Login → Forgot Password → Reset Password → Me

The Login and Register requests auto-save tokens to the `Local` environment,
so the **Me** and **Refresh Token** requests work out of the box.

---

## Password Rules (matches Flutter validation)
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter  
- At least 1 number
- At least 1 special character

## Phone Format
- Must include country code: `+256 740 000-0000` or `+256740000000`

## OTP
- 6-digit numeric code
- Expires in 10 minutes (configurable via `OTP_EXPIRY_MINUTES` in settings)
- Previous OTPs are invalidated when a new one is requested
- In production: OTP is emailed. In dev (DEBUG=True): returned in response as `debug_token`
