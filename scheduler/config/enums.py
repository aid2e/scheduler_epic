from enum import Enum


class JobType(str, Enum):
    SINGULARITY = "singularity"
    INTERACTIVE = "interactive"


class ProblemType(str, Enum):
    EIC_MOO = "EIC_MOO"
    CLOSURE_MOO = "CLOSURE_MOO"
