import os
from django.core.files.base import ContentFile
from django.db.models.fields.files import FileField, ImageField
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from import_export.resources import ModelResource
from multiselectfield import MultiSelectField
from base64 import b64encode, b64decode
from import_export.widgets import Widget


class MultiSelectFieldWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        return value

    def render(self, value, obj=None):
        return value


class FileFieldWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if value:
            file_name, file_format, encoded_string = value.split(',')
            return ContentFile(b64decode(encoded_string), name="{}.{}".format(file_name, file_format))

    def render(self, value, obj=None):
        if value and value.name and os.path.isfile(value.path):
            file_name, file_format = os.path.splitext(os.path.basename(value.name))
            return '%s,%s,%s' % (file_name.replace(',', '_'), file_format[1:], b64encode(value.read()))


class CalenderModelAdmin(ImportExportModelAdmin):
    save_as = True

    @property
    def resource_class(self):
        custom_widgets = {
            'FileField': FileFieldWidget,
            'ImageField': FileFieldWidget,
            'MultiSelectField': MultiSelectFieldWidget
        }
        class_attrs = {
            x.name: Field(column_name=x.name, attribute=x.name, widget=custom_widgets.get(x.__class__.__name__)())
            for x in self.model._meta.fields if isinstance(x, (FileField, ImageField, MultiSelectField))
        }
        class_attrs['Meta'] = type("Meta", (object,), {'model': self.model})
        return type('%sImportExportResource' % self.model.__name__, (ModelResource,), class_attrs)


def foreign_field(field_name):
    def accessor(obj):
        val = obj
        for part in field_name.split('__'):
            val = getattr(val, part) if val else None
        return val

    accessor.__name__ = str(field_name)
    return accessor


def many_to_many_field(field_name):
    def accessor(obj):
        related_field, field_to_display = field_name.split('__')
        display_res = [getattr(each_object, field_to_display)
                       for each_object in getattr(obj, related_field).all()
                       ]
        return ", ".join(sorted(display_res))

    accessor.__name__ = field_name
    return accessor


ff = foreign_field
mf = many_to_many_field
