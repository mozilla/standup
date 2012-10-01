from weakref import WeakKeyDictionary
from jinja2 import contextfunction
from jinja2.ext import Extension, nodes


class IfChangedExtension(Extension):
    """An extension that implements ifchanged (like in django) for Jinja2"""
    tags = set(['ifchanged'])

    _buffered_data = WeakKeyDictionary()

    def parse(self, parser):
        # get the line number of our tag and skip the "ifchanged" name
        lineno = parser.stream.next().lineno
        # create the arguments for our "_if_changed" method on our extension.
        # it only gets one constant argument that is a (not that unique, but
        # good enough for this example) key it uses to buffer the ifchanged body
        args = [nodes.Const(parser.free_identifier().name,
            lineno=lineno)]
        # parse everything up to endifchanged and drop the "endifchange" name
        # (the needle)
        body = parser.parse_statements(['name:endifchanged'],
            drop_needle=True)
        # create a callblock node that calls "_if_changed" with the arguments
        # from above.  The callblock passes a function to the function as
        # "caller" keyword argument that renders the body.
        return nodes.CallBlock(self.call_method('_if_changed', args),
            [], [], body).set_lineno(lineno)

    @contextfunction
    def _if_changed(self, context, key, caller):
        """The if-changed callback.  Because it's a contextfunction it also
        gets the context as first argument.
        """
        try:
            buffers = self._buffered_data[context]
        except KeyError:
            self._buffered_data[context] = buffers = {}
        body = caller()
        if key not in buffers or buffers[key] != body:
            rv = body
        else:
            rv = u''
        buffers[key] = body
        return rv