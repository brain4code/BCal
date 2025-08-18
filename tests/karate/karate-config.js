function fn() {
    var env = karate.env || 'dev';
    var config = {
        baseUrl: 'http://localhost:8000',
        apiUrl: 'http://localhost:8000/api',
        frontendUrl: 'http://localhost:3000'
    };
    
    if (env === 'dev') {
        config.baseUrl = 'http://localhost:8000';
        config.apiUrl = 'http://localhost:8000/api';
        config.frontendUrl = 'http://localhost:3000';
    } else if (env === 'prod') {
        config.baseUrl = 'http://localhost';
        config.apiUrl = 'http://localhost/api';
        config.frontendUrl = 'http://localhost';
    }
    
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
    
    // Test booking data
    config.testBooking = {
        host_id: 1,
        title: 'Test Meeting',
        description: 'Test meeting description',
        start_time: '2024-01-15T10:00:00Z',
        end_time: '2024-01-15T10:30:00Z',
        guest_email: 'guest@example.com',
        guest_name: 'Guest User'
    };
    
    // Test availability data
    config.testAvailability = {
        day_of_week: 1,
        start_time: '09:00',
        end_time: '17:00',
        is_active: true
    };
    
    return config;
}
