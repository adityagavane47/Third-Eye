import { Search, Filter, Eye, AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

interface MonitorPageProps {
  onSelectThreat: (threatId: string | null) => void;
}

const activityData = [
  { hour: '00', volume: 45, blocked: 8 },
  { hour: '04', volume: 62, blocked: 12 },
  { hour: '08', volume: 89, blocked: 18 },
  { hour: '12', volume: 108, blocked: 25 },
  { hour: '16', volume: 95, blocked: 22 },
  { hour: '20', volume: 71, blocked: 14 },
  { hour: '23', volume: 38, blocked: 6 },
];

const monitoredAddresses = [
  { address: '0x742d35Cc6634C0532925a3b844Bc91e6a39e3fa3', activity: 'High', status: '🔴 Active', transactions: 1247, lastActivity: '2 min ago' },
  { address: '0x1234567890123456789012345678901234567890', activity: 'Medium', status: '🟡 Monitoring', transactions: 342, lastActivity: '15 min ago' },
  { address: '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd', activity: 'High', status: '🔴 Flagged', transactions: 892, lastActivity: '45 min ago' },
  { address: '0xfedcbafedcbafedcbafedcbafedcbafedcbafed', activity: 'Low', status: '🟢 Clean', transactions: 23, lastActivity: '3 hours ago' },
  { address: '0x9876543210987654321098765432109876543210', activity: 'Medium', status: '🟡 Warning', transactions: 567, lastActivity: '1 hour ago' },
];

const protectedChains = [
  { name: 'Ethereum', protected: '98.5%', addresses: 2341, threats: 23 },
  { name: 'Polygon', protected: '97.2%', addresses: 1856, threats: 18 },
  { name: 'Base', protected: '99.1%', addresses: 892, threats: 8 },
  { name: 'Arbitrum', protected: '96.8%', addresses: 1204, threats: 31 },
  { name: 'Optimism', protected: '98.3%', addresses: 678, threats: 12 },
];

export default function MonitorPage({ onSelectThreat }: MonitorPageProps) {
  return (
    <div className="flex-1 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 px-8 py-6 bg-cyber-900/80 backdrop-blur-md border-b border-cyber-700/30">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Monitor</h1>
            <p className="text-cyber-400 mt-1">Real-time tracking of addresses and chains</p>
          </div>
        </div>
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-cyber-400" />
            <input
              type="text"
              placeholder="Search addresses, transactions, chains..."
              className="w-full pl-10 pr-4 py-2 bg-cyber-800/50 border border-cyber-700/50 rounded-lg text-cyber-100 placeholder-cyber-500 focus:outline-none focus:border-neon-blue/50"
            />
          </div>
          <button className="px-4 py-2 rounded-lg bg-cyber-800/50 text-cyber-300 hover:bg-cyber-700 border border-cyber-700/50 transition-colors flex items-center gap-2">
            <Filter className="w-4 h-4" />
            Filter
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-8 space-y-6">
        {/* Activity Overview */}
        <div className="glass rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Activity Overview</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 217, 255, 0.1)" />
              <XAxis dataKey="hour" stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #64748b', borderRadius: '8px' }}
                labelStyle={{ color: '#00d9ff' }}
              />
              <Bar dataKey="volume" stackId="a" fill="#00d9ff" />
              <Bar dataKey="blocked" stackId="a" fill="#ff006e" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Monitored Addresses */}
          <div className="lg:col-span-2 glass rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Monitored Addresses</h3>
              <button className="text-sm text-neon-blue hover:text-neon-blue/80">Add Address →</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-cyber-700/50">
                    <th className="text-left py-3 px-4 text-cyber-400 font-semibold">Address</th>
                    <th className="text-left py-3 px-4 text-cyber-400 font-semibold">Status</th>
                    <th className="text-center py-3 px-4 text-cyber-400 font-semibold">Transactions</th>
                    <th className="text-left py-3 px-4 text-cyber-400 font-semibold">Last Activity</th>
                    <th className="text-center py-3 px-4 text-cyber-400 font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {monitoredAddresses.map((item, idx) => (
                    <tr key={idx} className="border-b border-cyber-700/30 hover:bg-cyber-800/50 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-mono text-neon-blue text-xs">{item.address.slice(0, 10)}...{item.address.slice(-8)}</span>
                      </td>
                      <td className="py-3 px-4">{item.status}</td>
                      <td className="py-3 px-4 text-center text-cyber-300">{item.transactions.toLocaleString()}</td>
                      <td className="py-3 px-4 text-cyber-400">{item.lastActivity}</td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => onSelectThreat('threat-1')}
                          className="text-neon-blue hover:text-neon-blue/80 inline-flex items-center gap-1"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Chain Protection */}
          <div className="glass rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-4">Chain Protection</h3>
            <div className="space-y-4">
              {protectedChains.map((chain, idx) => (
                <div key={idx} className="bg-cyber-800/50 rounded-lg p-3 hover:bg-cyber-800 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-cyber-100">{chain.name}</span>
                    <span className="text-neon-green font-bold">{chain.protected}</span>
                  </div>
                  <div className="w-full bg-cyber-700 rounded-full h-2 overflow-hidden mb-2">
                    <div
                      className="h-full bg-gradient-to-r from-neon-green to-neon-blue"
                      style={{ width: chain.protected }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs text-cyber-400">
                    <span>{chain.addresses} Addresses</span>
                    <span className="text-neon-pink">{chain.threats} Threats</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Alert Settings */}
        <div className="glass rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="w-6 h-6 text-neon-amber" />
            <h3 className="text-lg font-bold text-white">Alert Configuration</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'Critical Alerts', status: 'Enabled', icon: '🔴' },
              { label: 'High Priority', status: 'Enabled', icon: '🟠' },
              { label: 'Notifications', status: 'Enabled', icon: '🔔' },
            ].map((alert, idx) => (
              <div key={idx} className="bg-cyber-800/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{alert.icon}</span>
                  <span className="font-semibold text-cyber-100">{alert.label}</span>
                </div>
                <span className="text-sm text-neon-green">{alert.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
