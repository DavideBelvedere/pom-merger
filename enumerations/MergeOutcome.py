import enum


class MergeOutcome(enum.Enum):
    OK = 0,
    NO_OP = 1,
    SOFT_CONFLICT = 3,
    CONFLICT = 4,
    UNKNOWN = 5

    def __init__(self, code):
        self.code = code
