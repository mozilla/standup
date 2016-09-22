import markdown


HEADER_TAGS = ['h{0}'.format(i) for i in range(7)]


class NixHeaderProcessor(markdown.treeprocessors.Treeprocessor):
    """Nix headers."""
    def run(self, doc):
        for elem in doc.getiterator():
            if elem.tag in HEADER_TAGS:
                elem.tag = 'p'


class NixHeaderExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = NixHeaderProcessor()
        md.treeprocessors.add('headerid', self.processor, '>inline')


def makeExtension(configs=None):
    return NixHeaderExtension()
