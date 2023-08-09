from formtools.wizard.views import NamedUrlSessionWizardView
from urllib.parse import urlencode


class DaisyWizard(NamedUrlSessionWizardView):
    def dispatch(self, request, *args, **kwargs):
        """
        Hook method to get parameters from the url.
        Used to prefill wizard.
        """
        response = super().dispatch(request, *args, **kwargs)

        # get querystring from get parameters if any
        querystring = request.GET.copy()
        querystring.pop("reset", {})
        # store them in the wizard storage
        extra_data = self.storage.extra_data.get("querystring", {})
        extra_data.update(querystring)
        self.storage.extra_data = {"querystring": extra_data}
        return response

    def _update_context_from_request(self, context, param):
        """
        Utility function.
        Update context based on the query parameters
        present on the wizard storage
        """
        if param in self.storage.extra_data.get("querystring", {}):
            try:
                context.update({param: self.storage.extra_data["querystring"][param]})
            except Exception:
                pass

    def get_template_names(self):
        return ["wizard.html"]

    def get_context_data(self, form, **kwargs):
        """
        Put query string parameters in the URL to keep them
        between steps (remove reset param)
        """
        context = super().get_context_data(form=form, **kwargs)
        querystring = self.storage.extra_data.get("querystring", False)
        if querystring:
            querystring = {k: v[0] for k, v in querystring.items()}
            context.update({"querystring": urlencode(querystring)})
        return context
