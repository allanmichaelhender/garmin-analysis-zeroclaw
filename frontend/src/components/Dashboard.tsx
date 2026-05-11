import { mockActivities } from '../data/mockActivities';

export default function Dashboard() {
  const totalActivities = mockActivities.length;
  const totalDistance = mockActivities.reduce((sum, a) => sum + a.distance, 0) / 1000;
  const avgHR = Math.round(mockActivities.reduce((sum, a) => sum + a.avgHR, 0) / totalActivities);

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8">Garmin Analysis Dashboard</h1>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-900 rounded-lg shadow-lg p-6 border border-gray-800">
            <h3 className="text-lg font-semibold text-gray-300">Total Activities</h3>
            <p className="text-3xl font-bold text-blue-400 mt-2">{totalActivities}</p>
          </div>
          <div className="bg-gray-900 rounded-lg shadow-lg p-6 border border-gray-800">
            <h3 className="text-lg font-semibold text-gray-300">Total Distance</h3>
            <p className="text-3xl font-bold text-green-400 mt-2">{totalDistance.toFixed(1)} km</p>
          </div>
          <div className="bg-gray-900 rounded-lg shadow-lg p-6 border border-gray-800">
            <h3 className="text-lg font-semibold text-gray-300">Avg Heart Rate</h3>
            <p className="text-3xl font-bold text-red-400 mt-2">{avgHR} bpm</p>
          </div>
        </div>

        {/* Recent Activities */}
        <div className="bg-gray-900 rounded-lg shadow-lg p-6 border border-gray-800">
          <h2 className="text-2xl font-bold text-white mb-4">Recent Activities</h2>
          <div className="space-y-4">
            {mockActivities.map((activity) => (
              <div key={activity.id} className="border-b border-gray-800 pb-4 last:border-0">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-white capitalize">{activity.type}</h3>
                    <p className="text-sm text-gray-400">{activity.date}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-white">{(activity.distance / 1000).toFixed(1)} km</p>
                    <p className="text-sm text-gray-400">{Math.floor(activity.duration / 60)} min</p>
                  </div>
                </div>
                <div className="flex gap-4 mt-2 text-sm text-gray-400">
                  <span>Avg HR: {activity.avgHR} bpm</span>
                  <span>Max HR: {activity.maxHR} bpm</span>
                  <span>Pace: {activity.pace} /km</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-center text-gray-500 mt-8 text-sm">
          Static showcase - no backend connection
        </p>
      </div>
    </div>
  );
}
