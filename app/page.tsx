export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">
          Curriculum Designer
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          AI-powered modular curriculum management for English teachers
        </p>
        
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold text-green-800 mb-4">
            🎉 Deployment Successful!
          </h2>
          <div className="text-left space-y-2">
            <div className="flex items-center">
              <span className="text-green-600 mr-2">✅</span>
              <span>Next.js 14 with TypeScript</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-600 mr-2">✅</span>
              <span>AWS Lambda deployment pipeline</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-600 mr-2">✅</span>
              <span>PostgreSQL database connected</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-600 mr-2">✅</span>
              <span>Terraform infrastructure (AWS)</span>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-2xl font-semibold text-blue-800 mb-4">
            🚀 Start Building Your Curriculum
          </h2>
          <p className="text-blue-700 mb-6">
            Your Modular Curriculum Management System is ready! Begin by creating activities for your lessons.
          </p>
          <div className="flex gap-4">
            <a 
              href="/activities"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Activity Library →
            </a>
            <div className="text-blue-600 font-medium flex items-center">
              Activity Library → Lesson Builder → AI Integration
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}