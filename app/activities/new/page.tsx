'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ActivityCategory, DifficultyLevel } from '@prisma/client'

const categories = [
  { value: 'GRAMMAR', label: 'Grammar' },
  { value: 'VOCABULARY', label: 'Vocabulary' },
  { value: 'SPEAKING', label: 'Speaking' },
  { value: 'LISTENING', label: 'Listening' },
  { value: 'READING', label: 'Reading' },
  { value: 'WRITING', label: 'Writing' },
  { value: 'PRONUNCIATION', label: 'Pronunciation' },
  { value: 'BUSINESS', label: 'Business English' },
  { value: 'CONVERSATION', label: 'Conversation' },
  { value: 'CULTURE', label: 'Culture' }
]

const difficulties = [
  { value: 'BEGINNER', label: 'Beginner' },
  { value: 'INTERMEDIATE', label: 'Intermediate' },
  { value: 'ADVANCED', label: 'Advanced' }
]

export default function NewActivityPage() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'GRAMMAR' as ActivityCategory,
    difficulty: 'BEGINNER' as DifficultyLevel,
    minDuration: 15,
    maxDuration: 45,
    typicalDuration: 30,
    objectives: [''],
    instructions: '',
    materials: '',
    tags: '',
    profession: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const objectives = formData.objectives.filter(obj => obj.trim() !== '')
      const tags = formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag !== '')
      const professions = formData.profession.split(',').map(prof => prof.trim()).filter(prof => prof !== '')

      const response = await fetch('/api/activities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          objectives,
          tags,
          profession: professions,
          materials: formData.materials ? JSON.parse(formData.materials) : {}
        }),
      })

      if (response.ok) {
        const activity = await response.json()
        router.push(`/activities/${activity.id}`)
      } else {
        throw new Error('Failed to create activity')
      }
    } catch (error) {
      console.error('Error creating activity:', error)
      alert('Failed to create activity. Please try again.')
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
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <Link href="/activities" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
          ← Back to Activities
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 mt-2">Create New Activity</h1>
        <p className="text-gray-600 mt-2">Build a modular curriculum activity</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Information */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
          
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Activity Title *
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Present Perfect Tense Practice"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category *
              </label>
              <select
                required
                value={formData.category}
                onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value as ActivityCategory }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {categories.map(cat => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Difficulty Level *
              </label>
              <select
                required
                value={formData.difficulty}
                onChange={(e) => setFormData(prev => ({ ...prev, difficulty: e.target.value as DifficultyLevel }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {difficulties.map(diff => (
                  <option key={diff.value} value={diff.value}>{diff.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Typical Duration (minutes) *
              </label>
              <input
                type="number"
                required
                min="5"
                max="120"
                value={formData.typicalDuration}
                onChange={(e) => setFormData(prev => ({ ...prev, typicalDuration: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              required
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Brief description of what this activity covers..."
            />
          </div>
        </div>

        {/* Learning Objectives */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Learning Objectives</h2>
          
          {formData.objectives.map((objective, index) => (
            <div key={index} className="flex gap-2 mb-3">
              <input
                type="text"
                value={objective}
                onChange={(e) => updateObjective(index, e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Students will be able to form present perfect questions"
              />
              {formData.objectives.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeObjective(index)}
                  className="px-3 py-2 text-red-600 hover:text-red-800"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          
          <button
            type="button"
            onClick={addObjective}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            + Add Objective
          </button>
        </div>

        {/* Instructions */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Instructions</h2>
          <textarea
            rows={6}
            value={formData.instructions}
            onChange={(e) => setFormData(prev => ({ ...prev, instructions: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Step-by-step instructions for conducting this activity..."
          />
        </div>

        {/* Additional Details */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Additional Details</h2>
          
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData(prev => ({ ...prev, tags: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., verbs, questions, interactive"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Relevant Professions (comma-separated)
              </label>
              <input
                type="text"
                value={formData.profession}
                onChange={(e) => setFormData(prev => ({ ...prev, profession: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., lawyers, doctors, business"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-4">
          <Link
            href="/activities"
            className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Creating...' : 'Create Activity'}
          </button>
        </div>
      </form>
    </div>
  )
}