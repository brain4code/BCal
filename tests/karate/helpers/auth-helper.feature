Feature: Authentication Helper

Background:
  * url baseUrl
  * def baseUrl = 'http://localhost:8000'

Scenario: Login and Get Token
  Given path '/api/auth/login'
  And form field username = '#(username)'
  And form field password = '#(password)'
  When method POST
  Then status 200
  And def token = response.access_token
