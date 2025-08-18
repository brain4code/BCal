Feature: Admin Dashboard

Background:
  * url baseUrl
  * def baseUrl = 'http://localhost:8000'
  * def token = call read('classpath:karate/helpers/auth-helper.feature') { username: 'admin@bcal.com', password: 'admin123' }

Scenario: Get Dashboard Statistics
  Given path '/api/admin/dashboard'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response contains { "total_bookings": "#number", "total_users": "#number", "active_users": "#number" }
  And match response contains { "pending_bookings": "#number", "confirmed_bookings": "#number", "cancelled_bookings": "#number" }

Scenario: Get All Users
  Given path '/api/admin/users'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Get All Users with Search Filter
  Given path '/api/admin/users'
  And param search = 'admin'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Get All Users with Active Filter
  Given path '/api/admin/users'
  And param is_active = 'true'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Get All Users with Admin Filter
  Given path '/api/admin/users'
  And param is_admin = 'true'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Get All Bookings
  Given path '/api/admin/bookings'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Get All Bookings with Search Filter
  Given path '/api/admin/bookings'
  And param search = 'meeting'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Get All Bookings with Status Filter
  Given path '/api/admin/bookings'
  And param status = 'PENDING'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Get All Bookings with Date Range Filter
  Given path '/api/admin/bookings'
  And param start_date = '2024-01-01'
  And param end_date = '2024-12-31'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: Update Booking Status
  Given path '/api/admin/bookings/#(bookingId)/status'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "status": "CONFIRMED",
    "title": "Updated Title"
  }
  """
  When method PUT
  Then status 200
  And match response contains { "status": "CONFIRMED", "title": "Updated Title" }

Scenario: Delete Booking
  Given path '/api/admin/bookings/#(bookingId)'
  And header Authorization = 'Bearer #(token)'
  When method DELETE
  Then status 200

Scenario: Toggle User Admin Status
  Given path '/api/admin/users/#(userId)/toggle-admin'
  And header Authorization = 'Bearer #(token)'
  When method PUT
  Then status 200
  And match response contains { "is_admin": "#boolean" }

Scenario: Toggle User Active Status
  Given path '/api/admin/users/#(userId)/toggle-active'
  And header Authorization = 'Bearer #(token)'
  When method PUT
  Then status 200
  And match response contains { "is_active": "#boolean" }

Scenario: Access Admin Endpoints without Admin Privileges
  Given path '/api/admin/dashboard'
  And header Authorization = 'Bearer #(userToken)'
  When method GET
  Then status 403

Scenario: Access Admin Endpoints without Authentication
  Given path '/api/admin/dashboard'
  When method GET
  Then status 401
