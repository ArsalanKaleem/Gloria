export type Role = 'user' | 'assistant';

export interface Source {
  title: string;
  page?: number | null;
  source_type?: string;
  source_url?: string | null;
  organization?: string | null;
}

export interface Message {
  id: string;
  role: Role;
  text: string;
  sources?: Source[];
  createdAt: number;
}
