// Script to import activities into Trello with proper structure
const fetch = require('node-fetch');
const fs = require('fs');

class TrelloImporter {
  constructor(apiKey, token, boardId) {
    this.apiKey = apiKey;
    this.token = token;
    this.boardId = boardId;
    this.baseUrl = 'https://api.trello.com/1';
  }

  // Create a properly formatted card
  async createActivityCard(activity) {
    const title = this.formatTitle(activity);
    const description = this.formatDescription(activity);
    const listId = await this.getListId(activity.category);
    const labels = await this.getLabels(activity);

    const card = await fetch(`${this.baseUrl}/cards`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        key: this.apiKey,
        token: this.token,
        idList: listId,
        name: title,
        desc: description,
        idLabels: labels,
        pos: 'bottom'
      })
    }).then(r => r.json());

    console.log(`Created: ${title}`);
    return card;
  }

  formatTitle(activity) {
    return `[${activity.duration}m] ${activity.name} | ${activity.category}`;
  }

  formatDescription(activity) {
    return `LEVEL: ${activity.level}
DURATION: ${activity.duration}
ENERGY: ${activity.energy || 'Medium'}
INTERACTION: ${activity.interaction || 'Pairs'}
SKILLS: ${activity.skills.join(', ')}
PROFESSION: ${activity.professions?.join(', ') || 'General'}

OBJECTIVES:
${activity.objectives.map(obj => `- ${obj}`).join('\n')}

MATERIALS:
${activity.materials || '- None required'}

INSTRUCTIONS:
${activity.instructions}

VARIATIONS:
${activity.variations || 'None yet'}

NOTES:
${activity.notes || 'No notes yet'}`;
  }

  async getListId(category) {
    // Map categories to Trello lists
    const listMap = {
      'Grammar': 'grammar_list_id',
      'Speaking': 'speaking_list_id',
      'Writing': 'writing_list_id',
      'Business': 'business_list_id',
      'General': 'ready_list_id'
    };

    // In real implementation, fetch actual list IDs
    const lists = await fetch(
      `${this.baseUrl}/boards/${this.boardId}/lists?key=${this.apiKey}&token=${this.token}`
    ).then(r => r.json());

    const list = lists.find(l => l.name.toLowerCase().includes(category.toLowerCase()));
    return list ? list.id : lists[0].id;
  }

  async getLabels(activity) {
    const labels = [];
    
    // Get all board labels
    const boardLabels = await fetch(
      `${this.baseUrl}/boards/${this.boardId}/labels?key=${this.apiKey}&token=${this.token}`
    ).then(r => r.json());

    // Match activity properties to labels
    const levelLabel = boardLabels.find(l => 
      l.name.toLowerCase() === activity.level.toLowerCase()
    );
    if (levelLabel) labels.push(levelLabel.id);

    const categoryLabel = boardLabels.find(l => 
      l.name.toLowerCase() === activity.category.toLowerCase()
    );
    if (categoryLabel) labels.push(categoryLabel.id);

    return labels;
  }

  // Import from CSV
  async importFromCSV(filepath) {
    const csv = fs.readFileSync(filepath, 'utf-8');
    const lines = csv.split('\n');
    const headers = lines[0].split(',');
    
    for (let i = 1; i < lines.length; i++) {
      const data = lines[i].split(',');
      const activity = {};
      
      headers.forEach((header, index) => {
        activity[header.trim()] = data[index]?.trim();
      });

      // Transform to our structure
      const formatted = {
        name: activity.title || activity.name,
        duration: parseInt(activity.duration) || 20,
        category: activity.category || 'General',
        level: activity.level || 'Intermediate',
        skills: (activity.skills || '').split(';'),
        objectives: (activity.objectives || '').split(';'),
        instructions: activity.instructions || '',
        materials: activity.materials || '',
        variations: activity.variations || '',
        notes: activity.notes || ''
      };

      await this.createActivityCard(formatted);
      
      // Rate limit
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  // Import from JSON (export from Canva or other tools)
  async importFromJSON(filepath) {
    const activities = JSON.parse(fs.readFileSync(filepath, 'utf-8'));
    
    for (const activity of activities) {
      await this.createActivityCard(activity);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  // Parse existing unstructured cards and reformat them
  async reformatExistingCards() {
    const cards = await fetch(
      `${this.baseUrl}/boards/${this.boardId}/cards?key=${this.apiKey}&token=${this.token}`
    ).then(r => r.json());

    for (const card of cards) {
      // Skip if already formatted
      if (card.name.includes('[') && card.desc.includes('LEVEL:')) {
        continue;
      }

      // Try to parse and reformat
      const formatted = this.parseUnstructuredCard(card);
      
      // Update the card
      await fetch(`${this.baseUrl}/cards/${card.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          key: this.apiKey,
          token: this.token,
          name: this.formatTitle(formatted),
          desc: this.formatDescription(formatted)
        })
      });

      console.log(`Reformatted: ${card.name}`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  parseUnstructuredCard(card) {
    // Attempt to extract structure from freeform text
    const activity = {
      name: card.name,
      duration: 20, // default
      category: 'General',
      level: 'Intermediate',
      skills: [],
      objectives: [],
      instructions: card.desc || '',
      materials: '',
      variations: '',
      notes: ''
    };

    // Try to extract duration from name
    const durationMatch = card.name.match(/(\d+)\s*min/i);
    if (durationMatch) {
      activity.duration = parseInt(durationMatch[1]);
    }

    // Try to detect category
    const categoryKeywords = {
      'Grammar': ['grammar', 'tense', 'conditional', 'passive'],
      'Speaking': ['speaking', 'conversation', 'roleplay', 'discussion'],
      'Writing': ['writing', 'essay', 'email', 'letter'],
      'Business': ['business', 'negotiation', 'presentation', 'meeting']
    };

    for (const [cat, keywords] of Object.entries(categoryKeywords)) {
      if (keywords.some(kw => card.name.toLowerCase().includes(kw))) {
        activity.category = cat;
        break;
      }
    }

    // Extract from description if it has any structure
    if (card.desc) {
      // Look for common patterns
      const levelMatch = card.desc.match(/level[:\s]+(\w+)/i);
      if (levelMatch) activity.level = levelMatch[1];

      // Look for objectives
      const objectivesMatch = card.desc.match(/objectives?[:\s]+(.*?)(?:\n\n|$)/is);
      if (objectivesMatch) {
        activity.objectives = objectivesMatch[1]
          .split(/[\n\-•]/)
          .filter(o => o.trim())
          .map(o => o.trim());
      }
    }

    return activity;
  }
}

// Usage example
async function main() {
  const importer = new TrelloImporter(
    process.env.TRELLO_API_KEY,
    process.env.TRELLO_TOKEN,
    process.env.TRELLO_BOARD_ID
  );

  // Import from different sources
  // await importer.importFromCSV('./activities.csv');
  // await importer.importFromJSON('./canva-export.json');
  
  // Or reformat existing cards
  await importer.reformatExistingCards();
}

// Run if called directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = TrelloImporter;