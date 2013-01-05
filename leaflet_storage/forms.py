import urllib2

from django import forms
from django.contrib.gis.geos import Point
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify

from vectorformats.formats import geojson, kml, gpx

from .models import Map, Category


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
                    raise forms.ValidationError(_("You already have a map with this name."))
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

    JSON = "json"
    KML = "kml"
    GPX = "gpx"
    CONTENT_TYPES = (
        (JSON, "JSON"),
        (KML, "KML"),
        (GPX, "GPX"),
    )

    # GPX has no official content_type, so we can't guess it's type when
    # fetched from an URL which doesn't give us a file name in responses
    # headers. So for now ask user the content_type...
    content_type = forms.ChoiceField(CONTENT_TYPES, label=_("Content type"))
    data_file = forms.FileField(required=False, label=_("file"))
    data_url = forms.URLField(required=False, label=_("URL"))
    category = forms.ModelChoiceField([], label=_("category"))  # queryset is set by view

    def clean_data_file(self):
        """
        Return a features list if file is valid.
        Otherwise raise a ValidationError.
        """
        features = []
        f = self.cleaned_data.get('data_file')
        if f:
            features = self.content_to_features(f.read())
        return features

    def clean_data_url(self):
        url = self.cleaned_data.get('data_url')
        features = []
        if url:
            try:
                response = urllib2.urlopen(url)
            except urllib2.URLError:
                raise forms.ValidationError(_('Unable to fetch content from URL.'))
            else:
                content = response.read()
                features = self.content_to_features(content)
        return features

    def clean(self):
        cleaned_data = super(UploadDataForm, self).clean()
        data_file = cleaned_data.get("data_file")
        data_url = cleaned_data.get("data_url")
        data_sources = [data_file, data_url]
        if not any(data_sources):
            raise forms.ValidationError(_('You must provide an URL or a file.'))
        elif all(data_sources):
            raise forms.ValidationError(_("You can't provide both a file and an URL."))
        return cleaned_data

    def content_to_features(self, content):
        features = []
        content_type = self.cleaned_data.get('content_type')
        MAP = {
            self.JSON: geojson.GeoJSON,
            self.KML: kml.KML,
            self.GPX: gpx.GPX
        }
        if not content_type in MAP:
            raise forms.ValidationError(_('Unsupported content_type: %s') % content_type)
        format = MAP[content_type]()
        try:
            features = format.decode(content)
        except:
            raise forms.ValidationError(_('Invalid %(content_type)s') % {'content_type': content_type})
        return features


class FeatureForm(PlaceholderForm):

    class Meta:
        # model is added at runtime by the views
        fields = ('name', 'description', 'color', 'category', 'latlng')
        widgets = {
            'latlng': forms.HiddenInput(),
        }
