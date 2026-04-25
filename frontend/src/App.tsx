<<<<<<< HEAD
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
=======
import Dashboard from "./pages/Dashboard";

export default function App() {
  // Dev mode: render Dashboard directly — no Privy appId needed
  // To enable Web3 auth, add VITE_PRIVY_APP_ID to your .env and
  // wrap <Dashboard /> with <PrivyProvider> here.
  return <Dashboard />;
>>>>>>> 65e87a86fe53cf5d1271775aed34951c2454a04c
}
