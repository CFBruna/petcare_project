(function ($) {
    $(document).ready(function () {

        $(document.body).on('select2:select', '.select2-hidden-accessible[name$="-product"]', function (e) {
            const productSelect = e.target;
            const productId = $(productSelect).val();

            const row = $(productSelect).closest('.dynamic-form, .form-row');
            const priceInput = row.find('input[name$="-unit_price"]');

            if (productId && priceInput.length) {
                const url = `/api/v1/store/products/${productId}/price/`;

                $.ajax({
                    url: url,
                    method: 'GET',
                    success: function (data) {
                        if (data && data.price) {
                            priceInput.val(parseFloat(data.price).toFixed(2));
                        }
                    },
                    error: function (xhr, status, error) {
                        console.error('Erro ao buscar preço:', {
                            status: status,
                            error: error,
                            response: xhr.responseText
                        });
                        priceInput.val('');
                    }
                });
            } else if (priceInput.length) {
                priceInput.val('');
            }
        });
    });
})($ || django.jQuery || jQuery);
