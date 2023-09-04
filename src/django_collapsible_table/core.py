from typing import Any, Dict
from django.template.loader import render_to_string
from logging import getLogger

from django.db.models.query import QuerySet
from django.views.generic import TemplateView
from django.http import HttpRequest, HttpResponse

log = getLogger(__name__)


class QuerySetNotDefined(Exception):
    pass


class CollapsibleTable:
    qs = None
    # fields = [
    #     {"name": "Id", "header_css_class": "col-2"},
    #     "name",
    #     "state",
    #     "ident",
    #     "unit",
    #     "state",
    # ]
    header = None

    table_css_class = "table"
    expand_header_css_class = "col-1"
    sort = None

    @property
    def field_names(self):
        fNames = []
        for field in self.fields:
            fNames.append(field["name"].lower())
        return fNames

    def __init__(self, data=None, fields=None, sort=None) -> None:
        self.qs = data if data is not None else self.get_queryset()
        self.qs = self.sort_queryset(sort)

        if not hasattr(self, "child_table_class"):
            self.child_table_class = self.__class__

        if fields is not None:
            self.fields = fields

    def _default_fields(self):
        self.fields = []
        for field in list(self.qs.values()[0]):
            self.fields.append(
                {
                    "name": field.capitalize(),
                    "header_css_class": "col-3",
                    "sortable": True,
                }
            )

    def sort_queryset(self, key) -> QuerySet[Any]:
        self.sort = key

        sort_func = getattr(self, f"sort_{key}", None)
        if sort_func is not None:
            return sort_func(self.qs)
        else:
            return self.qs.order_by(key)

    def get_fields(self):
        if not hasattr(self, "fields"):
            self._default_fields()
        else:
            if "__all__" in self.fields:
                self._default_fields()
            else:
                temp = []
                for field in self.fields:
                    if isinstance(field, dict):
                        if not "header_css_class" in field:
                            field.update({"header_css_class": "col-3"})

                        if not "sortable" in field:
                            field.update({"sortable": True})

                        temp.append(field)
                    else:
                        temp.append(
                            {
                                "name": field.capitalize(),
                                "header_css_class": "col-3",
                                "sortable": True,
                            }
                        )

                self.fields = temp

    def render_header(self):
        return render_to_string(
            "collapsible_table/header.html", context={"fields": self.fields}
        )

    def render_rows(self):
        rows = []

        fNames = self.field_names
        num_cols = len(fNames)

        for row in self.qs:
            log.debug(f"Rendering {row}")
            row.items = []
            for field in fNames:
                if hasattr(self, f"render_{field}"):
                    item = getattr(self, f"render_{field}")(row)
                elif hasattr(row, f"render_{field}"):
                    item = getattr(row, f"render_{field}")()
                else:
                    item = getattr(row, field, None)

                if item is not None:
                    row.items.append(
                        {"name": field, "value": item, "header_css_class": "m-1"}
                    )
                else:
                    row.items.append(None)

            child_qs = self.get_child_queryset(row)
            if child_qs is not None:
                row.child_table = self.child_table_class(data=child_qs).render()
            else:
                row.child_table = None

            rows.append(row)
        return rows

    def render(self):
        self.get_fields()

        return render_to_string(
            "collapsible_table/table.html",
            context={
                "table_css_class": self.table_css_class,
                "expand_header_css_class": self.expand_header_css_class,
                "fields": self.fields,
                "rows": self.render_rows(),
                "child_col_span": len(self.field_names) + 1,
                "sorting_field": self.sort,
            },
        )

    def get_queryset(self) -> QuerySet[Any]:
        raise QuerySetNotDefined
        pass

    def get_child_queryset(self, record) -> QuerySet[Any]:
        return None


class CollapsibleTableMixin:
    template_name = None
    template_hx = "collapsible_table/hx_table.html"

    table_class = None
    filterset_class = None
    model = None
    qs: QuerySet = None
    sort = None

    _table = None

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        request.session.set_expiry(0)

        if not "sort" in request.session:
            request.session["sort"] = None

        if "sort" in request.GET:
            request.session["sort"] = request.GET["sort"].lower()

        self.sort = request.session["sort"]

        self.qs = self.get_queryset()

        dev = self.filterset_class(request.GET, self.qs)
        self._table = self.table_class(dev.qs, sort=self.sort)

        if request.htmx:
            self.template_name = self.template_hx

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({"table": self._table.render(), "sorting_field": "test"})
        return context

    def get_queryset(self) -> QuerySet[Any]:
        _model = getattr(self, "model", None)
        if _model is not None:
            return _model.objects.all()
        else:
            raise QuerySetNotDefined(
                "Tried to create Collapsible table without queryset. Either define model or override 'get_queryset'"
            )


class CollapsibleTableView(CollapsibleTableMixin, TemplateView):
    def __init__(self) -> None:
        super().__init__()
