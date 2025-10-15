import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Flows from './pages/Flows';
import FlowEditor from './pages/FlowEditor';
import TTS from './pages/TTS';
import Settings from './pages/Settings';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/flows" element={<Flows />} />
              <Route path="/flows/new" element={<FlowEditor />} />
              <Route path="/flows/:id" element={<FlowEditor />} />
              <Route path="/tts" element={<TTS />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </div>
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
