from typing import Any, Dict
from django.template.loader import render_to_string
from logging import getLogger

from django.db.models.query import QuerySet

log = getLogger(__name__)


class CollapsibleTableViewMixin:
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        pass


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

    @property
    def field_names(self):
        fNames = []
        for field in self.fields:
            fNames.append(field["name"].lower())
        return fNames

    def __init__(self, data=None, fields=None) -> None:
        print("data:", data)

        self.qs = data if data is not None else self.get_queryset()

        if not hasattr(self, "child_table_class"):
            self.child_table_class = self.__class__

        if fields is not None:
            self.fields = fields

    def _default_fields(self):
        self.fields = []
        for field in list(self.qs.values()[0]):
            self.fields.append(
                {"name": field.capitalize(), "header_css_class": "col-3"}
            )

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
                        temp.append(field)
                    else:
                        temp.append(
                            {"name": field.capitalize(), "header_css_class": "col-3"}
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
                render_func = getattr(row, f"render_{field}", None)
                if render_func is not None:
                    item = render_func()
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
        self.render_header()

        return render_to_string(
            "collapsible_table/table.html",
            context={
                "table_css_class": self.table_css_class,
                "expand_header_css_class": self.expand_header_css_class,
                "fields": self.fields,
                "rows": self.render_rows(),
            },
        )

    def get_queryset(self) -> QuerySet[Any]:
        raise QuerySetNotDefined
        pass

    def get_child_queryset(self, record) -> QuerySet[Any]:
        return None
