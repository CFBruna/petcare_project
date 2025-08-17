console.log("Arquivo schedule_admin.js carregado com sucesso!");

document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM está pronto. Procurando o formulário de agendamento...");

    if (document.getElementById('appointment_form')) {
        console.log("Formulário encontrado! Procurando os campos de serviço e data...");

        const serviceSelect = document.getElementById('id_service');
        const dateInput = document.getElementById('id_appointment_date');
        const timeSelect = document.getElementById('id_appointment_time');

        console.log("Elemento do Serviço:", serviceSelect);
        console.log("Elemento da Data:", dateInput);

        if (!serviceSelect || !dateInput || !timeSelect) {
            console.error("ERRO CRÍTICO: Um ou mais campos (serviço, data ou hora) não foram encontrados no HTML! Verifique os IDs no forms.py e admin.py.");
            return;
        }

        console.log("Todos os campos foram encontrados. Adicionando 'escutadores' de eventos.");

        const fetchAvailableSlots = () => {

            console.log("EVENTO DISPARADO! A função fetchAvailableSlots foi chamada.");

            const serviceId = serviceSelect.value;
            const date = dateInput.value;

            if (!serviceId || !date) {
                console.log("Serviço ou data não preenchidos. Abortando busca.");
                return;
            }

            timeSelect.disabled = true;
            timeSelect.innerHTML = '<option value="">Buscando horários...</option>';
            console.log(`Buscando horários para o serviço ${serviceId} na data ${date}`);

            const url = `/api/v1/schedule/available-slots/?date=${date}&service_id=${serviceId}`;

            fetch(url)
                .then(response => response.json())
                .then(slots => {
                    console.log("API respondeu com:", slots);
                    timeSelect.innerHTML = '';

                    if (slots && slots.length > 0) {
                        timeSelect.innerHTML = '<option value="">---------</option>';
                        slots.forEach(slot => {
                            const option = new Option(slot, slot);
                            timeSelect.add(option);
                        });
                    } else {
                        timeSelect.innerHTML = '<option value="">Nenhum horário disponível</option>';
                    }
                })
                .catch(error => {
                    console.error("ERRO na chamada da API:", error);
                    timeSelect.innerHTML = '<option value="">Erro ao buscar horários</option>';
                })
                .finally(() => {
                    timeSelect.disabled = false;
                });
        };

        serviceSelect.addEventListener('change', fetchAvailableSlots);
        dateInput.addEventListener('blur', fetchAvailableSlots);

        console.log("Escutadores de eventos adicionados com sucesso.");

    } else {
        console.log("Formulário de agendamento não encontrado nesta página.");
    }
});
