Feature: Advanced Booking Rules

Background:
  * url baseUrl
  * def baseUrl = 'http://localhost:8000'
  * def token = call read('classpath:karate/helpers/auth-helper.feature') { username: 'admin@bcal.com', password: 'admin123' }

Scenario: Create Availability with Buffer Times
  Given path '/api/calendar/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "day_of_week": 1,
    "start_time": "09:00",
    "end_time": "17:00",
    "is_active": true,
    "buffer_before_minutes": 15,
    "buffer_after_minutes": 15,
    "min_notice_hours": 2,
    "max_booking_days": 30,
    "slot_duration_minutes": 60
  }
  """
  When method POST
  Then status 200
  And match response contains { "buffer_before_minutes": 15, "buffer_after_minutes": 15 }
  And match response contains { "min_notice_hours": 2, "max_booking_days": 30 }

Scenario: Create Recurring Availability
  Given path '/api/calendar/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "day_of_week": 1,
    "start_time": "09:00",
    "end_time": "17:00",
    "is_active": true,
    "is_recurring": true,
    "recurring_pattern": "weekly",
    "recurring_end_date": "2024-12-31T23:59:59Z",
    "recurring_days": [1, 3, 5]
  }
  """
  When method POST
  Then status 200
  And match response contains { "is_recurring": true, "recurring_pattern": "weekly" }

Scenario: Create Availability with Meeting Type
  Given path '/api/calendar/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "day_of_week": 2,
    "start_time": "10:00",
    "end_time": "16:00",
    "is_active": true,
    "meeting_type": "consultation",
    "meeting_description": "Professional consultation sessions",
    "meeting_location": "Conference Room A",
    "meeting_url": "https://meet.google.com/abc-defg-hij"
  }
  """
  When method POST
  Then status 200
  And match response contains { "meeting_type": "consultation" }
  And match response contains { "meeting_location": "Conference Room A" }

Scenario: Booking with Insufficient Notice
  Given path '/api/bookings/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "host_id": 1,
    "title": "Test Meeting",
    "description": "Test meeting description",
    "start_time": "2024-01-15T09:00:00Z",
    "end_time": "2024-01-15T10:00:00Z",
    "guest_email": "guest@example.com",
    "guest_name": "Guest User"
  }
  """
  When method POST
  Then status 400
  And match response.detail contains "insufficient notice"

Scenario: Booking Beyond Maximum Lead Time
  Given path '/api/bookings/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "host_id": 1,
    "title": "Test Meeting",
    "description": "Test meeting description",
    "start_time": "2024-12-15T09:00:00Z",
    "end_time": "2024-12-15T10:00:00Z",
    "guest_email": "guest@example.com",
    "guest_name": "Guest User"
  }
  """
  When method POST
  Then status 400
  And match response.detail contains "beyond maximum booking time"

Scenario: Get Available Slots with Buffer Times
  Given path '/api/calendar/slots/1'
  And param date = '2024-01-15'
  When method GET
  Then status 200
  And match response == '#array'
  And match response[*] contains { "start_time": "#string", "end_time": "#string" }
  And match response[*] contains { "available": "#boolean" }

Scenario: Update Availability with New Rules
  Given path '/api/calendar/#(availabilityId)'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "buffer_before_minutes": 30,
    "buffer_after_minutes": 30,
    "min_notice_hours": 4,
    "slot_duration_minutes": 90
  }
  """
  When method PUT
  Then status 200
  And match response contains { "buffer_before_minutes": 30, "buffer_after_minutes": 30 }
  And match response contains { "min_notice_hours": 4, "slot_duration_minutes": 90 }
