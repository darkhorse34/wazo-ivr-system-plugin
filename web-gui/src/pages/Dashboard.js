import React from 'react';
import { useQuery } from 'react-query';
import { 
  Activity, 
  Workflow, 
  Volume2, 
  Server, 
  CheckCircle, 
  XCircle,
  Clock,
  Users
} from 'lucide-react';
import { getSystemStatus } from '../services/api';

const Dashboard = () => {
  const { data: status, isLoading, error } = useQuery('systemStatus', getSystemStatus);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <XCircle className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading dashboard</h3>
            <div className="mt-2 text-sm text-red-700">
              {error.message}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const stats = [
    {
      name: 'Total Flows',
      value: status?.flows?.total || 0,
      icon: Workflow,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Active Flows',
      value: status?.flows?.active || 0,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'TTS Backends',
      value: Object.values(status?.tts || {}).filter(backend => backend.available).length,
      icon: Volume2,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      name: 'Wazo Services',
      value: Object.values(status?.wazo || {}).filter(service => service.available).length,
      icon: Server,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your Wazo IVR system
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`p-3 rounded-md ${stat.bgColor}`}>
                    <stat.icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stat.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* TTS Status */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              TTS Backends
            </h3>
            <div className="space-y-3">
              {Object.entries(status?.tts || {}).map(([backend, config]) => (
                <div key={backend} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      config.available ? 'bg-green-400' : 'bg-red-400'
                    }`} />
                    <span className="text-sm font-medium text-gray-900 capitalize">
                      {backend}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {config.available ? (
                      <span className="text-green-600">Available</span>
                    ) : (
                      <span className="text-red-600">Unavailable</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Wazo Services Status */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Wazo Services
            </h3>
            <div className="space-y-3">
              {Object.entries(status?.wazo || {}).map(([service, config]) => (
                <div key={service} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      config.available ? 'bg-green-400' : 'bg-red-400'
                    }`} />
                    <span className="text-sm font-medium text-gray-900 capitalize">
                      {service}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {config.available ? (
                      <span className="text-green-600">Connected</span>
                    ) : (
                      <span className="text-red-600">Disconnected</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Activity
            </h3>
            <div className="text-sm text-gray-500">
              <div className="flex items-center">
                <Clock className="h-4 w-4 mr-2" />
                Last updated: {new Date().toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
