from .utils import CoreModel, TextFieldWithInputWidget


class DataLogType(CoreModel):
    """
    Represents type of events that can be in the datasets logbook  e.g. receipt, transfer, deletion
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]

    name = TextFieldWithInputWidget(
        max_length=128, blank=False, verbose_name="Name of the type of the event"
    )

    def __str__(self):
        return f"{self.name}"
