from .base_dto import BaseDTO


class ExternalTaskDTO(BaseDTO):
    """
    Data Transfer Object (DTO) for Camunda External Task
    """

    def __init__(self, **kwargs):
        super().__init__(
            # Note: NDA, reimplement properties
            properties=[],
            record=kwargs
        )
