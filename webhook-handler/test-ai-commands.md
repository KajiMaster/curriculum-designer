# AI Commands Testing Guide

## Production Testing Checklist

Test these commands in your Trello board to verify the webhook handler is working correctly.

### 🟢 Basic Tests (Start Here)

1. **Health Check**
   ```
   @ai hello
   ```
   **Expected**: Personalized teaching assistant greeting
   
2. **Help Command**
   ```
   @ai help
   ```
   **Expected**: List of available commands or assistance offer

### 🎯 Activity Generation Tests

3. **Simple Activity**
   ```
   @ai activity "Colors and Shapes" grade:2 duration:15
   ```
   **Expected**: 
   - Acknowledgment comment with parameters
   - Detailed activity with materials, steps, objectives

4. **Activity with Type**
   ```
   @ai generate activity "Animals" grade:3 duration:20 type:game
   ```
   **Expected**: Game-based learning activity for animals

5. **Complex Activity Request**
   ```
   @ai activity "Food and Drinks" grade:4 duration:30 type:preference_choice
   ```
   **Expected**: Preference/opinion-based activity about food

### 📚 Lesson Plan Tests

6. **Basic Lesson Plan**
   ```
   @ai create lesson plan for beginner students focusing on greetings for 45 minutes
   ```
   **Expected**: Complete lesson plan with warm-up, main content, practice, wrap-up

7. **Advanced Lesson Plan**
   ```
   @ai lesson plan for intermediate students grammar focus 60 minutes
   ```
   **Expected**: Grammar-focused lesson with exercises

### 🔍 Analysis Tests

8. **Activity Analysis**
   ```
   @ai analyze Vocabulary Bingo
   ```
   **Expected**: Analysis with strengths, improvements, variations

9. **Review Request**
   ```
   @ai suggest improvements for this activity
   ```
   **Expected**: Specific improvement suggestions based on card content

### 💾 Framework Tests

10. **Save Framework** (on a well-structured card)
    ```
    @ai save framework
    ```
    **Expected**: Confirmation with framework ID

11. **Generate Variants** (on a saved framework card)
    ```
    @ai generate 2 variants
    ```
    **Expected**: Creates 2 new cards with framework variations

12. **List Frameworks**
    ```
    @ai list frameworks
    ```
    **Expected**: List of all saved frameworks for the board

### 💬 Feedback Tests (Only on Lesson Plans Board)

13. **Like Feedback**
    ```
    @ai like: This worked perfectly with my class!
    ```
    **Expected**: Confirmation that positive feedback was recorded

14. **Rating Feedback**
    ```
    @ai rating: 4/5
    ```
    **Expected**: Confirmation that rating was recorded

15. **Improvement Feedback**
    ```
    @ai improve: Add more visual aids
    ```
    **Expected**: Confirmation that suggestion was recorded

### 🎓 General Teaching Assistance

16. **Grammar Help**
    ```
    @ai help me explain present perfect tense to beginners
    ```
    **Expected**: Clear explanation with examples

17. **Resource Request**
    ```
    @ai suggest online resources for teaching pronunciation
    ```
    **Expected**: List of recommended resources

18. **Classroom Management**
    ```
    @ai how do I handle mixed-level groups in speaking activities?
    ```
    **Expected**: Practical strategies and tips

### 🚀 Advanced Tests

19. **Multi-parameter Activity**
    ```
    @ai generate activity "Technology and Social Media" grade:7 duration:25 type:discussion
    ```
    **Expected**: Discussion-based activity for older students

20. **Context-Aware Request**
    Create a card titled "Verb Conjugation Practice" with description, then:
    ```
    @ai create exercises for this topic
    ```
    **Expected**: Exercises specifically for verb conjugation

## Response Time Expectations

- **Simple queries**: 2-3 seconds
- **Activity generation**: 3-5 seconds  
- **Lesson plans**: 5-7 seconds
- **Framework variants**: 5-10 seconds

## Troubleshooting

### If "@ai hello" doesn't work:
1. Check Lambda logs: `aws logs tail /aws/lambda/curriculum-designer-webhook-dev --follow`
2. Verify webhook URL in Trello
3. Check API keys in Parameter Store

### If responses are generic:
1. Be more specific in commands
2. Include grade level and duration
3. Use structured commands (activity, lesson plan, etc.)

### If getting errors:
1. Check exact command syntax
2. Verify board IDs in config
3. Review Lambda function logs

## Success Criteria

✅ Test is successful if:
- Response appears within 10 seconds
- Content is relevant to the request
- Formatting includes emoji markers (🤖, 🎯, 📚, etc.)
- No error messages in response

❌ Test fails if:
- No response after 30 seconds
- Generic "I don't understand" response
- Error message in comment
- Lambda function error in logs

## Logging Commands

To monitor while testing:
```bash
# Watch Lambda logs
aws logs tail /aws/lambda/curriculum-designer-webhook-dev --follow

# Check recent invocations
aws lambda list-functions --query "Functions[?FunctionName=='curriculum-designer-webhook-dev']"

# Get function metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=curriculum-designer-webhook-dev \
  --start-time 2024-01-14T00:00:00Z \
  --end-time 2024-01-14T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## Test Results Recording

| Command | Result | Response Time | Notes |
|---------|---------|--------------|-------|
| @ai hello | ✅/❌ | Xs | |
| @ai activity "topic" | ✅/❌ | Xs | |
| @ai lesson plan | ✅/❌ | Xs | |
| @ai save framework | ✅/❌ | Xs | |
| @ai rating: 5/5 | ✅/❌ | Xs | |

Record your results to track system performance and identify issues.