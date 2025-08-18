import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api.ts';
import toast from 'react-hot-toast';
import { UsersIcon, ArrowRightIcon, CalendarIcon } from '@heroicons/react/24/outline';

interface Team {
  id: number;
  name: string;
  description: string;
  member_count: number;
}

const TeamSelectionPage: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = useCallback(async () => {
    try {
      const response = await apiService.getAvailableTeams();
      setTeams(response.teams);
    } catch (error) {
      toast.error('Failed to load teams');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleTeamSelect = (teamId: number) => {
    navigate(`/team/${teamId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <div className="text-lg mt-4">Loading teams...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Book Your Meeting
          </h1>
          <p className="text-xl text-gray-600">
            Choose a team to schedule your appointment
          </p>
        </div>

        {/* Teams Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team) => (
            <div
              key={team.id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer"
              onClick={() => handleTeamSelect(team.id)}
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <UsersIcon className="h-8 w-8 text-primary-600" />
                    <h3 className="text-xl font-semibold text-gray-900">
                      {team.name}
                    </h3>
                  </div>
                  <ArrowRightIcon className="h-5 w-5 text-gray-400" />
                </div>
                
                <p className="text-gray-600 mb-4">
                  {team.description || 'Professional team ready to help you.'}
                </p>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <UsersIcon className="h-4 w-4" />
                    <span>{team.member_count} member{team.member_count !== 1 ? 's' : ''}</span>
                  </div>
                  
                  <div className="flex items-center space-x-2 text-sm text-primary-600 font-medium">
                    <CalendarIcon className="h-4 w-4" />
                    <span>Book Now</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {teams.length === 0 && (
          <div className="text-center py-12">
            <UsersIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Teams Available</h3>
            <p className="text-gray-500">
              There are currently no teams available for booking.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamSelectionPage;
