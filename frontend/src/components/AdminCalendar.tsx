import React, { useEffect, useState } from 'react';
import { Calendar, dateFnsLocalizer, Event as CalendarEvent, EventProps } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay, addMinutes } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import './AdminCalendar.css';

const locales = {
    'pt-BR': ptBR,
};

const localizer = dateFnsLocalizer({
    format,
    parse,
    startOfWeek,
    getDay,
    locales,
});

interface Appointment {
    id: number;
    pet_name: string;
    service_name: string;
    schedule_time: string; // ISO string
    service_duration: number; // minutes
    status: 'pending' | 'confirmed' | 'completed' | 'canceled';
}

interface MyEvent extends CalendarEvent {
    id: number;
    title: string;
    start: Date;
    end: Date;
    resource: Appointment;
}

// Event component for Day View (Single Line)
const DayEvent = ({ event }: EventProps<MyEvent>) => {
    const timeRange = `${format(event.start, 'HH:mm')} - ${format(event.end, 'HH:mm')}`;
    return (
        <div className="event-content day-layout" title={`${timeRange} | ${event.resource.pet_name} | ${event.resource.service_name}`}>
            <span className="event-time-range">{timeRange}</span>
            <span className="event-details">
                <strong>{event.resource.pet_name}</strong> - <i>{event.resource.service_name}</i>
            </span>
        </div>
    );
};

// Event component for Week/Month Views (Stacked/Multi-line)
const StackedEvent = ({ event }: EventProps<MyEvent>) => {
    return (
        <div className="event-content stacked-layout">
            <div className="event-pet">{event.resource.pet_name}</div>
            <div className="event-service">{event.resource.service_name}</div>
        </div>
    );
};

// Styles based on status
const eventStyleGetter = (event: MyEvent) => {
    let backgroundColor = '#3b82f6';
    let color = 'white';

    switch (event.resource.status) {
        case 'confirmed':
            backgroundColor = '#10b981';
            break;
        case 'pending':
            backgroundColor = '#f59e0b';
            break;
        case 'canceled':
            backgroundColor = '#ef4444';
            break;
        case 'completed':
            backgroundColor = '#6b7280';
            break;
    }

    return {
        style: {
            backgroundColor,
            color,
            border: 'none',
        },
    };
};

const AdminCalendar: React.FC = () => {
    const [events, setEvents] = useState<MyEvent[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [currentView, setCurrentView] = useState('month');

    const handleSelectEvent = (event: MyEvent) => {
        window.location.href = `/admin/schedule/appointment/${event.resource.id}/change/`;
    };

    const handleViewChange = (view: any) => {
        setCurrentView(view);
    };

    useEffect(() => {
        const fetchAppointments = async () => {
            try {
                const response = await fetch('/api/v1/schedule/appointments/');
                if (!response.ok) {
                    throw new Error('Falha ao buscar agendamentos');
                }
                const data: Appointment[] = await response.json();

                const calendarEvents: MyEvent[] = data.map((appt) => {
                    const startDate = new Date(appt.schedule_time);
                    const endDate = addMinutes(startDate, appt.service_duration || 30);

                    return {
                        id: appt.id,
                        title: `${appt.service_name} - ${appt.pet_name}`,
                        start: startDate,
                        end: endDate,
                        resource: appt,
                    };
                });

                setEvents(calendarEvents);
            } catch (error) {
                console.error("Error fetching appointments:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchAppointments();
    }, []);

    if (loading) {
        return <div className="p-4 text-center text-gray-500">Carregando calendário...</div>;
    }

    const components = {
        event: currentView === 'day' ? DayEvent : StackedEvent,
    };

    return (
        <div style={{ height: '850px', backgroundColor: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1.5rem', color: '#111827', borderLeft: '4px solid #4f46e5', paddingLeft: '12px' }}>
                Calendário de Agendamentos
            </h2>
            <Calendar
                localizer={localizer}
                events={events}
                startAccessor="start"
                endAccessor="end"
                style={{ height: 750 }}
                culture='pt-BR'
                components={components}
                onView={handleViewChange}
                defaultView='month'
                eventPropGetter={eventStyleGetter}
                onSelectEvent={handleSelectEvent}
                popup={true}
                formats={{
                    eventTimeRangeFormat: () => "",
                }}
                messages={{
                    next: "Próximo",
                    previous: "Anterior",
                    today: "Hoje",
                    month: "Mês",
                    week: "Semana",
                    day: "Dia",
                    agenda: "Agenda",
                    date: "Data",
                    time: "Hora",
                    event: "Evento",
                    noEventsInRange: "Não há agendamentos neste período.",
                    showMore: (total) => `+ ${total} mais`,
                }}
            />
        </div>
    );
};

export default AdminCalendar;
