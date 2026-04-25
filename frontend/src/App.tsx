import { useState } from 'react';
import Sidebar from './components/Sidebar';
import MainContent from './components/MainContent';
import RightPanel from './components/RightPanel';

type Page = 'dashboard' | 'monitor' | 'insights';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [selectedThreat, setSelectedThreat] = useState<string | null>(null);

  return (
    <div className="flex h-screen bg-cyber-950 text-cyber-100">
      {/* Left Sidebar - Navigation */}
      <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} />

      {/* Main Content Area */}
      <MainContent 
        page={currentPage} 
        onSelectThreat={setSelectedThreat}
      />

      {/* Right Panel - Details */}
      <RightPanel selectedThreat={selectedThreat} />
    </div>
  );
}
