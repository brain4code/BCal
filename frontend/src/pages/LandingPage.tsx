import React from 'react';
import { Link } from 'react-router-dom';
import { 
  CalendarIcon, 
  UsersIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ArrowRightIcon,
  StarIcon
} from '@heroicons/react/24/outline';

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <CalendarIcon className="h-8 w-8 text-primary-600 mr-3" />
              <span className="text-2xl font-bold text-gray-900">BCal</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/teams"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                Book Now
              </Link>
              <Link
                to="/login"
                className="text-gray-500 hover:text-gray-700 px-3 py-2 text-sm font-medium"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Book Meetings with
              <span className="text-primary-600"> Your Team</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Schedule appointments with our expert teams. See all available agents, 
              choose your preferred time, and get instant confirmation with calendar invites.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/teams"
                className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 transition-colors"
              >
                <CalendarIcon className="h-5 w-5 mr-2" />
                Book Your Meeting
                <ArrowRightIcon className="h-5 w-5 ml-2" />
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center px-8 py-4 border border-gray-300 text-lg font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
              >
                Sign In to Manage
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose BCal?
            </h2>
            <p className="text-xl text-gray-600">
              Professional team booking with intelligent assignment and seamless calendar integration
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <UsersIcon className="h-12 w-12 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Team Availability
              </h3>
              <p className="text-gray-600">
                See all available team members for any date. Choose from multiple experts 
                based on your needs and their availability.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center mb-4">
                <ClockIcon className="h-12 w-12 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Intelligent Assignment
              </h3>
              <p className="text-gray-600">
                Our system automatically assigns the best available agent based on 
                workload, expertise, and availability.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center mb-4">
                <CheckCircleIcon className="h-12 w-12 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Instant Calendar Integration
              </h3>
              <p className="text-gray-600">
                Get calendar invites automatically sent to your email. 
                Works with Google Calendar, Outlook, and Apple Calendar.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600">
              Simple 3-step process to book your meeting
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="flex items-center justify-center w-12 h-12 bg-primary-600 text-white rounded-full text-xl font-bold">
                  1
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Choose Your Team
              </h3>
              <p className="text-gray-600">
                Browse available teams and select the one that best fits your needs.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="flex items-center justify-center w-12 h-12 bg-primary-600 text-white rounded-full text-xl font-bold">
                  2
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Pick Your Time
              </h3>
              <p className="text-gray-600">
                Select from available time slots and see which team members are available.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center mb-4">
                <div className="flex items-center justify-center w-12 h-12 bg-primary-600 text-white rounded-full text-xl font-bold">
                  3
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Get Confirmed
              </h3>
              <p className="text-gray-600">
                Receive instant confirmation and calendar invite. You're all set!
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-24 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Book Your Meeting?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Join thousands of satisfied customers who trust BCal for their scheduling needs.
          </p>
          <Link
            to="/teams"
            className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-medium rounded-md text-primary-600 bg-white hover:bg-gray-50 transition-colors"
          >
            <CalendarIcon className="h-5 w-5 mr-2" />
            Start Booking Now
            <ArrowRightIcon className="h-5 w-5 ml-2" />
          </Link>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex items-center justify-center mb-4">
              <CalendarIcon className="h-8 w-8 text-primary-400 mr-3" />
              <span className="text-2xl font-bold">BCal</span>
            </div>
            <p className="text-gray-400">
              Professional team booking and scheduling platform
            </p>
            <div className="mt-6 flex justify-center space-x-6">
              <Link to="/teams" className="text-gray-400 hover:text-white">
                Book Meeting
              </Link>
              <Link to="/login" className="text-gray-400 hover:text-white">
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
