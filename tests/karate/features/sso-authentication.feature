Feature: SSO Authentication

Background:
  * url baseUrl
  * def baseUrl = 'http://localhost:8000'

Scenario: Auth0 Login Flow
  Given path '/api/auth/auth0/login'
  When method GET
  Then status 200
  And match response contains { "auth_url": "#string" }

Scenario: Auth0 Callback
  Given path '/api/auth/auth0/callback'
  And param code = 'test_auth_code'
  When method GET
  Then status 200
  And match response contains { "access_token": "#string" }
  And match response contains { "token_type": "bearer" }

Scenario: Auth0 User Profile
  Given path '/api/auth/auth0/profile'
  And header Authorization = 'Bearer #(auth0Token)'
  When method GET
  Then status 200
  And match response contains { "email": "#string" }
  And match response contains { "name": "#string" }

Scenario: Generic SSO Login Flow
  Given path '/api/auth/sso/login'
  When method GET
  Then status 200
  And match response contains { "auth_url": "#string" }

Scenario: Generic SSO Callback
  Given path '/api/auth/sso/callback'
  And param code = 'test_sso_code'
  When method GET
  Then status 200
  And match response contains { "access_token": "#string" }
  And match response contains { "token_type": "bearer" }

Scenario: SSO User Profile
  Given path '/api/auth/sso/profile'
  And header Authorization = 'Bearer #(ssoToken)'
  When method GET
  Then status 200
  And match response contains { "email": "#string" }
  And match response contains { "name": "#string" }

Scenario: Link SSO Account to Existing User
  Given path '/api/auth/link-sso'
  And header Authorization = 'Bearer #(localToken)'
  And request 
  """
  {
    "sso_provider": "auth0",
    "sso_user_id": "auth0|123456789"
  }
  """
  When method POST
  Then status 200
  And match response contains { "linked": true }

Scenario: Unlink SSO Account
  Given path '/api/auth/unlink-sso'
  And header Authorization = 'Bearer #(localToken)'
  And request 
  """
  {
    "sso_provider": "auth0"
  }
  """
  When method POST
  Then status 200
  And match response contains { "unlinked": true }

Scenario: Get User SSO Accounts
  Given path '/api/auth/sso-accounts'
  And header Authorization = 'Bearer #(localToken)'
  When method GET
  Then status 200
  And match response == '#array'

Scenario: SSO Configuration Check
  Given path '/api/auth/sso/config'
  When method GET
  Then status 200
  And match response contains { "auth0_enabled": "#boolean" }
  And match response contains { "generic_sso_enabled": "#boolean" }

Scenario: Auth0 Token Verification
  Given path '/api/auth/verify-auth0-token'
  And request 
  """
  {
    "token": "#(auth0Token)"
  }
  """
  When method POST
  Then status 200
  And match response contains { "valid": true }

Scenario: Generic SSO Token Verification
  Given path '/api/auth/verify-sso-token'
  And request 
  """
  {
    "token": "#(ssoToken)",
    "provider": "generic"
  }
  """
  When method POST
  Then status 200
  And match response contains { "valid": true }

Scenario: Invalid SSO Token
  Given path '/api/auth/verify-sso-token'
  And request 
  """
  {
    "token": "invalid_token",
    "provider": "auth0"
  }
  """
  When method POST
  Then status 401
  And match response contains { "valid": false }
