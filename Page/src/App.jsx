import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Main from './Pages/Main';
import Tools from './Pages/Tools';
import './styles/tools.css';
import './styles/poi-verifier.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Main />} />
        <Route path="/tools" element={<Tools />} />
      </Routes>
    </Router>
  )
}

export default App
