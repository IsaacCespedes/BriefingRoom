export type Role = "host" | "candidate";

export interface TokenInfo {
  role: Role;
  interview_id: string;
}

export interface Interview {
  id: string;
  created_at: string;
  job_description: string | null;
  resume_text: string | null;
  status: string;
  job_description_source?: string;
  resume_source?: string;
  job_description_metadata?: any;
  resume_metadata?: any;
  job_description_path?: string | null;
  resume_path?: string | null;
}

export interface InterviewNote {
  id: string;
  interview_id: string;
  created_at: string;
  note: string;
  source: string;
}
