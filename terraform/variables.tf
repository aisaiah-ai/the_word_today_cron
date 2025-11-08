variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for resources"
  type        = string
  default     = "us-central1"
}

variable "service_account_name" {
  description = "Name of the service account for GitHub Actions"
  type        = string
  default     = "github-actions-deploy"
}

variable "function_name" {
  description = "Cloud Function name"
  type        = string
  default     = "the-word-today-cron"
}

