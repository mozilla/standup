from pipeline.conf import settings
from pipeline.compressors import SubProcessCompressor


class CleanCSSCompressor(SubProcessCompressor):
    def compress_css(self, css):
        return self.execute_command([settings.CLEANCSS_BINARY], css)
