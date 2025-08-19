# Curriculum Designer - AI-Powered Architecture

## System Overview

An intelligent curriculum design platform that leverages AI to help teachers create, organize, and deliver personalized English lessons efficiently.

## Core Technologies

### Frontend
- **Next.js 14** with App Router for modern React development
- **TypeScript** for type safety
- **Tailwind CSS** for rapid UI development
- **Shadcn/UI** for component library
- **React Query** for data fetching

### Backend
- **Next.js API Routes** for backend functionality
- **Prisma** as ORM with PostgreSQL
- **OpenAI API** for AI capabilities
- **NextAuth** for authentication

### AI Integration Points

1. **Student Assessment AI**
   - Analyzes student proficiency through initial questionnaire
   - Suggests appropriate difficulty levels
   - Identifies learning style preferences

2. **Module Recommendation Engine**
   - AI-powered activity selection based on:
     - Student profile
     - Previous lesson performance
     - Learning objectives
     - Professional context

3. **Curriculum Sequencing**
   - Intelligent ordering of activities
   - Pacing recommendations
   - Transition activity suggestions

4. **Content Generation Assistant**
   - Helps create variations of existing activities
   - Generates profession-specific examples
   - Creates custom exercises based on student interests

## System Architecture

```
┌─────────────────────────────────────────────┐
│              Teacher Dashboard              │
├─────────────┬───────────────┬───────────────┤
│   Student   │    Lesson     │   Activity    │
│   Manager   │    Builder    │   Library     │
└──────┬──────┴───────┬───────┴───────┬───────┘
       │              │               │
       ▼              ▼               ▼
┌─────────────────────────────────────────────┐
│            AI Orchestration Layer           │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐    │
│  │Student  │ │ Module   │ │ Content  │    │
│  │Analyzer │ │Recommender│ │Generator │    │
│  └─────────┘ └──────────┘ └──────────┘    │
└─────────────────────────────────────────────┘
       │              │               │
       ▼              ▼               ▼
┌─────────────────────────────────────────────┐
│              Database Layer                 │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐    │
│  │Students │ │Activities │ │ Lessons  │    │
│  └─────────┘ └──────────┘ └──────────┘    │
└─────────────────────────────────────────────┘
```

## Key Features

### 1. Activity Module System
- **Categories**: Grammar, Vocabulary, Conversation, Business English, Pronunciation
- **Metadata**: Duration, difficulty, prerequisites, materials needed
- **Variations**: AI-generated adaptations for different professions
- **Performance Tracking**: Success metrics and student feedback

### 2. Smart Lesson Builder
- **Quick Build**: AI suggests complete lesson based on student profile
- **Manual Override**: Teacher can adjust AI recommendations
- **Time Management**: Automatic timing calculations with buffer zones
- **Resource Attachment**: PDFs, videos, interactive exercises

### 3. Student Profiles
- **Assessment Data**: Initial and ongoing proficiency tracking
- **Learning Preferences**: Visual, auditory, kinesthetic
- **Professional Context**: Industry-specific vocabulary needs
- **Progress Tracking**: Completed modules, improvement areas

### 4. AI Assistant Features
- **Natural Language Queries**: "Show me intermediate conversation activities for lawyers"
- **Adaptive Suggestions**: Learn from teacher's selection patterns
- **Quality Scoring**: AI evaluates activity effectiveness
- **Custom Generation**: Create new activities based on prompts

## Data Models

### Activity Module
```typescript
interface ActivityModule {
  id: string
  title: string
  category: Category[]
  duration: { min: number, max: number, typical: number }
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  objectives: string[]
  materials: Material[]
  instructions: string
  variations: Variation[]
  metrics: PerformanceMetrics
  tags: string[]
}
```

### Student Profile
```typescript
interface StudentProfile {
  id: string
  name: string
  proficiencyLevel: ProficiencyLevel
  profession: string
  interests: string[]
  learningStyle: LearningStyle[]
  goals: Goal[]
  completedModules: CompletedModule[]
  schedule: Schedule
}
```

### Lesson Plan
```typescript
interface LessonPlan {
  id: string
  studentId: string
  date: Date
  duration: number
  mainActivities: ActivityModule[]
  transitions: TransitionActivity[]
  homework?: HomeworkAssignment
  notes: string
  aiSuggestions: AISuggestion[]
}
```

## AI Integration Strategy

### Phase 1: Foundation
- Basic activity categorization
- Simple recommendation based on difficulty
- Template-based lesson generation

### Phase 2: Intelligence
- Learning pattern recognition
- Performance-based adjustments
- Context-aware content generation

### Phase 3: Advanced
- Predictive curriculum planning
- Multi-student pattern analysis
- Fully autonomous lesson generation with review

## User Workflows

### Creating a New Student Curriculum
1. Teacher inputs student information
2. AI analyzes profile and suggests initial assessment
3. Based on assessment, AI recommends 12-week curriculum outline
4. Teacher reviews and adjusts recommendations
5. System generates first 3 lessons automatically

### Building a Single Lesson
1. Select student from dashboard
2. AI pre-populates lesson with recommended activities
3. Teacher can:
   - Accept recommendations
   - Browse alternative activities
   - Ask AI for specific adjustments
4. System calculates timing and generates lesson plan
5. Export or display for teaching session

### Post-Lesson Workflow
1. Teacher provides quick feedback on each activity
2. AI analyzes effectiveness
3. Adjustments made to future recommendations
4. Progress report generated for student

## Security & Privacy
- End-to-end encryption for student data
- GDPR compliance for international students
- Role-based access control
- Audit logging for all AI decisions