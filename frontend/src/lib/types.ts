export type Role = 'host' | 'candidate';

export interface TokenInfo {
	role: Role;
	interview_id: string;
}

export interface Interview {
	id: string;
	created_at: string;
	job_description: string;
	resume_text: string;
	status: string;
}

export interface InterviewNote {
	id: string;
	interview_id: string;
	created_at: string;
	note: string;
	source: string;
}

