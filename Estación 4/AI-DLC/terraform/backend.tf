# Terraform Backend Configuration
# State stored in S3 with DynamoDB lock for team collaboration

terraform {
  backend "s3" {
    bucket           = "ticketdesk-terraform-state"
    key              = "production/terraform.tfstate"
    region           = "us-south-1"
    encrypt          = true
    dynamodb_table   = "terraform-lock"
    skip_credentials_validation = false
  }
}

# NOTE: Before first apply, create S3 bucket and DynamoDB table:
#
# aws s3api create-bucket \
#   --bucket ticketdesk-terraform-state \
#   --region us-south-1 \
#   --create-bucket-configuration LocationConstraint=us-south-1
#
# aws s3api put-bucket-versioning \
#   --bucket ticketdesk-terraform-state \
#   --versioning-configuration Status=Enabled
#
# aws s3api put-bucket-encryption \
#   --bucket ticketdesk-terraform-state \
#   --server-side-encryption-configuration '{
#     "Rules": [{
#       "ApplyServerSideEncryptionByDefault": {
#         "SSEAlgorithm": "AES256"
#       }
#     }]
#   }'
#
# aws dynamodb create-table \
#   --table-name terraform-lock \
#   --attribute-definitions AttributeName=LockID,AttributeType=S \
#   --key-schema AttributeName=LockID,KeyType=HASH \
#   --billing-mode PAY_PER_REQUEST
