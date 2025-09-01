class AutoSchemaModelNameMixin:
    """
    A helper mixin that provides a method to get the model's verbose name.
    This is used by the CustomAutoSchema to generate dynamic summaries.
    """

    def _get_model_name(self, plural=False):
        if not hasattr(self, "queryset"):
            return ""

        model = self.queryset.model
        meta = model._meta
        name = meta.verbose_name_plural if plural else meta.verbose_name
        return name.title()
