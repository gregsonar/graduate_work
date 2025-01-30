from rest_framework import pagination
from rest_framework.response import Response


class TotalPagesCountPaginator(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(
            {
                'links': {
                    'next': self.get_next_link(),
                    'prev': self.get_previous_link(),
                },
                'next': self.page.next_page_number()
                if self.page.has_next()
                else None,
                'prev': self.page.previous_page_number()
                if self.page.has_previous()
                else None,
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'results': data,
            }
        )
