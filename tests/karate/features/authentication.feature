Feature: Authentication System

Background:
  * url baseUrl
  * def baseUrl = 'http://localhost:8000'

Scenario: User Registration
  Given path '/api/auth/register'
  And request 
  """
  {
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "testpassword123",
    "timezone": "UTC"
  }
  """
  When method POST
  Then status 200
  And match response contains { "email": "test@example.com", "username": "testuser", "full_name": "Test User" }
  And match response contains { "is_active": true, "is_admin": false }

Scenario: User Registration with Invalid Email
  Given path '/api/auth/register'
  And request 
  """
  {
    "email": "invalid-email",
    "username": "testuser",
    "full_name": "Test User",
    "password": "testpassword123",
    "timezone": "UTC"
  }
  """
  When method POST
  Then status 422

Scenario: User Registration with Duplicate Email
  Given path '/api/auth/register'
  And request 
  """
  {
    "email": "admin@bcal.com",
    "username": "newuser",
    "full_name": "New User",
    "password": "testpassword123",
    "timezone": "UTC"
  }
  """
  When method POST
  Then status 400
  And match response.detail contains "Email already registered"

Scenario: User Login
  Given path '/api/auth/login'
  And form field username = 'admin@bcal.com'
  And form field password = 'admin123'
  When method POST
  Then status 200
  And match response contains { "token_type": "bearer" }
  And match response.access_token != null

Scenario: User Login with Invalid Credentials
  Given path '/api/auth/login'
  And form field username = 'admin@bcal.com'
  And form field password = 'wrongpassword'
  When method POST
  Then status 401

Scenario: Get Current User Profile
  Given path '/api/auth/me'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response contains { "email": "admin@bcal.com", "is_admin": true }

Scenario: Get Current User Profile without Token
  Given path '/api/auth/me'
  When method GET
  Then status 401

Scenario: Get Current User Profile with Invalid Token
  Given path '/api/auth/me'
  And header Authorization = 'Bearer invalid-token'
  When method GET
  Then status 401
