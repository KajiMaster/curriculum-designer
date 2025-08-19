import Link from 'next/link'

// Temporary simplified version for debugging deployment issues
export default function ActivitiesPage() {
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

      <div className="text-center py-12">
        <div className="text-6xl mb-4">📚</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Activity Library Coming Soon</h3>
        <p className="text-gray-600 mb-6">The database integration is being set up</p>
        <Link 
          href="/"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          Back to Home
        </Link>
      </div>
    </div>
  )
}