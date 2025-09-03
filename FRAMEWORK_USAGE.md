# Course Framework Management

## Overview

The Course Framework feature allows teachers to save course structures as templates and generate multiple variants automatically. This is perfect for creating customized versions of a course for different student levels, focus areas, or durations.

## How It Works

### 1. Saving a Framework

Create a Trello card with your course framework structure in JSON format in the description, then comment:
```
@ai save framework
```

The framework will be stored permanently and assigned a unique ID.

### 2. Framework Structure

A framework should include:
```json
{
  "description": "Course description",
  "modules": [
    {
      "id": 1,
      "name": "Module Name",
      "objectives": ["Objective 1", "Objective 2"],
      "duration": "2 weeks",
      "activities": ["Activity 1", "Activity 2"]
    }
  ],
  "assessment_methods": ["Method 1", "Method 2"],
  "target_level": "B2",
  "total_duration": "8 weeks"
}
```

### 3. Generating Variants

To generate variants of a saved framework:
```
@ai generate variants framework_id=xxx num=5 list=Variants
```

Parameters:
- `framework_id`: The ID of the saved framework
- `num`: Number of variants to generate (default: 3)
- `list`: Name of the Trello list for variant cards (default: "Framework Variants")

### 4. Listing Frameworks

To see all saved frameworks:
```
@ai list frameworks
```

## Variant Generation

The system automatically creates variants by adjusting:

1. **Proficiency Levels**: B1, B2, C1, etc.
2. **Focus Areas**: General, Business, Academic, Technical
3. **Duration**: 4-week, 8-week, 12-week courses
4. **Intensity**: Standard or Intensive

Each variant gets its own Trello card with:
- Customized name indicating parameters
- Adjusted module content for the level
- Appropriate activities and assessments
- Full framework structure in comments

## Example Workflow

1. **Create Base Framework**
   - Design your ideal course structure
   - Save it as a Trello card with JSON in description

2. **Save Framework**
   - Comment: `@ai save framework`
   - Note the framework ID returned

3. **Generate Variants**
   - Comment: `@ai generate variants framework_id=abc123 num=6`
   - System creates 6 variant cards in "Framework Variants" list

4. **Customize Further**
   - Each variant can be manually adjusted
   - Use variants as starting points for specific students

## Benefits

- **Time Saving**: Generate multiple course versions in seconds
- **Consistency**: Maintain structure while adapting content
- **Personalization**: Quickly create student-specific curricula
- **Scalability**: Manage dozens of course variations easily
- **Memory**: Frameworks are permanently stored and reusable

## Tips

1. Start with a well-structured base framework
2. Include clear objectives and assessment methods
3. Use descriptive module names
4. Test with a small number of variants first
5. Review and adjust generated variants as needed

## Troubleshooting

If variants aren't generating:
- Ensure framework ID is correct
- Check that OpenAI API key is configured
- Verify DynamoDB table exists and is accessible
- Look for error messages in Lambda logs

## Future Enhancements

Planned features include:
- Variant templates for specific industries
- Student progress tracking per variant
- Automatic variant selection based on assessment
- Collaborative framework sharing between teachers