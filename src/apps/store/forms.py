from django import forms

from .models import Brand, Category


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            normalized_name = name.strip().title()
            query = Category.objects.filter(name__iexact=normalized_name)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise forms.ValidationError("Uma categoria com este nome já existe.")
            return normalized_name
        return name


class BrandAdminForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            normalized_name = name.strip().title()
            query = Brand.objects.filter(name__iexact=normalized_name)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise forms.ValidationError("Uma marca com este nome já existe.")
            return normalized_name
        return name


class SaleItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        total_quantity_per_lot = {}

        for form in self.forms:
            if (
                not form.is_valid()
                or self.can_delete
                and self._should_delete_form(form)
            ):
                continue

            cleaned_data = form.cleaned_data
            lot = cleaned_data.get("lot")
            quantity = cleaned_data.get("quantity")

            if lot and quantity:
                total_quantity_per_lot[lot] = (
                    total_quantity_per_lot.get(lot, 0) + quantity
                )

        for lot, total_quantity in total_quantity_per_lot.items():
            if lot.quantity < total_quantity:
                raise forms.ValidationError(
                    f"Estoque insuficiente para o lote '{lot}'. "
                    f"Disponível: {lot.quantity}, Solicitado: {total_quantity}."
                )
