import DashboardPage from './pages/DashboardPage';
import MonitorPage from './pages/MonitorPage';
import InsightsPage from './pages/InsightsPage';

interface MainContentProps {
  page: 'dashboard' | 'monitor' | 'insights';
  onSelectThreat: (threatId: string | null) => void;
}

export default function MainContent({ page, onSelectThreat }: MainContentProps) {
  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-gradient-cyber">
      {page === 'dashboard' && <DashboardPage onSelectThreat={onSelectThreat} />}
      {page === 'monitor' && <MonitorPage onSelectThreat={onSelectThreat} />}
      {page === 'insights' && <InsightsPage />}
    </div>
  );
}
