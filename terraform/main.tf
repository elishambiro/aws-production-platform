# S3 Bucket for application assets
resource "aws_s3_bucket" "app_bucket" {
  bucket = "${var.app_name}-${var.environment}-assets"

  tags = {
    Name        = "${var.app_name}-assets"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "app_bucket_versioning" {
  bucket = aws_s3_bucket.app_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# DynamoDB table for application data
resource "aws_dynamodb_table" "app_table" {
  name         = "${var.app_name}-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "timestamp"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Name        = "${var.app_name}-table"
    Environment = var.environment
  }
}

# SQS Queue for async message processing
resource "aws_sqs_queue" "app_queue" {
  name                       = "${var.app_name}-${var.environment}-queue"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = 86400
  visibility_timeout_seconds = 30

  tags = {
    Name        = "${var.app_name}-queue"
    Environment = var.environment
  }
}

# IAM Role for application
resource "aws_iam_role" "app_role" {
  name = "${var.app_name}-${var.environment}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "app_policy" {
  name = "${var.app_name}-policy"
  role = aws_iam_role.app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:DeleteItem",
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      }
    ]
  })
}
