terraform {
  required_version = ">= 1.0"
  
  required_providers {
    # The Trello provider has been removed from the registry
    # We'll need to use a different approach
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Get Trello credentials from Parameter Store
# If you only have one credential, we'll need both API key and token
# Get API Key from: https://trello.com/app-key
# Get Token from the "Token" link on that same page

data "aws_ssm_parameter" "trello_credentials" {
  name = "/global/curriculum-designer/trello-credentials"
}

locals {
  # Parse credentials from JSON string
  # Store as: {"api_key": "xxx", "token": "yyy"}
  trello_creds = jsondecode(data.aws_ssm_parameter.trello_credentials.value)
}

provider "trello" {
  api_key = local.trello_creds.api_key
  token   = local.trello_creds.token
}

provider "aws" {
  region = "us-east-1"
}

# ============================================
# DEMO BOARD - Fully Terraform Managed
# ============================================

resource "trello_board" "curriculum_demo" {
  name        = "Curriculum Designer - DEMO (Terraform Managed)"
  description = "Fully automated curriculum board showcasing Terraform capabilities"
  
  # Board settings
  permission_level     = "private"
  voting_permission    = "members"
  comment_permission   = "members"
  invitation_permission = "members"
  
  # Enable features
  enable_self_join     = false
  enable_card_covers   = true
  
  # Background color
  background_color     = "blue"
}

# ============================================
# LISTS - Workflow Columns
# ============================================

locals {
  lists = {
    "backlog" = {
      name = "📚 Activity Backlog"
      position = 1
    }
    "ready" = {
      name = "✅ Ready to Use"
      position = 2
    }
    "this_week" = {
      name = "📅 This Week's Lessons"
      position = 3
    }
    "in_progress" = {
      name = "🎯 Currently Teaching"
      position = 4
    }
    "completed" = {
      name = "✨ Completed Today"
      position = 5
    }
    "needs_revision" = {
      name = "🔧 Needs Revision"
      position = 6
    }
    "archive" = {
      name = "🗄️ Archive"
      position = 7
    }
  }
}

resource "trello_list" "lists" {
  for_each = local.lists
  
  board_id = trello_board.curriculum_demo.id
  name     = each.value.name
  position = each.value.position
}

# ============================================
# LABELS - Categories & Metadata
# ============================================

# Difficulty Levels
resource "trello_label" "beginner" {
  board_id = trello_board.curriculum_demo.id
  name     = "Beginner"
  color    = "green"
}

resource "trello_label" "intermediate" {
  board_id = trello_board.curriculum_demo.id
  name     = "Intermediate"
  color    = "yellow"
}

resource "trello_label" "advanced" {
  board_id = trello_board.curriculum_demo.id
  name     = "Advanced"
  color    = "red"
}

# Activity Types
resource "trello_label" "grammar" {
  board_id = trello_board.curriculum_demo.id
  name     = "Grammar"
  color    = "purple"
}

resource "trello_label" "speaking" {
  board_id = trello_board.curriculum_demo.id
  name     = "Speaking"
  color    = "blue"
}

resource "trello_label" "writing" {
  board_id = trello_board.curriculum_demo.id
  name     = "Writing"
  color    = "sky"
}

resource "trello_label" "business" {
  board_id = trello_board.curriculum_demo.id
  name     = "Business English"
  color    = "black"
}

# Special Tags
resource "trello_label" "warmup" {
  board_id = trello_board.curriculum_demo.id
  name     = "Warmup Activity"
  color    = "lime"
}

resource "trello_label" "homework" {
  board_id = trello_board.curriculum_demo.id
  name     = "Homework"
  color    = "pink"
}

resource "trello_label" "tested" {
  board_id = trello_board.curriculum_demo.id
  name     = "✓ Tested & Proven"
  color    = "orange"
}

# ============================================
# SAMPLE ACTIVITY CARDS
# ============================================

# Grammar Activity Card
resource "trello_card" "present_perfect" {
  list_id = trello_list.lists["ready"].id
  name    = "[25m] Present Perfect Practice | Grammar"
  
  description = <<-EOT
LEVEL: Intermediate
DURATION: 25
ENERGY: Medium
INTERACTION: Individual then Pairs
SKILLS: Grammar, Speaking
PROFESSION: General

OBJECTIVES:
- Distinguish present perfect from past simple
- Practice for/since time expressions
- Use present perfect in conversation

MATERIALS:
- Timeline visual aid
- Experience cards (PDF in Drive)
- Worksheet #PP-01

INSTRUCTIONS:
1. Warm-up (3 min): "Two truths and a lie" using present perfect
2. Review (5 min): Timeline demonstration - past simple vs present perfect
3. Controlled practice (7 min): Worksheet completion individually
4. Speaking practice (8 min): Interview partner about experiences
5. Wrap-up (2 min): Common errors discussion

VARIATIONS:
Beginner: Focus only on "have you ever..."
Advanced: Add present perfect continuous
Online: Use Jamboard for timeline drawing

NOTES:
Students often confuse with past simple
Emphasize connection to present
Works well before "Life experiences" speaking activity
  EOT
  
  position = 1
  
  label_ids = [
    trello_label.intermediate.id,
    trello_label.grammar.id,
    trello_label.tested.id
  ]
}

# Speaking Activity Card
resource "trello_card" "business_negotiations" {
  list_id = trello_list.lists["ready"].id
  name    = "[30m] Business Negotiation Roleplay | Speaking"
  
  description = <<-EOT
LEVEL: Upper-Intermediate
DURATION: 30
ENERGY: High
INTERACTION: Pairs
SKILLS: Speaking, Listening, Business Vocabulary
PROFESSION: Business, Sales, Management

OBJECTIVES:
- Practice negotiation phrases and tactics
- Build confidence in disagreeing politely
- Learn to make and respond to proposals

MATERIALS:
- Scenario cards (6 different business situations)
- Negotiation phrases handout
- Success criteria checklist

INSTRUCTIONS:
1. Warm-up (3 min): Brainstorm negotiation situations
2. Language input (5 min): Key phrases for proposals/counteroffers
3. Demo (4 min): Teacher models with strong student
4. Round 1 (8 min): Simple price negotiation
5. Round 2 (8 min): Complex contract terms
6. Debrief (2 min): Successful strategies sharing

VARIATIONS:
Large group: Fishbowl with observers taking notes
Advanced: Add cultural complications
Online: Breakout rooms with scenario in chat

NOTES:
Pre-teach "tentative language" 
Monitor for L1 interference
Great follow-up to "Making suggestions" lesson
Energy drops if longer than 30 min
  EOT
  
  position = 2
  
  label_ids = [
    trello_label.intermediate.id,
    trello_label.speaking.id,
    trello_label.business.id,
    trello_label.tested.id
  ]
}

# Warmup Activity Card
resource "trello_card" "two_minute_topics" {
  list_id = trello_list.lists["ready"].id
  name    = "[10m] Two-Minute Topics | Warmup"
  
  description = <<-EOT
LEVEL: All Levels
DURATION: 10
ENERGY: Medium to High
INTERACTION: Pairs
SKILLS: Speaking, Listening
PROFESSION: General

OBJECTIVES:
- Activate English-speaking mode
- Build fluency through time pressure
- Practice active listening

MATERIALS:
- Topic cards (or app: randomtopicgenerator.com)
- Timer

INSTRUCTIONS:
1. Pair students (1 min)
2. Student A talks for 2 min on random topic
3. Student B asks 2 follow-up questions (1 min)
4. Switch roles (3 min)
5. Share interesting facts with class (3 min)

VARIATIONS:
Beginner: Provide sentence starters
Advanced: Add "must use" vocabulary
Shy students: Allow 1 min prep time

NOTES:
Perfect Monday morning warmup
Adjust topics to match lesson theme
Keep energy high with music between rounds
  EOT
  
  position = 3
  
  label_ids = [
    trello_label.warmup.id,
    trello_label.speaking.id,
    trello_label.tested.id
  ]
}

# Writing Activity Card  
resource "trello_card" "email_writing" {
  list_id = trello_list.lists["this_week"].id
  name    = "[20m] Professional Email Writing | Writing"
  
  description = <<-EOT
LEVEL: Intermediate
DURATION: 20
ENERGY: Low
INTERACTION: Individual
SKILLS: Writing, Business Communication
PROFESSION: All Professional

OBJECTIVES:
- Structure formal emails appropriately
- Use correct opening/closing phrases
- Maintain appropriate tone

MATERIALS:
- Email template handout
- Sample emails (good and bad)
- Scenario prompts

INSTRUCTIONS:
1. Analyze (5 min): Compare formal vs informal email samples
2. Identify (3 min): Key components of professional emails
3. Practice (10 min): Write email based on scenario
4. Peer review (2 min): Quick check with partner

VARIATIONS:
Advanced: Add diplomatic language for complaints
Homework: Extend to full email exchange
Group work: Collaborative email writing

NOTES:
Common errors: too direct, wrong register
Emphasize subject lines
Can lead into phone call practice
  EOT
  
  position = 1
  
  label_ids = [
    trello_label.intermediate.id,
    trello_label.writing.id,
    trello_label.business.id
  ]
}

# Card in "needs revision" 
resource "trello_card" "pronunciation_drills" {
  list_id = trello_list.lists["needs_revision"].id
  name    = "[15m] Minimal Pairs Pronunciation | Speaking"
  
  description = <<-EOT
LEVEL: Beginner to Intermediate
DURATION: 15
ENERGY: Low
INTERACTION: Whole Class then Pairs
SKILLS: Pronunciation, Listening
PROFESSION: General

OBJECTIVES:
- Distinguish between similar sounds
- Improve pronunciation accuracy
- Build awareness of common errors

MATERIALS:
- Minimal pairs list
- Audio recordings (optional)

INSTRUCTIONS:
[NEEDS UPDATING - Students found this boring]
1. Teacher models pairs
2. Class repetition
3. Student practice
4. [MORE ENGAGING ACTIVITY NEEDED]

VARIATIONS:
[TO BE DEVELOPED]

NOTES:
Students found this too repetitive
Need to gamify somehow
Consider replacing with pronunciation app work
  EOT
  
  position = 1
  
  label_ids = [
    trello_label.beginner.id,
    trello_label.speaking.id
  ]
}

# ============================================
# CHECKLISTS - Reusable Templates
# ============================================

resource "trello_checklist" "lesson_prep" {
  card_id = trello_card.business_negotiations.id
  name    = "Pre-Lesson Checklist"
  
  items = [
    "Print scenario cards",
    "Test projector/screen share",
    "Prepare whiteboard markers",
    "Queue up timer",
    "Review key vocabulary",
    "Prepare backup activity"
  ]
}

resource "trello_checklist" "materials" {
  card_id = trello_card.present_perfect.id
  name    = "Materials Needed"
  
  items = [
    "Timeline visual (printed)",
    "Experience cards (Google Drive)",
    "Worksheet PP-01 (20 copies)",
    "Board markers (3 colors)"
  ]
}

# ============================================
# WEBHOOKS - Automation Triggers
# ============================================

resource "trello_webhook" "card_moved" {
  description  = "Track when activities move to 'This Week'"
  callback_url = "https://your-api.com/webhooks/trello/card-moved"
  id_model     = trello_board.curriculum_demo.id
}

# ============================================
# BOARD MEMBERS (if managing team)
# ============================================

# resource "trello_board_member" "assistant_teacher" {
#   board_id    = trello_board.curriculum_demo.id
#   member_id   = "trello_user_id_here"
#   member_type = "normal"
# }

# ============================================
# OUTPUTS - Useful Information
# ============================================

output "board_url" {
  value       = "https://trello.com/b/${trello_board.curriculum_demo.id}"
  description = "URL to access the demo board"
}

output "board_id" {
  value       = trello_board.curriculum_demo.id
  description = "Board ID for API access"
}

output "list_ids" {
  value = {
    for key, list in trello_list.lists : key => list.id
  }
  description = "List IDs for API automation"
}

output "webhook_info" {
  value = {
    webhook_id = trello_webhook.card_moved.id
    callback   = trello_webhook.card_moved.callback_url
  }
  description = "Webhook configuration"
  sensitive   = true
}

# ============================================
# DOCUMENTATION
# ============================================

output "demo_features" {
  value = <<-EOT
    This Terraform-managed board demonstrates:
    
    ✅ Board Creation & Configuration
    ✅ Lists (Workflow Columns)
    ✅ Labels (Categories/Levels)
    ✅ Cards with Structured Descriptions
    ✅ Checklists for Reusable Tasks
    ✅ Webhooks for Automation
    
    What Terraform CAN'T do:
    ❌ Custom Fields (Power-Up)
    ❌ Butler Automation Rules
    ❌ Card Attachments/Images
    ❌ Card Comments
    ❌ Due Dates (via API only)
    
    Best Practice:
    - Use TF for initial setup
    - Use API/UI for daily operations
    - Use webhooks for automation
  EOT
  description = "What this demo showcases"
}