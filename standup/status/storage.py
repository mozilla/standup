from pipeline.storage import PipelineMixin
from whitenoise.storage import CompressedManifestStaticFilesStorage


class StandupStorage(PipelineMixin, CompressedManifestStaticFilesStorage):
    pass
