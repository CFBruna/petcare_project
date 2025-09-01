from drf_spectacular.openapi import AutoSchema


class CustomAutoSchema(AutoSchema):
    def get_summary(self):
        """
        Overrides the default summary generation to create dynamic summaries
        for standard ViewSet actions based on the model's verbose name.
        """
        if hasattr(self.view, "_get_model_name"):
            action = getattr(self.view, "action", "default")
            if action == "list":
                return f"List all {self.view._get_model_name(plural=True)}"
            if action == "retrieve":
                return f"Retrieve a {self.view._get_model_name()}"
            if action == "create":
                return f"Create a new {self.view._get_model_name()}"
            if action == "update":
                return f"Update a {self.view._get_model_name()}"
            if action == "partial_update":
                return f"Partially update a {self.view._get_model_name()}"
            if action == "destroy":
                return f"Delete a {self.view._get_model_name()}"

        return super().get_summary()
