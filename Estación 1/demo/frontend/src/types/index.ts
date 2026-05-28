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
