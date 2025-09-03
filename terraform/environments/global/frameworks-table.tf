resource "aws_dynamodb_table" "curriculum_frameworks" {
  name           = "curriculum-frameworks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "framework_id"

  attribute {
    name = "framework_id"
    type = "S"
  }

  attribute {
    name = "board_id"
    type = "S"
  }

  # Global Secondary Index for querying by board_id
  global_secondary_index {
    name            = "board-index"
    hash_key        = "board_id"
    projection_type = "ALL"
  }

  tags = {
    Name        = "Curriculum Frameworks"
    Environment = "production"
    Purpose     = "Store course frameworks for variant generation"
  }
}

output "frameworks_table_name" {
  value = aws_dynamodb_table.curriculum_frameworks.name
}

output "frameworks_table_arn" {
  value = aws_dynamodb_table.curriculum_frameworks.arn
}