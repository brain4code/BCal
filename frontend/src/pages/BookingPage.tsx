import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import apiService from '../services/api.ts';
import { AvailabilitySlot, User, BookingCreate } from '../types/index.ts';
import toast from 'react-hot-toast';
import { CalendarIcon, ClockIcon, UserIcon } from '@heroicons/react/24/outline';

const BookingPage: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const [host, setHost] = useState<User | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [availableSlots, setAvailableSlots] = useState<AvailabilitySlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null);
  const [loading, setLoading] = useState(true);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    guest_name: '',
    guest_email: ''
  });

  useEffect(() => {
    if (userId) {
      loadHostInfo();
    }
  }, [userId]);

  useEffect(() => {
    if (selectedDate && userId) {
      loadAvailableSlots();
    }
  }, [selectedDate, userId]);

  const loadHostInfo = async () => {
    try {
      // For now, we'll use a mock user since we don't have a public user endpoint
      // In a real app, you'd have a public endpoint to get user info
      setHost({
        id: parseInt(userId!),
        email: 'host@example.com',
        username: 'host',
        full_name: 'John Doe',
        timezone: 'UTC',
        bio: 'Available for meetings and consultations',
        is_active: true,
        is_admin: false,
        created_at: new Date().toISOString(),
      });
    } catch (error) {
      toast.error('Failed to load host information');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableSlots = async () => {
    if (!selectedDate || !userId) return;

    try {
      const dateStr = selectedDate.toISOString().split('T')[0];
      const slots = await apiService.getAvailableSlots(parseInt(userId), dateStr);
      setAvailableSlots(slots);
    } catch (error) {
      toast.error('Failed to load available slots');
    }
  };

  const handleDateChange = (date: Date | null) => {
    setSelectedDate(date);
    setSelectedSlot(null);
  };

  const handleSlotSelect = (slot: AvailabilitySlot) => {
    if (slot.is_available) {
      setSelectedSlot(slot);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedSlot || !host) {
      toast.error('Please select a time slot');
      return;
    }

    setBookingLoading(true);

    try {
      const startTime = new Date(selectedDate!);
      const [hours, minutes] = selectedSlot.start_time.split(':').map(Number);
      startTime.setHours(hours, minutes, 0, 0);

      const endTime = new Date(startTime);
      endTime.setMinutes(endTime.getMinutes() + 30);

      const booking: BookingCreate = {
        host_id: host.id,
        title: formData.title,
        description: formData.description,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        guest_name: formData.guest_name,
        guest_email: formData.guest_email
      };

      await apiService.createBooking(booking);
      toast.success('Booking created successfully!');
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        guest_name: '',
        guest_email: ''
      });
      setSelectedSlot(null);
      setSelectedDate(null);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create booking');
    } finally {
      setBookingLoading(false);
    }
  };

  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!host) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-red-600">Host not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0">
              <UserIcon className="h-12 w-12 text-primary-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Book with {host.full_name}</h1>
              <p className="text-gray-600">{host.bio}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Date and Time Selection */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Select Date & Time</h2>
            
            {/* Date Picker */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Date
              </label>
              <DatePicker
                selected={selectedDate}
                onChange={handleDateChange}
                minDate={new Date()}
                dateFormat="MMMM d, yyyy"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                placeholderText="Select a date"
              />
            </div>

            {/* Time Slots */}
            {selectedDate && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Available Times for {selectedDate.toLocaleDateString()}
                </label>
                <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
                  {availableSlots.length === 0 ? (
                    <p className="text-sm text-gray-500 col-span-2">No available slots for this date</p>
                  ) : (
                    availableSlots.map((slot, index) => (
                      <button
                        key={index}
                        onClick={() => handleSlotSelect(slot)}
                        disabled={!slot.is_available}
                        className={`p-3 text-sm rounded-md border ${
                          selectedSlot === slot
                            ? 'bg-primary-100 border-primary-500 text-primary-700'
                            : slot.is_available
                            ? 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                            : 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        {formatTime(slot.start_time)} - {formatTime(slot.end_time)}
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Booking Form */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Booking Details</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Meeting Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Brief description of the meeting"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Description (Optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Additional details about the meeting"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Your Name
                </label>
                <input
                  type="text"
                  value={formData.guest_name}
                  onChange={(e) => setFormData({ ...formData, guest_name: e.target.value })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Enter your full name"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Your Email
                </label>
                <input
                  type="email"
                  value={formData.guest_email}
                  onChange={(e) => setFormData({ ...formData, guest_email: e.target.value })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Enter your email address"
                  required
                />
              </div>

              {selectedSlot && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <h3 className="text-sm font-medium text-blue-900">Selected Time</h3>
                  <p className="text-sm text-blue-700 mt-1">
                    {selectedDate?.toLocaleDateString()} at {formatTime(selectedSlot.start_time)} - {formatTime(selectedSlot.end_time)}
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={!selectedSlot || bookingLoading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {bookingLoading ? 'Creating Booking...' : 'Book Appointment'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookingPage;
