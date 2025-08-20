// MCP Server - Provides Trello context to Claude
const { MCPServer } = require('@modelcontextprotocol/server');
const fetch = require('node-fetch');

class CurriculumMCPServer extends MCPServer {
  constructor() {
    super({
      name: 'curriculum-designer',
      version: '1.0.0',
      description: 'Provides curriculum activities from Trello to AI'
    });

    this.trelloKey = process.env.TRELLO_API_KEY;
    this.trelloToken = process.env.TRELLO_TOKEN;
    this.boardId = process.env.TRELLO_BOARD_ID;
  }

  async getTools() {
    return [
      {
        name: 'get_activities',
        description: 'Get all curriculum activities from Trello',
        inputSchema: {
          type: 'object',
          properties: {
            category: { type: 'string', description: 'Filter by category (grammar, speaking, etc)' },
            level: { type: 'string', description: 'Filter by level (beginner, intermediate, advanced)' },
            duration: { type: 'number', description: 'Maximum duration in minutes' }
          }
        }
      },
      {
        name: 'suggest_lesson',
        description: 'Suggest activities for a lesson plan',
        inputSchema: {
          type: 'object',
          properties: {
            student_level: { type: 'string', required: true },
            focus_area: { type: 'string' },
            total_duration: { type: 'number', default: 120 }
          }
        }
      },
      {
        name: 'search_activities',
        description: 'Search activities by keyword',
        inputSchema: {
          type: 'object',
          properties: {
            query: { type: 'string', required: true }
          }
        }
      }
    ];
  }

  async handleToolCall(name, args) {
    switch(name) {
      case 'get_activities':
        return await this.getActivities(args);
      case 'suggest_lesson':
        return await this.suggestLesson(args);
      case 'search_activities':
        return await this.searchActivities(args);
    }
  }

  async getActivities({ category, level, duration }) {
    // Fetch cards from Trello
    const cards = await fetch(
      `https://api.trello.com/1/boards/${this.boardId}/cards?key=${this.trelloKey}&token=${this.trelloToken}`
    ).then(r => r.json());

    // Parse activity data from card descriptions
    const activities = cards.map(card => {
      // Parse structured data from card description
      // Format: [Level: X] [Duration: Y] [Category: Z]
      const parsed = this.parseCardData(card);
      return {
        id: card.id,
        name: card.name,
        description: card.desc,
        level: parsed.level,
        duration: parsed.duration,
        category: parsed.category,
        materials: parsed.materials,
        listName: card.list.name
      };
    });

    // Apply filters
    let filtered = activities;
    if (category) filtered = filtered.filter(a => a.category === category);
    if (level) filtered = filtered.filter(a => a.level === level);
    if (duration) filtered = filtered.filter(a => a.duration <= duration);

    return filtered;
  }

  async suggestLesson({ student_level, focus_area, total_duration }) {
    const activities = await this.getActivities({ level: student_level });
    
    // Smart lesson building logic
    const lesson = {
      warmup: null,
      main_activities: [],
      cooldown: null,
      total_duration: 0
    };

    // Find warmup (5-10 min, lighter cognitive load)
    lesson.warmup = activities.find(a => 
      a.duration <= 10 && 
      a.tags?.includes('warmup')
    );

    // Find main activities (aim for variety)
    const mainTime = total_duration - 20; // Reserve time for warmup/cooldown
    // ... smart selection logic here

    return lesson;
  }

  parseCardData(card) {
    // Extract structured data from Trello card
    const regex = /\[(\w+):\s*([^\]]+)\]/g;
    const data = {};
    let match;
    
    while ((match = regex.exec(card.desc)) !== null) {
      data[match[1].toLowerCase()] = match[2];
    }
    
    return {
      level: data.level || 'intermediate',
      duration: parseInt(data.duration) || 20,
      category: data.category || 'general',
      materials: data.materials || ''
    };
  }
}

// Export for Lambda
exports.handler = async (event) => {
  const server = new CurriculumMCPServer();
  return await server.handle(event);
};