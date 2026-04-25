import { TrendingUp, Award, BookOpen, Target } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const insightData = [
  { week: 'W1', avgRisk: 75, mitigated: 23 },
  { week: 'W2', avgRisk: 72, mitigated: 31 },
  { week: 'W3', avgRisk: 68, mitigated: 45 },
  { week: 'W4', avgRisk: 65, mitigated: 52 },
];

const trends = [
  {
    title: 'Flash Loan Attacks on the Rise',
    description: 'Detected 34% increase in flash loan attack patterns across major chains this month.',
    impact: 'HIGH',
    date: '2 days ago',
  },
  {
    title: 'MEV Bot Activity Surge',
    description: 'Unusual spike in MEV extraction activities on Ethereum. Recommend increased monitoring.',
    impact: 'MEDIUM',
    date: '5 days ago',
  },
  {
    title: 'Bridge Security Updates Required',
    description: 'Several cross-chain bridges showing vulnerabilities. New exploit signatures detected.',
    impact: 'HIGH',
    date: '1 week ago',
  },
];

const recommendations = [
  'Implement multi-sig wallets for high-value transactions',
  'Enable time-lock mechanisms for critical operations',
  'Monitor MEV-related activities more closely',
  'Use flashbots protect to prevent sandwich attacks',
  'Implement slippage controls on swaps',
  'Regular smart contract audits recommended',
];

export default function InsightsPage() {
  return (
    <div className="flex-1 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 px-8 py-6 bg-cyber-900/80 backdrop-blur-md border-b border-cyber-700/30">
        <div>
          <h1 className="text-3xl font-bold text-white">Insights & Analytics</h1>
          <p className="text-cyber-400 mt-1">Threat trends, recommendations, and security analytics</p>
        </div>
      </div>

      {/* Content */}
      <div className="p-8 space-y-6">
        {/* Key Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Threats Mitigated', value: '1,247', icon: Award, color: 'neon-green' },
            { label: 'Avg Risk Score', value: '42%', icon: TrendingUp, color: 'neon-blue' },
            { label: 'Security Insights', value: '156', icon: BookOpen, color: 'neon-amber' },
            { label: 'Recommendations', value: '38', icon: Target, color: 'neon-purple' },
          ].map((stat, idx) => {
            const Icon = stat.icon;
            return (
              <div key={idx} className="glass rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-cyber-400 text-sm font-medium">{stat.label}</span>
                  <Icon className={`w-5 h-5 text-neon-${stat.color}`} />
                </div>
                <div className="text-2xl font-bold text-white">{stat.value}</div>
              </div>
            );
          })}
        </div>

        {/* Trends Chart */}
        <div className="glass rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Risk Trend Analysis</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={insightData}>
              <defs>
                <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d9ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00d9ff" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorMitigated" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#39ff14" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#39ff14" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 217, 255, 0.1)" />
              <XAxis dataKey="week" stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #64748b', borderRadius: '8px' }}
                labelStyle={{ color: '#00d9ff' }}
              />
              <Area type="monotone" dataKey="avgRisk" stroke="#00d9ff" fillOpacity={1} fill="url(#colorRisk)" name="Avg Risk Score" />
              <Area type="monotone" dataKey="mitigated" stroke="#39ff14" fillOpacity={1} fill="url(#colorMitigated)" name="Threats Mitigated" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Two Column */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Threat Trends */}
          <div className="glass rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-4">Emerging Threat Patterns</h3>
            <div className="space-y-4">
              {trends.map((trend, idx) => (
                <div key={idx} className="bg-cyber-800/50 rounded-lg p-4 hover:bg-cyber-800 transition-colors border border-cyber-700/30 hover:border-cyber-600/50">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-white flex-1">{trend.title}</h4>
                    <span className={`ml-2 px-2 py-1 rounded text-xs font-bold ${
                      trend.impact === 'HIGH'
                        ? 'bg-neon-pink/20 text-neon-pink'
                        : 'bg-neon-amber/20 text-neon-amber'
                    }`}>
                      {trend.impact}
                    </span>
                  </div>
                  <p className="text-sm text-cyber-400 mb-2">{trend.description}</p>
                  <p className="text-xs text-cyber-500">{trend.date}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div className="glass rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-4">Security Recommendations</h3>
            <div className="space-y-2">
              {recommendations.map((rec, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 bg-cyber-800/50 rounded-lg hover:bg-cyber-800 transition-colors">
                  <div className="w-5 h-5 rounded-full bg-neon-green/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <div className="w-2 h-2 rounded-full bg-neon-green"></div>
                  </div>
                  <span className="text-sm text-cyber-300">{rec}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="glass rounded-lg p-6">
            <div className="text-sm text-cyber-400 mb-2">Protocol Breakdown</div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-cyber-300">Uniswap</span>
                <span className="text-neon-blue font-bold">34%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-cyber-300">AAVE</span>
                <span className="text-neon-green font-bold">28%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-cyber-300">OpenSea</span>
                <span className="text-neon-amber font-bold">22%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-cyber-300">Bridges</span>
                <span className="text-neon-pink font-bold">16%</span>
              </div>
            </div>
          </div>

          <div className="glass rounded-lg p-6">
            <div className="text-sm text-cyber-400 mb-2">Top Attack Vectors</div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-cyber-300">Flash Loans</span>
                <span className="font-bold text-cyber-200">42</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-cyber-300">Reentrancy</span>
                <span className="font-bold text-cyber-200">28</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-cyber-300">MEV</span>
                <span className="font-bold text-cyber-200">35</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-cyber-300">Bridge Exploit</span>
                <span className="font-bold text-cyber-200">18</span>
              </div>
            </div>
          </div>

          <div className="glass rounded-lg p-6">
            <div className="text-sm text-cyber-400 mb-2">Most Protected Chains</div>
            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span className="text-cyber-300">Ethereum</span>
                <span className="text-neon-green font-bold">98.5%</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-cyber-300">Base</span>
                <span className="text-neon-green font-bold">99.1%</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-cyber-300">Polygon</span>
                <span className="text-neon-green font-bold">97.2%</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-cyber-300">Arbitrum</span>
                <span className="text-neon-green font-bold">96.8%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
