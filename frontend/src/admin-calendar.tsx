import React from 'react';
import ReactDOM from 'react-dom/client';
import AdminCalendar from './components/AdminCalendar';
import './index.css'; // Optional: Use base styles if safe, or minimal styles.

const rootElement = document.getElementById('admin-calendar-root');

if (rootElement) {
    ReactDOM.createRoot(rootElement).render(
        <React.StrictMode>
            <AdminCalendar />
        </React.StrictMode>
    );
}
