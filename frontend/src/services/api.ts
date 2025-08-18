import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  User, 
  UserCreate, 
  UserLogin, 
  Token, 
  Availability, 
  AvailabilityCreate, 
  AvailabilitySlot,
  Booking,
  BookingCreate,
  BookingWithDetails,
  DashboardStats
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor to handle errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  // Note: Registration is disabled - only admins can create users

  async login(credentials: UserLogin): Promise<Token> {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    const response: AxiosResponse<Token> = await this.api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response: AxiosResponse<User> = await this.api.get('/api/auth/me');
    return response.data;
  }

  // Availability
  async getUserAvailability(): Promise<Availability[]> {
    const response: AxiosResponse<Availability[]> = await this.api.get('/api/calendar/');
    return response.data;
  }

  async createAvailability(availability: AvailabilityCreate): Promise<Availability> {
    const response: AxiosResponse<Availability> = await this.api.post('/api/calendar/', availability);
    return response.data;
  }

  async updateAvailability(id: number, availability: Partial<AvailabilityCreate>): Promise<Availability> {
    const response: AxiosResponse<Availability> = await this.api.put(`/api/calendar/${id}`, availability);
    return response.data;
  }

  async deleteAvailability(id: number): Promise<void> {
    await this.api.delete(`/api/calendar/${id}`);
  }

  async getAvailableSlots(userId: number, date: string): Promise<AvailabilitySlot[]> {
    const response: AxiosResponse<AvailabilitySlot[]> = await this.api.get(`/api/calendar/slots/${userId}?date=${date}`);
    return response.data;
  }

  // Bookings
  async createBooking(booking: BookingCreate): Promise<Booking> {
    const response: AxiosResponse<Booking> = await this.api.post('/api/bookings/', booking);
    return response.data;
  }

  async getUserBookings(): Promise<BookingWithDetails[]> {
    const response: AxiosResponse<BookingWithDetails[]> = await this.api.get('/api/bookings/');
    return response.data;
  }

  async getBooking(id: number): Promise<BookingWithDetails> {
    const response: AxiosResponse<BookingWithDetails> = await this.api.get(`/api/bookings/${id}`);
    return response.data;
  }

  async updateBooking(id: number, booking: Partial<Booking>): Promise<Booking> {
    const response: AxiosResponse<Booking> = await this.api.put(`/api/bookings/${id}`, booking);
    return response.data;
  }

  async cancelBooking(id: number): Promise<void> {
    await this.api.delete(`/api/bookings/${id}`);
  }

  // Admin
  async getDashboardStats(): Promise<DashboardStats> {
    const response: AxiosResponse<DashboardStats> = await this.api.get('/api/admin/dashboard');
    return response.data;
  }

  async getAllUsers(params?: {
    search?: string;
    is_active?: boolean;
    role?: string;
  }): Promise<User[]> {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
    if (params?.role) queryParams.append('role', params.role);
    
    const url = `/api/admin/users${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response: AxiosResponse<User[]> = await this.api.get(url);
    return response.data;
  }

  async getAllBookings(params?: {
    search?: string;
    status?: string;
    host_id?: number;
    guest_id?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<BookingWithDetails[]> {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.host_id) queryParams.append('host_id', params.host_id.toString());
    if (params?.guest_id) queryParams.append('guest_id', params.guest_id.toString());
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    
    const url = `/api/admin/bookings${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response: AxiosResponse<BookingWithDetails[]> = await this.api.get(url);
    return response.data;
  }

  async updateBookingStatus(bookingId: number, updateData: {
    status?: string;
    title?: string;
    description?: string;
  }): Promise<BookingWithDetails> {
    const response: AxiosResponse<BookingWithDetails> = await this.api.put(`/api/admin/bookings/${bookingId}/status`, updateData);
    return response.data;
  }

  async deleteBooking(bookingId: number): Promise<void> {
    await this.api.delete(`/api/admin/bookings/${bookingId}`);
  }

  async toggleUserAdminStatus(userId: number): Promise<User> {
    const response: AxiosResponse<User> = await this.api.put(`/api/admin/users/${userId}/toggle-admin`);
    return response.data;
  }

  async toggleUserActiveStatus(userId: number): Promise<User> {
    const response: AxiosResponse<User> = await this.api.put(`/api/admin/users/${userId}/toggle-active`);
    return response.data;
  }

  async updateUserRole(userId: number, role: string): Promise<User> {
    const response: AxiosResponse<User> = await this.api.put(`/api/admin/users/${userId}/role`, { role });
    return response.data;
  }

  // Public Booking
  async getAvailableTeams(): Promise<any> {
    const response: AxiosResponse<any> = await this.api.get('/api/public/teams');
    return response.data;
  }

  async getTeamAvailability(teamId: number, date: string): Promise<any> {
    const response: AxiosResponse<any> = await this.api.get(`/api/public/teams/${teamId}/availability?date=${date}`);
    return response.data;
  }

  async bookWithTeam(teamId: number, bookingData: any): Promise<any> {
    const response: AxiosResponse<any> = await this.api.post(`/api/public/teams/${teamId}/book`, bookingData);
    return response.data;
  }

  // Team Management
  async getTeams(): Promise<any[]> {
    const response: AxiosResponse<any[]> = await this.api.get('/api/teams/');
    return response.data;
  }

  async createTeam(teamData: any): Promise<any> {
    const response: AxiosResponse<any> = await this.api.post('/api/teams/', teamData);
    return response.data;
  }

  async updateTeam(teamId: number, teamData: any): Promise<any> {
    const response: AxiosResponse<any> = await this.api.put(`/api/teams/${teamId}`, teamData);
    return response.data;
  }

  async deleteTeam(teamId: number): Promise<void> {
    await this.api.delete(`/api/teams/${teamId}`);
  }

  async getTeamMembers(teamId: number): Promise<any[]> {
    const response: AxiosResponse<any[]> = await this.api.get(`/api/teams/${teamId}/members`);
    return response.data;
  }

  async addTeamMember(teamId: number, memberData: any): Promise<any> {
    const response: AxiosResponse<any> = await this.api.post(`/api/teams/${teamId}/members`, memberData);
    return response.data;
  }

  async updateTeamMember(teamId: number, memberId: number, memberData: any): Promise<any> {
    const response: AxiosResponse<any> = await this.api.put(`/api/teams/${teamId}/members/${memberId}`, memberData);
    return response.data;
  }

  async removeTeamMember(teamId: number, memberId: number): Promise<void> {
    await this.api.delete(`/api/teams/${teamId}/members/${memberId}`);
  }
}

export const apiService = new ApiService();
export default apiService;
