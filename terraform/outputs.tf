output "service_account_email" {
  description = "Email of the service account for GitHub Actions"
  value       = google_service_account.github_actions.email
}

output "service_account_id" {
  description = "ID of the service account"
  value       = google_service_account.github_actions.id
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL for Cloud Function images"
  value       = google_artifact_registry_repository.function_images.name
}

output "enabled_apis" {
  description = "List of enabled APIs"
  value       = keys(google_project_service.required_apis)
}

output "next_steps" {
  description = "Next steps after applying Terraform"
  value = <<-EOT
    ✅ Terraform setup complete!
    
    Next steps:
    1. Create a service account key:
       gcloud iam service-accounts keys create gcp-sa-key.json \
         --iam-account=${google_service_account.github_actions.email}
    
    2. Add the following secrets to GitHub:
       - GCP_SA_KEY: Contents of gcp-sa-key.json
       - GCP_PROJECT_ID: ${var.project_id}
       - YOUTUBE_API_KEY: Your YouTube API key
       - FIREBASE_CREDENTIALS_JSON: Your Firebase credentials JSON
       - DRY_RUN: False (or True for testing)
    
    3. Push to main branch to trigger deployment!
  EOT
}

