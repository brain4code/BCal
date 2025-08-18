export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  timezone: string;
  bio?: string;
  is_active: boolean;
  role: string;  // visitor, user, admin
  created_at: string;
  updated_at?: string;
}

export interface UserCreate {
  email: string;
  username: string;
  full_name: string;
  password: string;
  timezone?: string;
  bio?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Availability {
  id: number;
  user_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AvailabilityCreate {
  day_of_week: number;
  start_time: string;
  end_time: string;
}

export interface AvailabilitySlot {
  date: string;
  start_time: string;
  end_time: string;
  is_available: boolean;
}

export interface Booking {
  id: number;
  host_id: number;
  guest_id: number;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  status: BookingStatus;
  guest_email: string;
  guest_name: string;
  created_at: string;
  updated_at?: string;
}

export interface BookingCreate {
  host_id: number;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  guest_email: string;
  guest_name: string;
}

export interface BookingWithDetails extends Booking {
  host: {
    id: number;
    full_name: string;
    email: string;
  };
  guest: {
    id: number;
    full_name: string;
    email: string;
  };
}

export enum BookingStatus {
  PENDING = "pending",
  CONFIRMED = "confirmed",
  CANCELLED = "cancelled",
  COMPLETED = "completed",
}

export interface DashboardStats {
  total_bookings: number;
  pending_bookings: number;
  confirmed_bookings: number;
  cancelled_bookings: number;
  completed_bookings: number;
  total_users: number;
  active_users: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}
