resource "random_id" "suffix" {
  byte_length = 3
}

resource "aws_s3_bucket" "assets" {
  bucket = "${local.name}-assets-${random_id.suffix.hex}"
  tags   = { Name = "${local.name}-assets" }
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket                  = aws_s3_bucket.assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
