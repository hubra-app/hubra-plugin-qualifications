import { apiFetch } from '@hubra/plugin-sdk'

export type QualificationState = 'valid' | 'soon' | 'expired'

// ── Qualifications ──────────────────────────────────────────────────────────

export interface QualificationKind {
  id: number
  name: string
  description: string | null
  validMonths: number | null
  remindDays: number
  /** Members add it to themselves ("Elektriker"); everyone sees who has it. */
  selfService: boolean
}

export interface Qualification {
  id: number
  memberId: number
  memberName: string | null
  kindId: number
  kindName: string
  selfService: boolean
  obtainedOn: string
  expiresOn: string | null
  note: string | null
  state: QualificationState
  /** Self-service: the member who vouched for it. */
  confirmedBy: string | null
  confirmedById: number | null
  confirmedAt: string | null
}

export interface KindInput {
  name: string
  description: string | null
  validMonths: number | null
  remindDays: number
  selfService: boolean
}

export interface QualificationInput {
  memberId?: number
  kindId?: number
  obtainedOn: string
  expiresOn?: string | null
  note: string | null
}

const Q = '/qualifications'
export const listKinds = () => apiFetch<QualificationKind[]>(`${Q}/kinds`)
export const createKind = (input: KindInput) =>
  apiFetch<QualificationKind>(`${Q}/kinds`, { method: 'POST', body: JSON.stringify(input) })
export const updateKind = (id: number, input: KindInput) =>
  apiFetch<QualificationKind>(`${Q}/kinds/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteKind = (id: number) => apiFetch<void>(`${Q}/kinds/${id}`, { method: 'DELETE' })
export const listQualifications = () => apiFetch<Qualification[]>(Q)
export const myQualifications = () => apiFetch<Qualification[]>(`${Q}/mine`)
export const addQualification = (input: QualificationInput) =>
  apiFetch<Qualification>(Q, { method: 'POST', body: JSON.stringify(input) })
export const updateQualification = (id: number, input: QualificationInput) =>
  apiFetch<Qualification>(`${Q}/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteQualification = (id: number) => apiFetch<void>(`${Q}/${id}`, { method: 'DELETE' })

// ── What members can do (self-service qualifications) ──────────────────────

export interface CanDo {
  id: number
  memberId: number
  memberName: string | null
  kindId: number
  kindName: string
  note: string | null
  mine: boolean
  confirmedBy: string | null
  confirmedById: number | null
  confirmedAt: string | null
}

export const listCanDo = (q: string) => apiFetch<CanDo[]>(`${Q}/directory?${new URLSearchParams({ q })}`)
export const addMine = (input: { kindId?: number; name?: string; note: string | null }) =>
  apiFetch<Qualification>(`${Q}/mine`, { method: 'POST', body: JSON.stringify(input) })
export const updateMine = (id: number, note: string | null) =>
  apiFetch<Qualification>(`${Q}/mine/${id}`, { method: 'PATCH', body: JSON.stringify({ note }) })
export const deleteMine = (id: number) => apiFetch<void>(`${Q}/mine/${id}`, { method: 'DELETE' })
export const confirmCanDo = (id: number) => apiFetch<Qualification>(`${Q}/${id}/confirm`, { method: 'POST' })
export const unconfirmCanDo = (id: number) => apiFetch<Qualification>(`${Q}/${id}/confirm`, { method: 'DELETE' })
