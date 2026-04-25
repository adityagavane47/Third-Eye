import Dashboard from "./pages/Dashboard";

export default function App() {
  // Dev mode: render Dashboard directly — no Privy appId needed
  // To enable Web3 auth, add VITE_PRIVY_APP_ID to your .env and
  // wrap <Dashboard /> with <PrivyProvider> here.
  return <Dashboard />;
}
