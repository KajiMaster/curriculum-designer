#!/usr/bin/env node

// MCP Server - Provides Trello context to Claude
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { 
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const fetch = require('node-fetch');

class CurriculumMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'curriculum-designer',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.trelloKey = process.env.TRELLO_API_KEY;
    this.trelloToken = process.env.TRELLO_TOKEN;
    this.boardId = process.env.TRELLO_BOARD_ID;
    
    this.setupToolHandlers();
  }

  setupToolHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
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
        ]
      };
    });

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        switch(name) {
          case 'get_activities':
            return { content: [{ type: 'text', text: JSON.stringify(await this.getActivities(args || {})) }] };
          case 'suggest_lesson':
            return { content: [{ type: 'text', text: JSON.stringify(await this.suggestLesson(args || {})) }] };
          case 'search_activities':
            return { content: [{ type: 'text', text: JSON.stringify(await this.searchActivities(args || {})) }] };
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{ type: 'text', text: `Error: ${error.message}` }],
          isError: true
        };
      }
    });
  }

  async searchActivities({ query }) {
    const activities = await this.getActivities({});
    
    // Simple text search across name and description
    const filtered = activities.filter(activity => 
      activity.name.toLowerCase().includes(query.toLowerCase()) ||
      activity.description.toLowerCase().includes(query.toLowerCase())
    );
    
    return filtered;
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Curriculum Designer MCP Server running on stdio');
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

// Main execution
if (require.main === module) {
  const server = new CurriculumMCPServer();
  server.run().catch(console.error);
}

module.exports = { CurriculumMCPServer };