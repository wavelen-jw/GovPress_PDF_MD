export type JobStatus = "queued" | "processing" | "completed" | "failed";
export type HwpxTableMode = "text" | "html";

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

export type JobCreatePayload = Job & {
  edit_token: string;
};

export type ResultVariant = {
  markdown: string | null;
  html_preview: string | null;
};

export type ResultPayload = {
  job_id: string;
  status: JobStatus;
  markdown: string | null;
  html_preview: string | null;
  table_variants: {
    text: ResultVariant;
    html: ResultVariant;
  };
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

export type PolicyBriefingItem = {
  news_item_id: string;
  title: string;
  department: string;
  approve_date: string;
  original_url: string;
  file_name: string;
  file_url: string;
  has_appendix_hwpx: boolean;
};

export type PolicyBriefingListPayload = {
  date: string;
  items: PolicyBriefingItem[];
};

export type PolicyBriefingImportPayload = JobCreatePayload & {
  news_item_id: string;
  title: string;
  department: string;
  original_url: string;
};

export type UploadResult = {
  job: JobCreatePayload;
  resolvedBaseUrl: string;
};
