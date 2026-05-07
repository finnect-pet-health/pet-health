import { api } from './client';
import { Family } from '../auth/store';

export interface FamilyDetail {
  id: string;
  name: string;
}

export interface FamilyMember {
  user_id: string;
  name: string;
  role: 'owner' | 'member';
  joined_at: string;
}

export interface CreateFamilyResponse {
  family: FamilyDetail;
  member: { role: 'owner' };
}

export interface InviteResponse {
  invite_code: string;
  expires_at: string;
}

export interface JoinResponse {
  family: FamilyDetail;
  role: 'member';
}

export const families = {
  /** GET /v1/families — 내 가족 목록 */
  list(): Promise<Family[]> {
    return api.get<Family[]>('/families').then((r) => r.data);
  },

  /** POST /v1/families — 가족 생성 (본인이 owner로 자동 가입) */
  create(name: string): Promise<CreateFamilyResponse> {
    return api.post<CreateFamilyResponse>('/families', { name }).then((r) => r.data);
  },

  /** POST /v1/families/{id}/invite — 초대 코드 발급 (owner 전용) */
  invite(familyId: string, ttlHours?: number): Promise<InviteResponse> {
    const body: { ttl_hours?: number } = {};
    if (ttlHours !== undefined) body.ttl_hours = ttlHours;
    return api
      .post<InviteResponse>(`/families/${familyId}/invite`, body)
      .then((r) => r.data);
  },

  /** POST /v1/families/join — 초대 코드로 가족 참여 */
  join(inviteCode: string): Promise<JoinResponse> {
    return api
      .post<JoinResponse>('/families/join', { invite_code: inviteCode })
      .then((r) => r.data);
  },

  /** GET /v1/families/{id}/members — 가족 멤버 목록 (member 이상) */
  members(familyId: string): Promise<FamilyMember[]> {
    return api
      .get<FamilyMember[]>(`/families/${familyId}/members`)
      .then((r) => r.data);
  },
};
