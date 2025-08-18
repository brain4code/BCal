import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import apiService from '../services/api.ts';
import toast from 'react-hot-toast';
import { CalendarIcon, ClockIcon, UserIcon, UsersIcon } from '@heroicons/react/24/outline';

interface Team {
  id: number;
  name: string;
  description: string;
  member_count: number;
}

interface AvailableSlot {
  user_id: number;
  user_name: string;
  user_email: string;
  start_time: string;
  end_time: string;
  meeting_type: string;
  meeting_description: string;
  meeting_location: string;
  slot_duration: number;
}

interface TeamAvailability {
  team_id: number;
  team_name: string;
  date: string;
  available_slots: AvailableSlot[];
}

const TeamBookingPage: React.FC = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const [team, setTeam] = useState<Team | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [availability, setAvailability] = useState<TeamAvailability | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<AvailableSlot | null>(null);
  const [loading, setLoading] = useState(true);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    guest_name: '',
    guest_email: ''
  });

  useEffect(() => {
    if (teamId) {
      loadTeamInfo();
    }
  }, [teamId]);

  useEffect(() => {
    if (selectedDate && teamId) {
      loadTeamAvailability();
    }
  }, [selectedDate, teamId]);

  const loadTeamInfo = async () => {
    try {
      const teams = await apiService.getAvailableTeams();
      const currentTeam = teams.teams.find((t: Team) => t.id === parseInt(teamId!));
      if (currentTeam) {
        setTeam(currentTeam);
      } else {
        toast.error('Team not found');
      }
    } catch (error) {
      toast.error('Failed to load team information');
    } finally {
      setLoading(false);
    }
  };

  const loadTeamAvailability = async () => {
    if (!selectedDate || !teamId) return;

    try {
      const dateStr = selectedDate.toISOString().split('T')[0];
      const availabilityData = await apiService.getTeamAvailability(parseInt(teamId), dateStr);
      setAvailability(availabilityData);
    } catch (error) {
      toast.error('Failed to load team availability');
    }
  };

  const handleDateChange = (date: Date | null) => {
    setSelectedDate(date);
    setSelectedSlot(null);
  };

  const handleSlotSelect = (slot: AvailableSlot) => {
    setSelectedSlot(slot);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedSlot || !team) {
      toast.error('Please select a time slot');
      return;
    }

    setBookingLoading(true);

    try {
      const startTime = new Date(selectedDate!);
      const [hours, minutes] = selectedSlot.start_time.split(':').map(Number);
      startTime.setHours(hours, minutes, 0, 0);

      const endTime = new Date(startTime);
      endTime.setMinutes(endTime.getMinutes() + selectedSlot.slot_duration);

      const bookingData = {
        title: formData.title,
        description: formData.description,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        guest_name: formData.guest_name,
        guest_email: formData.guest_email
      };

      const result = await apiService.bookWithTeam(parseInt(teamId!), bookingData);
      toast.success(result.message);
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        guest_name: '',
        guest_email: ''
      });
      setSelectedSlot(null);
      setSelectedDate(null);
      
      // Reload availability
      loadTeamAvailability();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create booking');
    } finally {
      setBookingLoading(false);
    }
  };

  const formatTime = (time: string) => {
    return time;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <div className="text-lg mt-4">Loading team information...</div>
        </div>
      </div>
    );
  }

  if (!team) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-lg text-red-600">Team not found</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0">
              <UsersIcon className="h-12 w-12 text-primary-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{team.name}</h1>
              <p className="text-gray-600 mt-1">{team.description}</p>
              <p className="text-sm text-gray-500 mt-1">
                {team.member_count} team member{team.member_count !== 1 ? 's' : ''} available
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Date Selection */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Date</h2>
            <DatePicker
              selected={selectedDate}
              onChange={handleDateChange}
              minDate={new Date()}
              maxDate={new Date(Date.now() + 90 * 24 * 60 * 60 * 1000)} // 90 days from now
              dateFormat="MMMM d, yyyy"
              placeholderText="Choose a date"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Available Slots */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Time Slots</h2>
            {selectedDate ? (
              availability && availability.available_slots.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {availability.available_slots.map((slot, index) => (
                    <div
                      key={index}
                      onClick={() => handleSlotSelect(slot)}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedSlot === slot
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <UserIcon className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="font-medium text-gray-900">{slot.user_name}</p>
                            <p className="text-sm text-gray-500">{slot.meeting_type}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-gray-900">
                            {formatTime(slot.start_time)} - {formatTime(slot.end_time)}
                          </p>
                          <p className="text-sm text-gray-500">{slot.slot_duration} min</p>
                        </div>
                      </div>
                      {slot.meeting_description && (
                        <p className="text-sm text-gray-600 mt-2">{slot.meeting_description}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <CalendarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No available slots for this date</p>
                </div>
              )
            ) : (
              <div className="text-center py-8">
                <CalendarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Please select a date to see available slots</p>
              </div>
            )}
          </div>
        </div>

        {/* Booking Form */}
        {selectedSlot && (
          <div className="bg-white shadow rounded-lg p-6 mt-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Book Your Meeting</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Meeting Title</label>
                  <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Enter meeting title"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Your Name</label>
                  <input
                    type="text"
                    required
                    value={formData.guest_name}
                    onChange={(e) => setFormData({ ...formData, guest_name: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Enter your full name"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Your Email</label>
                <input
                  type="email"
                  required
                  value={formData.guest_email}
                  onChange={(e) => setFormData({ ...formData, guest_email: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Enter your email address"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Meeting Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Describe what you'd like to discuss"
                />
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-900 mb-2">Booking Summary</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Date:</span>
                    <span className="ml-2 font-medium">{selectedDate?.toLocaleDateString()}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Time:</span>
                    <span className="ml-2 font-medium">
                      {formatTime(selectedSlot.start_time)} - {formatTime(selectedSlot.end_time)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Agent:</span>
                    <span className="ml-2 font-medium">{selectedSlot.user_name}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Duration:</span>
                    <span className="ml-2 font-medium">{selectedSlot.slot_duration} minutes</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={bookingLoading}
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  {bookingLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Booking...
                    </>
                  ) : (
                    'Confirm Booking'
                  )}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamBookingPage;
