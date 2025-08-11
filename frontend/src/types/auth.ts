export interface User {
  id: number
  username: string
  email: string
  full_name: string
  avatar_url?: string
  bio?: string
  company?: string
  department?: string
  position?: string
  role: 'admin' | 'manager' | 'analyst' | 'viewer'
  status: 'active' | 'inactive' | 'suspended' | 'deleted'
  is_email_verified: boolean
  created_at: string
  updated_at: string
  last_login_at?: string
  email_verified_at?: string
}

export interface LoginCredentials {
  username_or_email: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  full_name: string
  password: string
  confirm_password: string
  avatar_url?: string
  bio?: string
  company?: string
  department?: string
  position?: string
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface Team {
  id: number
  name: string
  description?: string
  is_public: boolean
  max_members: number
  owner_id: number
  created_at: string
  updated_at: string
  owner: User
  members: User[]
  member_count?: number
}

export interface TeamCreate {
  name: string
  description?: string
  is_public?: boolean
  max_members?: number
}

export interface TeamUpdate {
  name?: string
  description?: string
  is_public?: boolean
  max_members?: number
}

export interface UserSearchParams {
  q?: string
  role?: string
  status?: string
  company?: string
  department?: string
}

export interface UserStatistics {
  total_users: number
  active_users: number
  new_users_today: number
  new_users_this_week: number
  new_users_this_month: number
  user_distribution: {
    by_role: Record<string, number>
    by_status: Record<string, number>
  }
}