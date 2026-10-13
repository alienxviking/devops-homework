output "bucket_name" {
  description = "Name of the bucket"
  value       = aws_s3_bucket.demo.bucket
}

output "bucket_arn" {
  description = "ARN of the bucket"
  value       = aws_s3_bucket.demo.arn
}

output "bucket_region" {
  description = "Region of the bucket"
  value       = aws_s3_bucket.demo.region
}

output "versioning_status" {
  value = aws_s3_bucket_versioning.demo.versioning_configuration[0].status
}
