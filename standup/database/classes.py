from math import ceil

from flask import abort
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

    def _paginate(self, page):
        if page < 1:
            abort(404)
        offset = (page - 1) * self.per_page
        items = self.query.limit(self.per_page).offset(offset).all()
        if not items and page != 1:
            abort(404)
        return Pagination(self.query, page, self.per_page,
                          self.query.count(), items)

    @property
    def pages(self):
        """The total number of pages"""
        return int(ceil(self.total / float(self.per_page)))

    def prev(self):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, ('a query object is required '
                                        'for this method to work')
        return self._paginate(self.page - 1)

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
        assert self.query is not None, ('a query object is required '
                                        'for this method to work')
        return self._paginate(self.page + 1)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1
