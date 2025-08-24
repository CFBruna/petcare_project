from django import forms


class SaleItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        total_quantity_per_product = {}

        for form in self.forms:
            if not form.is_valid() or form in self.deleted_forms:
                continue

            cleaned_data = form.cleaned_data
            product = cleaned_data.get("product")
            quantity = cleaned_data.get("quantity")

            if product and quantity:
                total_quantity_per_product[product] = (
                    total_quantity_per_product.get(product, 0) + quantity
                )

        for product, total_quantity in total_quantity_per_product.items():
            if product.stock < total_quantity:
                raise forms.ValidationError(
                    f"Estoque insuficiente para o produto '{product.name}'. "
                    f"Disponível: {product.stock}, Solicitado: {total_quantity}."
                )
