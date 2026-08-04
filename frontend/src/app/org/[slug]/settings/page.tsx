'use client';
import { useState } from 'react';
import { useParams } from 'next/navigation';

export default function OrgSettingsPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [activeTab, setActiveTab] = useState('members');

  const tabs = [
    { id: 'members', label: 'Members' },
    { id: 'teams', label: 'Teams' },
    { id: 'apikeys', label: 'API Keys' },
    { id: 'audit', label: 'Audit Logs' }
  ];

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Organization Settings</h1>
          <p className="text-slate-500 mt-2">Manage settings for {slug}</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          {/* Tabs */}
          <div className="border-b border-slate-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                    }
                  `}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content area */}
          <div className="p-6">
            {activeTab === 'members' && (
              <div>
                <h2 className="text-lg font-medium text-slate-900 mb-4">Members</h2>
                <div className="bg-slate-50 rounded-lg border border-slate-200 p-8 text-center text-slate-500">
                  <p>Member management coming soon.</p>
                </div>
              </div>
            )}
            {activeTab === 'teams' && (
              <div>
                <h2 className="text-lg font-medium text-slate-900 mb-4">Teams</h2>
                <div className="bg-slate-50 rounded-lg border border-slate-200 p-8 text-center text-slate-500">
                  <p>Team management coming soon.</p>
                </div>
              </div>
            )}
            {activeTab === 'apikeys' && (
              <div>
                <h2 className="text-lg font-medium text-slate-900 mb-4">API Keys</h2>
                <div className="bg-slate-50 rounded-lg border border-slate-200 p-8 text-center text-slate-500">
                  <p>API Keys management coming soon.</p>
                </div>
              </div>
            )}
            {activeTab === 'audit' && (
              <div>
                <h2 className="text-lg font-medium text-slate-900 mb-4">Audit Logs</h2>
                <div className="bg-slate-50 rounded-lg border border-slate-200 p-8 text-center text-slate-500">
                  <p>Audit logs view coming soon.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
