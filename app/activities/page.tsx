import Link from 'next/link'
import { prisma } from '@/lib/db'
import { ActivityCategory, DifficultyLevel } from '@prisma/client'

async function getActivities() {
  // During build time, return empty array to avoid database connection issues
  if (process.env.NODE_ENV === 'production' && !process.env.POSTGRES_PRISMA_URL) {
    return []
  }
  
  try {
    const activities = await prisma.activity.findMany({
      where: { isArchived: false },
      orderBy: { createdAt: 'desc' },
      take: 20
    })
    return activities
  } catch (error) {
    console.error('Database error:', error)
    return []
  }
}

const categoryColors: Record<ActivityCategory, string> = {
  GRAMMAR: 'bg-blue-100 text-blue-800',
  VOCABULARY: 'bg-green-100 text-green-800',
  SPEAKING: 'bg-purple-100 text-purple-800',
  LISTENING: 'bg-yellow-100 text-yellow-800',
  READING: 'bg-red-100 text-red-800',
  WRITING: 'bg-indigo-100 text-indigo-800',
  PRONUNCIATION: 'bg-pink-100 text-pink-800',
  BUSINESS: 'bg-gray-100 text-gray-800',
  CONVERSATION: 'bg-orange-100 text-orange-800',
  CULTURE: 'bg-teal-100 text-teal-800'
}

const difficultyColors: Record<DifficultyLevel, string> = {
  BEGINNER: 'bg-green-50 border-green-200 text-green-700',
  INTERMEDIATE: 'bg-yellow-50 border-yellow-200 text-yellow-700',
  ADVANCED: 'bg-red-50 border-red-200 text-red-700'
}

export default async function ActivitiesPage() {
  const activities = await getActivities()

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Activity Library</h1>
          <p className="text-gray-600 mt-2">Manage your modular curriculum activities</p>
        </div>
        <Link 
          href="/activities/new"
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          Create Activity
        </Link>
      </div>

      {activities.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📚</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No activities yet</h3>
          <p className="text-gray-600 mb-6">Create your first modular activity to get started</p>
          <Link 
            href="/activities/new"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Create Your First Activity
          </Link>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {activities.map((activity) => (
            <div key={activity.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {activity.title}
                </h3>
                <span className={`px-2 py-1 text-xs rounded-full font-medium ${difficultyColors[activity.difficulty]}`}>
                  {activity.difficulty}
                </span>
              </div>
              
              <p className="text-gray-600 text-sm mb-4">
                {activity.description}
              </p>

              <div className="flex items-center justify-between mb-4">
                <span className={`px-2 py-1 text-xs rounded-full font-medium ${categoryColors[activity.category]}`}>
                  {activity.category}
                </span>
                <span className="text-sm text-gray-500">
                  {activity.typicalDuration} min
                </span>
              </div>

              <div className="flex justify-between items-center">
                <div className="text-xs text-gray-500">
                  {activity.objectives.length} objectives
                </div>
                <Link 
                  href={`/activities/${activity.id}`}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  View Details →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}