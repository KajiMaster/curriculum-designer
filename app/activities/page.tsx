import Link from 'next/link'
import { Plus, Search, Filter } from 'lucide-react'

export default function ActivitiesPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Activity Library</h1>
          <p className="text-gray-600 mt-2">Manage your modular curriculum activities</p>
        </div>
        <Link 
          href="/activities/new"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <Plus size={20} />
          New Activity
        </Link>
      </div>

      <div className="flex gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search activities..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
          <Filter size={20} />
          Filters
        </button>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <div className="mb-4">
            <div className="mx-auto w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
              <Plus className="h-6 w-6 text-gray-400" />
            </div>
          </div>
          <h3 className="text-lg font-medium mb-2">No activities yet</h3>
          <p className="text-gray-400 mb-4">Create your first activity to get started with building your curriculum.</p>
          <Link 
            href="/activities/new"
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            <Plus size={16} />
            Create Activity
          </Link>
        </div>
      </div>
    </div>
  )
}