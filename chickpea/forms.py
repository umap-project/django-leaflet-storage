from django import forms
from django.template.defaultfilters import slugify
from django.contrib.gis.geos import Point

from vectorformats.Formats import GeoJSON

from chickpea.models import Map, Category


class PlaceholderForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(PlaceholderForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.iteritems():
            if isinstance(field.widget, (forms.Textarea, forms.TextInput)):
                field.widget.attrs['placeholder'] = field.label
                field.label = ""


class QuickMapCreateForm(PlaceholderForm):

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        super(QuickMapCreateForm, self).__init__(*args, **kwargs)

    # don't bother the user with the slug and center, instead calculate them
    center = forms.CharField(required=False, widget=forms.HiddenInput())
    slug = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Map
        fields = ('name', 'description', 'licence', 'slug', 'center')

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', None)
        name = self.cleaned_data.get('name', None)
        if not slug and name:
            # If name is empty, don't do nothing, validation will raise
            # later on the process because name is required
            self.cleaned_data['slug'] = slugify(name)
            return self.cleaned_data['slug']
        else:
            return ""

    def clean_center(self):
        if not self.cleaned_data['center']:
            point = Point(2, 51)
            self.cleaned_data['center'] = point
        return self.cleaned_data['center']

    def clean(self):
        # slug is not displayed, so check that it's unique on name
        slug = self.cleaned_data.get('slug', None)
        if slug:
            try:
                existing_map = Map.objects.get(owner=self.owner, slug=slug)
            except Map.DoesNotExist:
                pass
            else:
                if existing_map.pk != self.instance.pk:
                    raise forms.ValidationError("You already have a map with this name.")
        return self.cleaned_data


class UpdateMapExtentForm(forms.ModelForm):

    class Meta:
        model = Map
        fields = ('zoom', 'center')


class UpdateMapPermissionsForm(forms.ModelForm):

    class Meta:
        model = Map
        fields = ('edit_status', 'editors')


class CategoryForm(PlaceholderForm):

    class Meta:
        model = Category
        widgets = {
            "map": forms.HiddenInput()
        }


class UploadDataForm(forms.Form):

    data_file = forms.FileField(help_text="Supported format: GeoJSON.")
    category = forms.ModelChoiceField([])  # queryset is set by view

    def clean_data_file(self):
        """
        Return a features list if file is valid.
        Otherwise raise a ValidationError.
        """
        features = []
        f = self.cleaned_data.get('data_file')
        if f.content_type == "application/json":
            geoj = GeoJSON.GeoJSON()
            try:
                features = geoj.decode(f.read())
            except:
                raise forms.ValidationError('Invalid geojson')
        else:
            raise forms.ValidationError('Invalid content_type: %s' % f.content_type)
        return features


class FeatureForm(PlaceholderForm):

    class Meta:
        # model is added at runtime by the views
        fields = ('name', 'description', 'color', 'category', 'latlng')
        widgets = {
            'latlng': forms.HiddenInput(),
        }
