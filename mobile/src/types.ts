export type JobStatus = "queued" | "processing" | "completed" | "failed";

export type Job = {
  job_id: string;
  status: JobStatus;
  file_name: string;
  created_at: string;
  updated_at?: string | null;
  progress?: number;
  error_code?: string | null;
  error_message?: string | null;
};

export type ResultPayload = {
  job_id: string;
  status: JobStatus;
  markdown: string | null;
  html_preview: string | null;
  meta: {
    title: string | null;
    department: string | null;
    source_file_name: string;
  };
};

export type AppConfig = {
  baseUrl: string;
  apiKey: string;
};

export type CleanupPayload = {
  deleted_count: number;
};
