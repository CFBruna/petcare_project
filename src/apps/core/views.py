class AutoSchemaModelNameMixin:
    """
    A helper mixin that provides a method to get the model's verbose name.
    This is used by the CustomAutoSchema to generate dynamic summaries.
    """

    def _get_model_name(self, plural: bool = False) -> str:
        if not hasattr(self, "queryset") or self.queryset is None:
            return ""

        model = self.queryset.model
        meta = model._meta
        name = meta.verbose_name_plural if plural else meta.verbose_name
        return name.title()
