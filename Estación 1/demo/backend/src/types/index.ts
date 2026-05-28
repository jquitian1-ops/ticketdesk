export interface Skill {
  skillId: string;
  skillName: string;
  likeCount: number;
}

export interface Participant {
  participantId: string;
  displayName: string;
  photoUrl: string;
  skills: Skill[];
  totalLikes: number;
  createdAt: string;
}

export interface ParticipantRecord {
  PK: string;
  SK: string;
  participantId: string;
  sessionCode: string;
  displayName: string;
  photoObjectKey: string;
  skills: Skill[];
  totalLikes: number;
  createdAt: string;
}

export interface SessionRecord {
  PK: string;
  SK: "METADATA";
  sessionCode: string;
  createdAt: string;
}

export interface VoteRecord {
  PK: string;
  SK: string;
}

export interface LeaderEntry {
  participantId: string;
  displayName: string;
  photoUrl: string;
  totalLikes: number;
}

export interface SkillEntry {
  skillId: string;
  skillName: string;
  totalLikes: number;
}

export interface UploadUrlResponse {
  uploadUrl: string;
  objectKey: string;
}

export interface JoinResponse {
  participantId: string;
  displayName: string;
  photoUrl: string;
  skills: Skill[];
}

export interface WallResponse {
  items: Participant[];
}

export interface LeaderboardResponse {
  topParticipants: LeaderEntry[];
  topSkills: SkillEntry[];
}

export interface LikeResponse {
  likeCount: number;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  dynamodb: "ok" | "error";
  timestamp: string;
}
