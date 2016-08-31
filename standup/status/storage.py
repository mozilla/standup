from whitenoise.django import GzipManifestStaticFilesStorage
from pipeline.storage import PipelineMixin


class StandupStorage(PipelineMixin, GzipManifestStaticFilesStorage):
    pass
