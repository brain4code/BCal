# BCal Karate Test Suite

This directory contains comprehensive API tests for the BCal calendar booking application using the Karate framework.

## 📋 **Test Coverage**

### **Authentication Tests** (`authentication.feature`)
- ✅ User registration with validation
- ✅ User login and token generation
- ✅ Token verification and user profile access
- ✅ Error handling for invalid credentials
- ✅ Duplicate email registration prevention

### **Calendar Management Tests** (`calendar.feature`)
- ✅ Availability slot creation and management
- ✅ Time validation and conflict detection
- ✅ Available slots generation
- ✅ Availability updates and deletion
- ✅ Error handling for invalid time ranges

### **Booking System Tests** (`bookings.feature`)
- ✅ Booking creation with conflict detection
- ✅ Booking management (view, update, cancel)
- ✅ Guest user creation
- ✅ Booking validation rules
- ✅ Error handling for invalid bookings

### **Admin Dashboard Tests** (`admin.feature`)
- ✅ Dashboard statistics retrieval
- ✅ User management operations
- ✅ Booking management operations
- ✅ Advanced filtering and search
- ✅ Admin-only endpoint access control

### **Email Notifications Tests** (`email-notifications.feature`)
- ✅ Email service configuration
- ✅ Email template management
- ✅ Test email sending
- ✅ Email settings updates

### **Advanced Booking Rules Tests** (`advanced-booking-rules.feature`)
- ✅ Buffer time configuration
- ✅ Minimum notice periods
- ✅ Maximum booking lead times
- ✅ Recurring availability patterns
- ✅ Meeting type configuration

### **SSO Authentication Tests** (`sso-authentication.feature`)
- ✅ Auth0 integration
- ✅ Generic SSO provider support
- ✅ OAuth flow testing
- ✅ Token verification
- ✅ Account linking/unlinking

## 🚀 **Running Tests**

### **Prerequisites**
1. Java 8 or higher
2. Maven or Gradle
3. BCal application running on `http://localhost:8000`

### **Setup**
```bash
# Install Karate dependencies
mvn clean install

# Or with Gradle
./gradlew clean build
```

### **Run All Tests**
```bash
# Run all feature files
mvn test -Dtest=KarateTest

# Run specific feature
mvn test -Dtest=KarateTest -Dkarate.options="classpath:karate/features/authentication.feature"

# Run with specific environment
mvn test -Dtest=KarateTest -Dkarate.env=prod
```

### **Run Tests in Parallel**
```bash
# Run tests in parallel (4 threads)
mvn test -Dtest=KarateTest -Dkarate.options="--threads 4"
```

### **Generate Reports**
```bash
# Generate HTML reports
mvn test -Dtest=KarateTest -Dkarate.options="--output target/karate-reports"

# View reports
open target/karate-reports/karate-summary.html
```

## 📁 **Test Structure**

```
tests/karate/
├── features/
│   ├── authentication.feature          # Authentication tests
│   ├── calendar.feature                # Calendar management tests
│   ├── bookings.feature                # Booking system tests
│   ├── admin.feature                   # Admin dashboard tests
│   ├── email-notifications.feature     # Email functionality tests
│   ├── advanced-booking-rules.feature  # Advanced booking rules tests
│   └── sso-authentication.feature      # SSO authentication tests
├── helpers/
│   ├── auth-helper.feature             # Authentication helper functions
│   └── common-utils.feature            # Common utility functions
├── data/
│   ├── test-users.json                 # Test user data
│   ├── test-bookings.json              # Test booking data
│   └── test-availability.json          # Test availability data
├── karate-config.js                    # Karate configuration
└── README.md                           # This file
```

## 🔧 **Configuration**

### **Environment Configuration** (`karate-config.js`)
```javascript
function fn() {
    var env = karate.env || 'dev';
    var config = {
        baseUrl: 'http://localhost:8000',
        apiUrl: 'http://localhost:8000/api',
        frontendUrl: 'http://localhost:3000'
    };
    
    if (env === 'dev') {
        config.baseUrl = 'http://localhost:8000';
    } else if (env === 'prod') {
        config.baseUrl = 'https://your-production-domain.com';
    }
    
    return config;
}
```

