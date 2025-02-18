from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "prev": self.page.number - 1 if self.page.has_previous() else None,
                "next": self.page.number + 1 if self.page.has_next() else None,
                "results": data,
            }
        )

    def get_page_number(self, request, paginator):
        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number == "last":
            page_number = paginator.num_pages
        return page_number
