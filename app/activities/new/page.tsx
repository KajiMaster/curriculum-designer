'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Save } from 'lucide-react'
import Link from 'next/link'

const categories = [
  'GRAMMAR', 'VOCABULARY', 'SPEAKING', 'LISTENING', 
  'READING', 'WRITING', 'PRONUNCIATION', 'BUSINESS', 
  'CONVERSATION', 'CULTURE'
]

const difficulties = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED']

const professionOptions = [
  'Business Professionals', 'Healthcare Workers', 'Engineers/Tech', 
  'Legal Professionals', 'Education/Academia', 'Sales/Marketing',
  'Finance/Banking', 'General Professional', 'Customer Service'
]

export default function NewActivityPage() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'CONVERSATION',
    subcategory: '',
    difficulty: 'INTERMEDIATE',
    minDuration: 15,
    maxDuration: 25,
    typicalDuration: 20,
    objectives: [''],
    instructions: '',
    materials: '',
    tags: '',
    profession: 'Business Professionals',
    skillsFocus: '',
    preparation: '',
    variations: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/activities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          objectives: formData.objectives.filter(obj => obj.trim()),
          materials: formData.materials ? { description: formData.materials } : {},
          variations: formData.variations ? { description: formData.variations } : {},
          tags: formData.tags.split(',').map(tag => tag.trim()).filter(Boolean),
          profession: [formData.profession]
        })
      })

      if (response.ok) {
        router.push('/activities')
      } else {
        console.error('Failed to create activity')
      }
    } catch (error) {
      console.error('Error creating activity:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const addObjective = () => {
    setFormData(prev => ({
      ...prev,
      objectives: [...prev.objectives, '']
    }))
  }

  const updateObjective = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      objectives: prev.objectives.map((obj, i) => i === index ? value : obj)
    }))
  }

  const removeObjective = (index: number) => {
    setFormData(prev => ({
      ...prev,
      objectives: prev.objectives.filter((_, i) => i !== index)
    }))
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="flex items-center gap-4 mb-8">
        <Link href="/activities" className="text-gray-600 hover:text-gray-800">
          <ArrowLeft size={24} />
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Create New Activity</h1>
          <p className="text-gray-600 mt-1">Add a new modular activity to your curriculum library</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium mb-2">Title</label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Primary Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Subcategory</label>
              <input
                type="text"
                value={formData.subcategory}
                onChange={(e) => setFormData(prev => ({ ...prev, subcategory: e.target.value }))}
                placeholder="e.g., Presentation Skills, Email Writing"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Level</label>
              <select
                value={formData.difficulty}
                onChange={(e) => setFormData(prev => ({ ...prev, difficulty: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {difficulties.map(diff => (
                  <option key={diff} value={diff}>{diff}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Target Profession</label>
              <select
                value={formData.profession}
                onChange={(e) => setFormData(prev => ({ ...prev, profession: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {professionOptions.map(prof => (
                  <option key={prof} value={prof}>{prof}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-sm font-medium mb-2">Min Duration</label>
                <input
                  type="number"
                  required
                  min="5"
                  step="5"
                  value={formData.minDuration}
                  onChange={(e) => setFormData(prev => ({ ...prev, minDuration: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Typical</label>
                <input
                  type="number"
                  required
                  min="5"
                  step="5"
                  value={formData.typicalDuration}
                  onChange={(e) => setFormData(prev => ({ ...prev, typicalDuration: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Max Duration</label>
                <input
                  type="number"
                  required
                  min="5"
                  step="5"
                  value={formData.maxDuration}
                  onChange={(e) => setFormData(prev => ({ ...prev, maxDuration: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <div className="mt-6">
            <label className="block text-sm font-medium mb-2">Description</label>
            <textarea
              required
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Learning Objectives</h2>
          
          {formData.objectives.map((objective, index) => (
            <div key={index} className="flex gap-2 mb-3">
              <input
                type="text"
                placeholder="Learning objective..."
                value={objective}
                onChange={(e) => updateObjective(index, e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {formData.objectives.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeObjective(index)}
                  className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          
          <button
            type="button"
            onClick={addObjective}
            className="mt-2 text-blue-600 hover:text-blue-700"
          >
            + Add Objective
          </button>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Activity Details</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Step-by-Step Instructions</label>
              <textarea
                required
                rows={6}
                value={formData.instructions}
                onChange={(e) => setFormData(prev => ({ ...prev, instructions: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="1. Warm-up: Ask students about...&#10;2. Present vocabulary/concept...&#10;3. Practice activity...&#10;4. Wrap-up discussion..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Skills Focus</label>
              <input
                type="text"
                value={formData.skillsFocus}
                onChange={(e) => setFormData(prev => ({ ...prev, skillsFocus: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Negotiation vocabulary, Past tense, Presentation confidence"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Materials Needed</label>
              <textarea
                rows={2}
                value={formData.materials}
                onChange={(e) => setFormData(prev => ({ ...prev, materials: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Handouts, whiteboard, role-play cards, timer..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Teacher Preparation</label>
              <textarea
                rows={3}
                value={formData.preparation}
                onChange={(e) => setFormData(prev => ({ ...prev, preparation: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Review key vocabulary, prepare examples, set up breakout rooms..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Activity Variations</label>
              <textarea
                rows={3}
                value={formData.variations}
                onChange={(e) => setFormData(prev => ({ ...prev, variations: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="For larger groups: divide into teams...&#10;For advanced students: add complexity...&#10;Online adaptation: use breakout rooms..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Tags</label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData(prev => ({ ...prev, tags: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="interactive, role-play, group-work, presentation"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-4">
          <Link
            href="/activities"
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg flex items-center gap-2"
          >
            <Save size={16} />
            {isSubmitting ? 'Creating...' : 'Create Activity'}
          </button>
        </div>
      </form>
    </div>
  )
}