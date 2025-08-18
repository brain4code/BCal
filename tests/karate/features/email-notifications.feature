Feature: Email Notifications

Background:
  * url baseUrl
  * def baseUrl = 'http://localhost:8000'
  * def token = call read('classpath:karate/helpers/auth-helper.feature') { username: 'admin@bcal.com', password: 'admin123' }

Scenario: Email Service Configuration Check
  Given path '/api/admin/email/config'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response contains { "enabled": "#boolean" }

Scenario: Send Test Email
  Given path '/api/admin/email/test'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "recipient": "test@example.com",
    "subject": "Test Email",
    "message": "This is a test email from BCal"
  }
  """
  When method POST
  Then status 200
  And match response contains { "sent": true }

Scenario: Email Templates Available
  Given path '/api/admin/email/templates'
  And header Authorization = 'Bearer #(token)'
  When method GET
  Then status 200
  And match response contains { "templates": "#array" }
  And match response.templates[*] contains "booking_confirmation"
  And match response.templates[*] contains "booking_reminder"
  And match response.templates[*] contains "booking_cancellation"

Scenario: Update Email Settings
  Given path '/api/admin/email/settings'
  And header Authorization = 'Bearer #(token)'
  And request 
  """
  {
    "enabled": true,
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "test@example.com",
    "use_tls": true
  }
  """
  When method PUT
  Then status 200
  And match response contains { "enabled": true }