### **Test Data Management**
```javascript
// Common test data
config.testUser = {
    email: 'test@example.com',
    username: 'testuser',
    full_name: 'Test User',
    password: 'testpassword123',
    timezone: 'UTC'
};

config.adminUser = {
    email: 'admin@bcal.com',
    password: 'admin123'
};
```

## 📊 **Test Reports**

### **HTML Reports**
Karate generates detailed HTML reports including:
- Test execution summary
- Request/response details
- Screenshots (if configured)
- Performance metrics
- Error details and stack traces

### **JUnit Integration**
Tests can be run as part of CI/CD pipelines:
```bash
# Run tests in CI environment
mvn test -Dtest=KarateTest -Dkarate.env=ci -Dkarate.options="--output target/test-reports"
```

## 🧪 **Test Scenarios**

### **Positive Test Cases**
- ✅ Valid user registration
- ✅ Successful login
- ✅ Booking creation
- ✅ Availability management
- ✅ Admin operations

### **Negative Test Cases**
- ❌ Invalid credentials
- ❌ Duplicate email registration
- ❌ Booking conflicts
- ❌ Insufficient permissions
- ❌ Invalid data formats

### **Edge Cases**
- 🔄 Timezone handling
- 🔄 Date boundary conditions
- 🔄 Large data sets
- 🔄 Concurrent operations
- 🔄 Network failures

## 🔍 **Debugging Tests**

### **Enable Debug Mode**
```bash
# Run with debug logging
mvn test -Dtest=KarateTest -Dkarate.options="--debug"

# Run single scenario
mvn test -Dtest=KarateTest -Dkarate.options="classpath:karate/features/authentication.feature:5"
```

### **View Test Logs**
```bash
# View detailed logs
mvn test -Dtest=KarateTest -Dkarate.options="--logback.config=logback-test.xml"
```

### **Interactive Mode**
```bash
# Run tests interactively
mvn test -Dtest=KarateTest -Dkarate.options="--interactive"
```

## 📈 **Performance Testing**

### **Load Testing**
```bash
# Run load test with 10 concurrent users
mvn test -Dtest=KarateTest -Dkarate.options="classpath:karate/features/load-test.feature --threads 10"
```

### **Stress Testing**
```bash
# Run stress test with 50 concurrent users
mvn test -Dtest=KarateTest -Dkarate.options="classpath:karate/features/stress-test.feature --threads 50"
```

## 🔐 **Security Testing**

### **Authentication Tests**
- ✅ JWT token validation
- ✅ SSO token verification
- ✅ Permission checks
- ✅ Session management

### **Authorization Tests**
- ✅ Role-based access control
- ✅ Admin-only endpoints
- ✅ User data isolation
- ✅ API rate limiting

## 📝 **Best Practices**

### **Test Organization**
1. **Feature-based grouping**: Group related scenarios together
2. **Clear naming**: Use descriptive scenario names
3. **Data isolation**: Use unique test data for each test
4. **Cleanup**: Clean up test data after tests

### **Test Data Management**
1. **External data files**: Store test data in JSON files
2. **Dynamic data**: Generate unique data for each test run
3. **Environment-specific data**: Use different data for different environments

### **Error Handling**
1. **Expected errors**: Test both success and failure scenarios
2. **Validation**: Verify error messages and status codes
3. **Recovery**: Test system recovery after errors

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Connection Refused**
```bash
# Check if application is running
curl http://localhost:8000/health

# Start the application
docker-compose -f docker-compose.dev.yml up -d
```

#### **Authentication Failures**
```bash
# Check default admin credentials
# Email: admin@bcal.com
# Password: admin123

# Verify JWT token generation
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@bcal.com&password=admin123"
```

#### **Database Issues**
```bash
# Check database connection
docker-compose -f docker-compose.dev.yml logs postgres

# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

## 📞 **Support**

For issues with the test suite:
1. Check the troubleshooting section above
2. Review the Karate documentation: https://github.com/karatelabs/karate
3. Check the application logs for errors
4. Verify the application is running and accessible

## 📚 **Additional Resources**

- [Karate Framework Documentation](https://github.com/karatelabs/karate)
- [Karate Examples](https://github.com/karatelabs/karate/tree/master/karate-demo)
- [BCal API Documentation](http://localhost:8000/docs)
- [BCal Project README](../README.md)
