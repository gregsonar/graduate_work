import { useQuery } from '@tanstack/react-query';
import { authApi } from '../api/auth';
import { Shield } from 'lucide-react';

export default function ProfilePage() {
  const { data: user } = useQuery({
    queryKey: ['currentUser'],
    queryFn: () => authApi.getCurrentUser().then(res => res.data)
  });

  const { data: socialAccounts } = useQuery({
    queryKey: ['socialAccounts'],
    queryFn: () => authApi.getSocialAccounts().then(res => res.data.accounts)
  });

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Profile Information</h3>
        
        <div className="mt-5 border-t border-gray-200">
          <dl className="divide-y divide-gray-200">
            <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-gray-500">Username</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {user?.username}
              </dd>
            </div>
            
            <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-gray-500">Email</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {user?.email || 'Not provided'}
              </dd>
            </div>

            <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-gray-500">Roles</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                <div className="flex flex-wrap gap-2">
                  {user?.roles.map(role => (
                    <span
                      key={role}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      <Shield className="w-3 h-3 mr-1" />
                      {role}
                    </span>
                  ))}
                </div>
              </dd>
            </div>
          </dl>
        </div>

        {socialAccounts && socialAccounts.length > 0 && (
          <div className="mt-6">
            <h4 className="text-lg font-medium text-gray-900">Connected Accounts</h4>
            <div className="mt-4 space-y-4">
              {socialAccounts.map(account => (
                <div
                  key={account.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center">
                    {account.avatar_url && (
                      <img
                        src={account.avatar_url}
                        alt={account.social_username || ''}
                        className="w-10 h-10 rounded-full"
                      />
                    )}
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">
                        {account.social_username || account.social_id}
                      </p>
                      <p className="text-sm text-gray-500">
                        {account.provider.toUpperCase()}
                      </p>
                    </div>
                  </div>
                  {account.is_primary && (
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      Primary
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}