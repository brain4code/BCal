Feature: Calendar Availability Management

Background:
  * url baseUrl
  * def baseUrl = 'http://localhost:8000'
  * def token = call read('classpath:karate/helpers/auth-helper.feature') { username: 'admin@bcal.com', password: 'admin123' }

Scenario: Get User Availability
  Given path '/api/calendar/'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Create Availability Slot
  Given path '/api/calendar/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "day_of_week": 1,
    "start_time": "09:00",
    "end_time": "17:00",
    "is_active": true
  }
  """
  When method POST
  Then status 200
  And match response contains { "day_of_week": 1, "start_time": "09:00", "end_time": "17:00", "is_active": true }

Scenario: Create Availability with Invalid Time Range
  Given path '/api/calendar/'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "day_of_week": 1,
    "start_time": "17:00",
    "end_time": "09:00",
    "is_active": true
  }
  """
  When method POST
  Then status 422

Scenario: Update Availability Slot
  Given path '/api/calendar/#(availabilityId)'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "start_time": "10:00",
    "end_time": "18:00"
  }
  """
  When method PUT
  Then status 200
  And match response contains { "start_time": "10:00", "end_time": "18:00" }

Scenario: Delete Availability Slot
  Given path '/api/calendar/#(availabilityId)'
  And header Authorization = 'Bearer #(token)'
  When method DELETE
  Then status 200

Scenario: Get Available Slots for User
  Given path '/api/calendar/slots/1'
  And param date = '2024-01-15'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Get Available Slots for Non-existent User
  Given path '/api/calendar/slots/999'
  And param date = '2024-01-15'
  When method GET
  Then status 404

Scenario: Get Available Slots for Past Date
  Given path '/api/calendar/slots/1'
  And param date = '2020-01-01'
  When method GET
  Then status 200
  And match response == '#array'
