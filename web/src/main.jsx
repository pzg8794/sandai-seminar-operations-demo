import React, {useState, useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import {LayoutDashboard, GraduationCap, ArrowUpRight, Activity, BookOpen} from 'lucide-react';
import Management from './Management';
import Student from './Student';
import {repo} from './components';
import './style.css';

function App() {
  const [view, setView] = useState(location.hash === '#student' ? 'student' : 'management');
  const [studentOpened, setStudentOpened] = useState(location.hash === '#student');
  function navigate(next) {
    setView(next);
    if (next === 'student') setStudentOpened(true);
    location.hash = next;
  }
  useEffect(() => {
    const handleHash = () => {
      const next = location.hash === '#student' ? 'student' : 'management';
      setView(next);
      if (next === 'student') setStudentOpened(true);
    };
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);
  return <div className="app">
    <a className="skip-link" href="#workspace" onClick={event => {event.preventDefault(); document.getElementById('workspace').focus();}}>Skip to workspace</a>
    <aside className="sidebar">
      <a className="brand" href="#management" onClick={() => navigate('management')}><span className="brand-icon">S</span>SaNDAI<span className="brand-sub">GROWTH & LEARNING STUDIO</span></a>
      <div className="nav-label">YOUR WORKSPACE</div>
      <button className={view === 'management' ? 'active' : ''} aria-current={view === 'management' ? 'page' : undefined} onClick={() => navigate('management')}><LayoutDashboard size={19}/>Command Center</button>
      <button className={view === 'student' ? 'active' : ''} aria-current={view === 'student' ? 'page' : undefined} onClick={() => navigate('student')}><GraduationCap size={20}/>Student Career Lab</button>
      <div className="sidebar-bottom"><span className="pulse"/>Assignment prototype<p>Designed by Piter Garcia</p><a href={repo} target="_blank" rel="noreferrer">Source & notebooks<ArrowUpRight size={14}/></a></div>
    </aside>
    <main id="workspace" tabIndex={-1}>
      <header className="topbar"><span><Activity size={16}/>Learning that leads somewhere.</span><a href={`${repo}/blob/main/strategy/Piter_Garcia_SaNDAI_8_Week_Seminar_Growth_Plan.pdf`} target="_blank" rel="noreferrer"><BookOpen size={16}/>Strategy brief</a></header>
      <div className="content">
        {view === 'management' && <Management/>}
        {/* Keep the workshop mounted: navigating away must not erase a learner's work. */}
        {studentOpened && <div hidden={view !== 'student'}><Student/></div>}
        <footer>SaNDAI seminar strategy · Sample-data demonstration · No outreach or payments are executed.</footer>
      </div>
    </main>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
