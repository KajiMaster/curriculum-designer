# Trello Card Template for AI Parsing

## Card Title Format
[Duration] Activity Name | Category

## Card Description Structure
```
LEVEL: Intermediate
DURATION: 20
ENERGY: High
INTERACTION: Pairs
SKILLS: Speaking, Listening, Business Vocabulary
PROFESSION: Business, Sales, Marketing

OBJECTIVES:
- Practice negotiation phrases
- Build confidence in disagreeing politely
- Learn to make counteroffers

MATERIALS:
- Roleplay cards (PDF link)
- Whiteboard for vocabulary
- Timer

INSTRUCTIONS:
1. Warm-up (3 min): Review key phrases on board
2. Demo (5 min): Teacher models negotiation with strong student
3. Practice (10 min): Pairs negotiate using scenario cards
4. Wrap-up (2 min): Share successful phrases

VARIATIONS:
Online: Use breakout rooms, share scenario in chat
Large Group: Fishbowl technique with observers taking notes
Advanced: Add time pressure or unexpected complications

NOTES:
Works best after "Making Suggestions" lesson
Students love the competitive element
Save 5 min buffer for feedback
```

## Example Real Card

### Title: `[25m] Restaurant Complaints Roleplay | Speaking`

### Description:
```
LEVEL: Intermediate
DURATION: 25
ENERGY: Medium
INTERACTION: Pairs
SKILLS: Speaking, Listening, Customer Service
PROFESSION: Hospitality, Service, General

OBJECTIVES:
- Practice polite complaint language
- Learn to respond to complaints professionally
- Use conditional structures naturally

MATERIALS:
- Situation cards (Google Drive link)
- Complaint phrases handout
- Feedback checklist

INSTRUCTIONS:
1. Warm-up (3 min): Brainstorm complaint situations
2. Language (5 min): Review polite phrases "I'm afraid...", "Would it be possible..."
3. Practice Round 1 (7 min): Simple complaints
4. Practice Round 2 (7 min): Escalated situations
5. Debrief (3 min): Most challenging situations

VARIATIONS:
Beginner: Provide full dialogue templates
Advanced: Add cultural misunderstandings
Online: Record and review conversations

NOTES:
Pre-teach "I'm afraid" vs being afraid
Emphasize tone over words
Great for business English students
```

## Structured Data Fields (AI Can Parse)

### Required Fields:
- **LEVEL**: Beginner | Elementary | Intermediate | Upper-Intermediate | Advanced
- **DURATION**: Number in minutes
- **SKILLS**: Comma-separated list
- **OBJECTIVES**: Bullet points starting with verbs

### Optional but Helpful:
- **ENERGY**: Low | Medium | High
- **INTERACTION**: Individual | Pairs | Groups | Whole Class
- **PROFESSION**: Target professions
- **MATERIALS**: What's needed
- **VARIATIONS**: Adaptations
- **NOTES**: Teacher tips

## Labels for Quick Filtering

### Color-Coded Labels:
- 🟢 Green: Grammar activities
- 🔵 Blue: Speaking activities  
- 🟡 Yellow: Business focus
- 🔴 Red: Needs preparation
- ⚫ Black: Homework/Async
- 🟣 Purple: Assessment

### Tags in Card Names:
- `#warmup` - Good starter activities
- `#cooldown` - Good closing activities
- `#filler` - Can expand/contract timing
- `#tested` - Proven successful
- `#new` - Not yet tested

## Checklists for Reusable Elements

### Materials Checklist:
- [ ] Copies printed
- [ ] Links checked
- [ ] Backup activity ready
- [ ] Timer set
- [ ] Board space cleared

### Post-Activity:
- [ ] Student feedback noted
- [ ] Timing accurate?
- [ ] Objectives met?
- [ ] Update card notes

## Custom Fields (Power-Up)

If using Custom Fields Power-Up:
- **Duration** (Number): For sorting
- **Level** (Dropdown): For filtering
- **Success Rate** (Number): 1-5 rating
- **Last Used** (Date): Track freshness
- **Prep Time** (Number): Setup minutes needed

## AI Parsing Benefits

With this structure, AI can:
1. **Filter effectively**: "Find 20-minute intermediate speaking activities"
2. **Build lessons**: "Create 2-hour lesson with grammar focus"
3. **Suggest alternatives**: "This activity too long, what's similar but shorter?"
4. **Track patterns**: "Which activities work best for business professionals?"
5. **Generate variations**: "Adapt this for online delivery"

## Integration with MCP

The MCP server can extract:
```javascript
const activity = {
  // From title
  duration: extractDuration(card.name), // [20m] -> 20
  name: extractName(card.name),
  quickCategory: extractCategory(card.name),
  
  // From description
  level: extractField(card.desc, 'LEVEL'),
  skills: extractField(card.desc, 'SKILLS').split(','),
  objectives: extractBullets(card.desc, 'OBJECTIVES'),
  
  // From labels
  categories: card.labels.map(l => l.name),
  difficulty: card.labels.find(l => l.color === 'red'),
  
  // From position
  status: card.list.name, // "Ready", "This Week", etc.
}
```

## Quick Copy Templates

### For New Grammar Activity:
```
LEVEL: [Choose: Beginner/Intermediate/Advanced]
DURATION: [Minutes]
ENERGY: Medium
INTERACTION: Individual then Pairs
SKILLS: Grammar, Writing
OBJECTIVES:
- Practice [structure]
- Identify correct usage
- Produce original examples
```

### For New Speaking Activity:
```
LEVEL: [Choose level]
DURATION: [Minutes]
ENERGY: High
INTERACTION: Pairs
SKILLS: Speaking, Listening
OBJECTIVES:
- Practice [topic] vocabulary
- Build fluency
- Give peer feedback
```

## Pro Tips:

1. **Use consistent formatting** - AI parses better
2. **Include duration in title** - For quick scanning
3. **List objectives as verbs** - "Practice", "Learn", "Master"
4. **Add profession tags** - Helps with student matching
5. **Update notes after use** - Creates feedback loop
6. **Link materials** - Google Drive or Dropbox links
7. **Use checklists** - For routine tasks

This structure makes cards:
- **Human-readable** at a glance
- **AI-parseable** for automation
- **Sortable/filterable** in Trello
- **Reusable** across students
- **Trackable** for success metrics