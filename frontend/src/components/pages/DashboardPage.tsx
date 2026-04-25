import { AlertCircle, TrendingUp, Shield, Zap } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface DashboardPageProps {
  onSelectThreat: (threatId: string | null) => void;
}

const chartData = [
  { time: '00:00', threats: 12, score: 85 },
  { time: '04:00', threats: 19, score: 80 },
  { time: '08:00', threats: 28, score: 75 },
  { time: '12:00', threats: 35, score: 70 },
  { time: '16:00', threats: 42, score: 65 },
  { time: '20:00', threats: 38, score: 72 },
  { time: '23:59', threats: 25, score: 80 },
];

const riskData = [
  { name: 'Critical', value: 12, color: '#ff006e' },
  { name: 'High', value: 34, color: '#fbbf24' },
  { name: 'Medium', value: 58, color: '#00d9ff' },
  { name: 'Low', value: 743, color: '#39ff14' },
];

const threats = [
  { id: 'threat-1', name: 'Suspicious Token Transfer', severity: 'CRITICAL', risk: 92, time: '2 min ago', chain: 'ETH' },
  { id: 'threat-2', name: 'Flash Loan Attack Pattern', severity: 'HIGH', risk: 78, time: '15 min ago', chain: 'POLY' },
  { id: 'threat-3', name: 'Bridge Exploit Detection', severity: 'HIGH', risk: 85, time: '45 min ago', chain: 'BASE' },
  { id: 'threat-4', name: 'MEV Bot Activity', severity: 'MEDIUM', risk: 62, time: '1 hr ago', chain: 'ETH' },
];

export default function DashboardPage({ onSelectThreat }: DashboardPageProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'text-neon-pink bg-neon-pink/10 border-neon-pink/30';
      case 'HIGH':
        return 'text-neon-amber bg-neon-amber/10 border-neon-amber/30';
      case 'MEDIUM':
        return 'text-neon-blue bg-neon-blue/10 border-neon-blue/30';
      default:
        return 'text-neon-green bg-neon-green/10 border-neon-green/30';
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 px-8 py-6 bg-cyber-900/80 backdrop-blur-md border-b border-cyber-700/30">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Security Dashboard</h1>
            <p className="text-cyber-400 mt-1">Real-time threat monitoring and analysis</p>
          </div>
          <div className="flex gap-3">
            <button className="px-4 py-2 rounded-lg bg-cyber-800/50 text-cyber-300 hover:bg-cyber-700 border border-cyber-700/50 transition-colors text-sm font-medium">
              Refresh
            </button>
            <button className="px-4 py-2 rounded-lg bg-neon-blue/20 text-neon-blue hover:bg-neon-blue/30 border border-neon-blue/50 transition-colors text-sm font-medium">
              Export Report
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-8 space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Threats', value: '847', change: '+12%', icon: AlertCircle, color: 'neon-pink' },
            { label: 'Security Score', value: '92%', change: '+5%', icon: Shield, color: 'neon-blue' },
            { label: 'Wallets Protected', value: '15.2K', change: '+342', icon: Zap, color: 'neon-green' },
            { label: 'Active Monitors', value: '238', change: '+18', icon: TrendingUp, color: 'neon-amber' },
          ].map((metric, idx) => {
            const Icon = metric.icon;
            return (
              <div key={idx} className="glass rounded-lg p-4 hover:bg-cyber-900/60 hover:border-cyber-600/50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-cyber-400 text-sm font-medium">{metric.label}</span>
                  <Icon className={`w-5 h-5 text-neon-${metric.color}`} />
                </div>
                <div className="flex items-end gap-2">
                  <div className="text-2xl font-bold text-white">{metric.value}</div>
                  <span className={`text-xs font-semibold text-neon-${metric.color}`}>{metric.change}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Threat Timeline */}
          <div className="lg:col-span-2 glass rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-4">Threat Timeline</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 217, 255, 0.1)" />
                <XAxis dataKey="time" stroke="#94a3b8" style={{ fontSize: '12px' }} />
                <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #64748b', borderRadius: '8px' }}
                  labelStyle={{ color: '#00d9ff' }}
                />
                <Line
                  type="monotone"
                  dataKey="threats"
                  stroke="#ff006e"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Risk Distribution */}
          <div className="glass rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-4">Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #64748b', borderRadius: '8px' }}
                  labelStyle={{ color: '#00d9ff' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 mt-4">
              {riskData.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className="text-cyber-400">{item.name}</span>
                  <span className="font-bold text-white">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Threats */}
        <div className="glass rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-white">Recent Threats</h3>
            <button className="text-sm text-neon-blue hover:text-neon-blue/80">View All →</button>
          </div>
          <div className="space-y-3">
            {threats.map((threat) => (
              <button
                key={threat.id}
                onClick={() => onSelectThreat(threat.id)}
                className="w-full p-4 glass-hover rounded-lg text-left"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-semibold text-white hover:text-neon-blue">{threat.name}</h4>
                      <div className={`px-2 py-1 rounded text-xs font-bold border ${getSeverityColor(threat.severity)}`}>
                        {threat.severity}
                      </div>
                      <span className="text-xs text-cyber-400">{threat.chain}</span>
                    </div>
                    <p className="text-sm text-cyber-400">{threat.time}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-neon-pink">{threat.risk}</div>
                    <div className="text-xs text-cyber-400">Risk Score</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
