import request from './request'
import type { LoginRequest, TokenResponse, UserCreate, UserResponse } from '@/types/api'

export function register(data: UserCreate): Promise<TokenResponse> {
  return request.post('/auth/register', data)
}

export function login(data: LoginRequest): Promise<TokenResponse> {
  return request.post('/auth/login', data)
}

export function getMe(): Promise<UserResponse> {
  return request.get('/auth/me')
}
