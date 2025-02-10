import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { subscriptionApi } from '../api/subscription';
import { CreditCard, Clock, AlertCircle } from 'lucide-react';

export default function SubscriptionPage() {
  const { data: subscription } = useQuery({
    queryKey: ['currentSubscription'],
    queryFn: () => subscriptionApi.getCurrentSubscription().then(res => res.data)
  });

  const { data: history } = useQuery({
    queryKey: ['subscriptionHistory', subscription?.id],
    queryFn: () => subscription 
      ? subscriptionApi.getSubscriptionHistory(subscription.id).then(res => res.data)
      : Promise.resolve([]),
    enabled: !!subscription
  });

  if (!subscription) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">No active subscription</h3>
        <p className="mt-2 text-sm text-gray-500">Subscribe to access premium features</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Current Subscription
            </h3>
            <span
              className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                subscription.status === 'active'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              {subscription.status}
            </span>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                    <CreditCard className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Plan Type
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {subscription.plan_type}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                    <Clock className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Valid Until
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {format(new Date(subscription.end_date), 'PP')}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-purple-500 rounded-md p-3">
                    <AlertCircle className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Auto Renewal
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {subscription.is_auto_renewable ? 'Enabled' : 'Disabled'}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {history && history.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Subscription History
            </h3>
            <div className="flow-root">
              <ul className="-mb-8">
                {history.map((event, eventIdx) => (
                  <li key={event.id}>
                    <div className="relative pb-8">
                      {eventIdx !== history.length - 1 ? (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      ) : null}
                      <div className="relative flex space-x-3">
                        <div>
                          <span className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center ring-8 ring-white">
                            <Clock className="h-5 w-5 text-white" />
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                          <div>
                            <p className="text-sm text-gray-500">
                              {event.action.charAt(0).toUpperCase() + event.action.slice(1)}
                              {event.details && (
                                <span className="font-medium text-gray-900">
                                  {' '}
                                  - {event.details.reason}
                                </span>
                              )}
                            </p>
                          </div>
                          <div className="text-right text-sm whitespace-nowrap text-gray-500">
                            {format(new Date(event.created_at), 'PP')}
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}