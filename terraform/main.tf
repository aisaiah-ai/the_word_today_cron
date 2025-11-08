terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
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

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudfunctions.googleapis.com",      # Cloud Functions API
    "run.googleapis.com",                 # Cloud Run API (required for Gen2)
    "cloudbuild.googleapis.com",          # Cloud Build API
    "cloudscheduler.googleapis.com",      # Cloud Scheduler API
    "logging.googleapis.com",              # Cloud Logging API
    "artifactregistry.googleapis.com",    # Artifact Registry (for function images)
    "secretmanager.googleapis.com",       # Secret Manager (optional, for credentials)
    "iam.googleapis.com",                 # IAM API
    "serviceusage.googleapis.com",        # Service Usage API
  ])

  project = var.project_id
  service  = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Create service account for GitHub Actions
resource "google_service_account" "github_actions" {
  project      = var.project_id
  account_id   = var.service_account_name
  display_name = "GitHub Actions Deployment Account"
  description  = "Service account used by GitHub Actions for deploying Cloud Functions"
}

# Grant IAM roles to service account
resource "google_project_iam_member" "cloudfunctions_developer" {
  project = var.project_id
  role    = "roles/cloudfunctions.developer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "cloudscheduler_admin" {
  project = var.project_id
  role    = "roles/cloudscheduler.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "iam_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "artifactregistry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "service_usage_consumer" {
  project = var.project_id
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Create Artifact Registry repository for Cloud Function images
resource "google_artifact_registry_repository" "function_images" {
  project       = var.project_id
  location      = var.region
  repository_id = "cloud-functions"
  description   = "Repository for Cloud Function container images"
  format        = "DOCKER"
}

# Outputs
output "service_account_email" {
  description = "Email of the service account"
  value       = google_service_account.github_actions.email
}

output "service_account_id" {
  description = "ID of the service account"
  value       = google_service_account.github_actions.id
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = google_artifact_registry_repository.function_images.name
}

output "enabled_apis" {
  description = "List of enabled APIs"
  value       = keys(google_project_service.required_apis)
}

