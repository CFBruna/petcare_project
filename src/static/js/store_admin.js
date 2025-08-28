(function ($) {
    $(document).ready(function () {
        const formsetPrefix = 'items';
        const inlineGroupId = `#${formsetPrefix}-group`;
        const rowSelector = `.dynamic-${formsetPrefix}`;

        function updateTotal() {
            let total = 0;
            $(inlineGroupId).find(rowSelector).not('.deleted').each(function () {
                const row = $(this);
                const quantity = parseFloat(row.find('input[name$="-quantity"]').val()) || 0;
                const price = parseFloat(row.find('input[name$="-unit_price"]').val()) || 0;
                total += quantity * price;
            });

            const totalValueField = $('.field-total_value .readonly');
            if (totalValueField.length) {
                totalValueField.text(total.toFixed(2).replace('.', ','));
            }
        }
        $(inlineGroupId).on('change keyup', 'input[name$="-quantity"], input[name$="-unit_price"]', function () {
            updateTotal();
        });
        $(document).on('formset:added', function (event, $row, formsetName) {
            if (formsetName === formsetPrefix) {
                updateTotal();
            }
        });

        $(document).on('formset:removed', function (event, $row, formsetName) {
            if (formsetName === formsetPrefix) {
                updateTotal();
            }
        });
        $(document.body).on('select2:select', '.select2-hidden-accessible[name$="-lot"]', function (e) {
            const lotSelect = e.target;
            const lotId = $(lotSelect).val();
            const row = $(lotSelect).closest(rowSelector);
            const priceInput = row.find('input[name$="-unit_price"]');

            if (lotId && priceInput.length) {
                const url = `/api/v1/store/lots/${lotId}/price/`;
                $.ajax({
                    url: url,
                    method: 'GET',
                    success: function (data) {
                        if (data && data.price) {
                            priceInput.val(parseFloat(data.price).toFixed(2));
                            priceInput.trigger('change');
                        }
                    },
                    error: function (xhr) {
                        priceInput.val('');
                        priceInput.trigger('change');
                    }
                });
            }
        });


        updateTotal();
    });
})($ || django.jQuery || jQuery);
