from pipeline.storage import PipelineMixin
from whitenoise.django import GzipManifestStaticFilesStorage


class StandupStorage(PipelineMixin, GzipManifestStaticFilesStorage):
    pass
