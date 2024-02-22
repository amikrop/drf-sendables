from sendables.core.models import Sendable
from sendables.core.utils import conditionally_concrete


@conditionally_concrete
class Notice(Sendable):
    class Meta:
        abstract = True
