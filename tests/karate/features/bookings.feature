Feature: Booking System

Background:
  * url baseUrl
  * def baseUrl = 'http://localhost:8000'
  * def token = call read('classpath:karate/helpers/auth-helper.feature') { username: 'admin@bcal.com', password: 'admin123' }

Scenario: Create Booking
  Given path '/api/bookings/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "host_id": 1,
    "title": "Test Meeting",
    "description": "Test meeting description",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:30:00Z",
    "guest_email": "guest@example.com",
    "guest_name": "Guest User"
  }
  """
  When method POST
  Then status 200
  And match response contains { "title": "Test Meeting", "status": "PENDING" }
  And match response contains { "guest_email": "guest@example.com", "guest_name": "Guest User" }

Scenario: Create Booking with Conflict
  Given path '/api/bookings/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "host_id": 1,
    "title": "Conflicting Meeting",
    "description": "This should conflict",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:30:00Z",
    "guest_email": "guest2@example.com",
    "guest_name": "Guest User 2"
  }
  """
  When method POST
  Then status 400
  And match response.detail contains "conflict"

Scenario: Get User Bookings
  Given path '/api/bookings/'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Get Specific Booking
  Given path '/api/bookings/#(bookingId)'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response contains { "id": "#(bookingId)" }

Scenario: Update Booking
  Given path '/api/bookings/#(bookingId)'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "title": "Updated Meeting Title",
    "description": "Updated description"
  }
  """
  When method PUT
  Then status 200
  And match response contains { "title": "Updated Meeting Title" }

Scenario: Cancel Booking
  Given path '/api/bookings/#(bookingId)'
  And header Authorization = 'Bearer #(token)'
  When method DELETE
  Then status 200

Scenario: Create Booking for Non-existent Host
  Given path '/api/bookings/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "host_id": 999,
    "title": "Test Meeting",
    "description": "Test meeting description",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:30:00Z",
    "guest_email": "guest@example.com",
    "guest_name": "Guest User"
  }
  """
  When method POST
  Then status 404

Scenario: Create Booking with Invalid Time Range
  Given path '/api/bookings/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "host_id": 1,
    "title": "Test Meeting",
    "description": "Test meeting description",
    "start_time": "2024-01-15T10:30:00Z",
    "end_time": "2024-01-15T10:00:00Z",
    "guest_email": "guest@example.com",
    "guest_name": "Guest User"
  }
  """
  When method POST
  Then status 422
