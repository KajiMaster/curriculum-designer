# Trello Board Design for AI-Powered Curriculum

## Board Structure: "English Curriculum AI Assistant"

### Lists (Workflow Columns):
```
📚 Activity Bank          - All available activities
🤖 AI Requests            - Cards requesting AI help  
📋 AI Suggestions         - AI-generated recommendations
📅 This Week             - Scheduled for this week
⏰ Today                 - Today's lesson activities
✅ Completed             - Finished activities  
🔄 Needs Revision        - Activities to improve
🗂️ Templates             - Reusable lesson structures
```

### Labels (Color-Coded Categories):
```
🟢 Beginner             - Green
🟡 Intermediate          - Yellow  
🔴 Advanced             - Red
🔵 Grammar              - Blue
🟣 Speaking             - Purple
⚫ Writing              - Black
🟠 Business English      - Orange
🔵 Listening            - Light Blue
🟢 Warmup               - Lime
🔴 Assessment           - Pink
```

## Card Naming Convention:

### Activity Cards:
```
Format: [Duration] Activity Name | Level | Type
Examples:
- [20m] Present Perfect Practice | Intermediate | Grammar
- [30m] Business Meeting Roleplay | Advanced | Speaking
- [15m] Email Writing | Intermediate | Business
- [10m] Pronunciation Warm-up | Beginner | Warmup
```

### AI Command Cards:
```
Format: 🤖 AI: [Command] - [Details]
Examples:
- 🤖 AI: Build Lesson - Tuesday 2pm, Maria, Intermediate, Business Focus
- 🤖 AI: Find Alternative - Similar to Negotiation Roleplay but shorter
- 🤖 AI: Analyze Usage - What activities work best for shy students?
- 🤖 AI: Create Variation - Adapt "Email Writing" for online class
```

## Card Description Template (Structured for AI):

### Activity Cards:
```
📊 METADATA:
Level: Intermediate
Duration: 20 minutes  
Energy: Medium
Skills: Grammar, Speaking
Interaction: Pairs then Individual
Materials: Worksheet, Timer

🎯 OBJECTIVES:
- Master present perfect vs past simple
- Use time expressions (for/since)
- Practice in conversation context

📝 INSTRUCTIONS:
1. Warm-up (3m): Timeline on board
2. Explanation (5m): Key differences
3. Practice (8m): Worksheet completion
4. Speaking (4m): Interview partner

🔄 VARIATIONS:
- Online: Use Jamboard for timeline
- Large class: Gallery walk with examples
- Advanced: Add present perfect continuous

💡 NOTES:
Best after past tense lesson
Students struggle with "since" vs "for"  
Keep examples relevant to their jobs

🏷️ TAGS: #tested #popular #grammar-sequence
```

### AI Command Cards:
```
🤖 AI REQUEST:
Type: Lesson Builder
Student: Maria Rodriguez  
Level: Intermediate
Duration: 120 minutes
Focus: Business presentations
Constraints: Online class, max 8 students

📋 REQUIREMENTS:
- Include warmup (10m)
- 2-3 main activities
- Interactive elements for Zoom
- Homework assignment
- Materials list

⏰ DEADLINE: Need by Monday 9am

🎯 CONTEXT:
Student profile: Accountant, shy speaker
Previous lessons: Email writing, phone skills
Struggles with: Speaking fluency, confidence
Goals: Quarterly business presentations
```

## AI Interaction Patterns:

### 1. Comment-Based Commands:
```
Teacher adds comment to any card:
"@ai suggest 3 similar activities but easier"
"@ai create homework for this activity" 
"@ai what comes before this in learning sequence?"
"@ai adapt this for online class"

AI responds in same comment thread with suggestions.
```

### 2. List-Based Triggers:
```
Move card to "AI Requests" list:
→ AI analyzes card and creates response in "AI Suggestions"

Move card to "This Week":  
→ AI adds preparation checklist
→ AI checks for prerequisites
→ AI suggests lesson order

Move card to "Needs Revision":
→ AI analyzes why it might need revision
→ AI suggests improvements
```

### 3. Label-Based Actions:
```
Add "🤖 Analyze" label:
→ AI reviews activity usage stats
→ Posts comment with insights

Add "🤖 Alternative" label:  
→ AI finds similar activities
→ Creates new cards with alternatives

Add "🤖 Sequence" label:
→ AI suggests what to teach before/after
→ Creates learning pathway
```

### 4. Scheduled AI Cards:
```
Card: "🤖 Weekly Planner - Auto"
Every Sunday at 6pm:
→ AI reviews "This Week" list
→ Creates lesson plan suggestions
→ Checks material requirements
→ Posts planning card for Monday

Card: "🤖 Usage Analytics - Monthly"  
First of month:
→ AI analyzes previous month's activities
→ Reports most/least used
→ Suggests neglected skills
→ Creates improvement recommendations
```

## Special List Behaviors:

### "🤖 AI Requests" List:
- Any card moved here triggers AI analysis
- AI posts response in "AI Suggestions"  
- Original card gets "Processing" label
- Auto-moves to "Suggestions" when done

### "📋 AI Suggestions" List:
- AI-created cards with recommendations
- Teacher can drag activities to "Activity Bank"
- Has "Accept" and "Reject" checklists
- Auto-archives after 1 week if no action

### "📅 This Week" List: 
- Moving card here triggers prep automation
- AI adds preparation checklist
- Checks material links still work
- Estimates total lesson time
- Warns if over/under duration targets

## Board Automation Rules (Butler + Webhook):

### Butler Rules:
```
1. When comment contains "@ai" → Add "AI Request" label

2. When card moved to "This Week" → Add due date (next Friday)

3. When card moved to "Completed" → Add completion date to title

4. Every Monday 8am → Create card "🗓️ This Week's Plan" in "AI Requests"

5. When label "🤖 Analyze" added → Move to "AI Requests" list
```

### Webhook Triggers:
```
1. Card moved to "AI Requests" → Process AI request

2. Comment with "@ai" → Generate AI response

3. Card created with "🤖" in title → Auto-process command

4. Label "🤖" added → Trigger appropriate AI function

5. Card moved to "This Week" → Create prep checklist
```

## Sample Board Setup Commands:

### Initial Setup (Manual):
1. Create board: "English Curriculum AI Assistant"
2. Create all lists in order
3. Add labels with colors
4. Create sample activity cards
5. Set up Butler rules
6. Configure webhook URL

### AI Command Examples:
```
Card: "🤖 AI: Import Activities"
Description: "Analyze attached PDF and create activity cards"
Action: Move to "AI Requests" → AI extracts activities from document

Card: "🤖 AI: Student Assessment" 
Description: "Based on Maria's progress, suggest next 3 activities"
Action: Comment with "@ai assess student progress" → AI analyzes and suggests

Card: "🤖 AI: Lesson Optimizer"
Description: "Analyze my teaching patterns and suggest improvements"  
Action: Scheduled monthly → AI reviews board usage and suggests optimizations
```

This structure makes Trello a powerful AI-assisted curriculum management system where the teacher never leaves the Trello interface but gets intelligent assistance for every aspect of lesson planning.