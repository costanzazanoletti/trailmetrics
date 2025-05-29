import { createRoot } from 'react-dom/client';
import './styles/index.css';
import 'leaflet/dist/leaflet.css';
import './assets/weather-icons/css/weather-icons.min.css';
import App from './App.tsx';

createRoot(document.getElementById('root')!).render(<App />);
