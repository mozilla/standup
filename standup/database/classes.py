from math import ceil

from sqlalchemy.ext.declarative import declarative_base


Model = declarative_base(name='Model')


class Pagination(object):

    def __init__(self, query, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        self.query = query
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        return int(ceil(self.total / float(self.per_page)))

    def prev(self):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, 'a query object is required '\
                                       'for this method to work'
        return Pagination(self.query, self.page - 1, self.per_page,
                          self.query.count())

    @property
    def prev_num(self):
        """Number of the previous page."""
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.query is not None, 'a query object is required '\
                                       'for this method to work'
        return Pagination(self.query, self.page + 1, self.per_page,
                          self.query.count())

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """Iterates over the page numbers in the pagination."""
        last = 0
        for num in xrange(1, self.pages + 1):
            if (num <= left_edge or
                (num > self.page - left_current - 1 and
                 num < self.page + right_current) or
                num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num
