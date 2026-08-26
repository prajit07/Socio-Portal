import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { user, logout } = useAuth();

  const roleLabels = {
    citizen: 'Citizen',
    student: 'Student',
    faculty: 'Faculty',
    university_admin: 'University Admin',
    industry: 'Industry/Startup',
    government: 'Government',
    admin: 'Admin',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-800">Societal Innovation Portal</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                {user?.name} ({roleLabels[user?.role] || user?.role})
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-lg shadow-sm border p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome, {user?.name}!</h2>
          <p className="text-gray-600 mb-6">Your account is set up and ready to use.</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-50 p-6 rounded-lg">
              <h3 className="font-semibold text-gray-800 mb-2">Account Details</h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Email</dt>
                  <dd className="font-medium">{user?.email}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Role</dt>
                  <dd className="font-medium capitalize">{roleLabels[user?.role] || user?.role}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">User ID</dt>
                  <dd className="font-medium font-mono text-xs">{user?.id}</dd>
                </div>
              </dl>
            </div>

            <div className="bg-gray-50 p-6 rounded-lg">
              <h3 className="font-semibold text-gray-800 mb-2">Available Actions</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Submit societal problems (Citizen)</li>
                <li>• Browse and solve problems (Student/Faculty)</li>
                <li>• Manage university participation (University Admin)</li>
                <li>• Partner on solutions (Industry/Startup)</li>
                <li>• View impact dashboard (Government)</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}