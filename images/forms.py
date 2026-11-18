import io
from urllib.parse import urlparse

import requests
from PIL import Image as PILImage
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django import forms
from .models import Image


class ImageCreateForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['title', 'url', 'description']
        widgets = {
            'url': forms.HiddenInput,
        }

    def clean_url(self):
        url = self.cleaned_data['url']
        valid_extensions = ['jpg', 'jpeg', 'png']
        path = urlparse(url).path
        extension = path.rsplit('.', 1)[-1].lower() if '.' in path else ''
        if extension not in valid_extensions:
            raise forms.ValidationError(
                'The given URL does not match valid image extensions.'
            )
        return url

    def save(self, force_insert=False, force_update=False,commit = True):
        image = super().save(commit=False)
        image_url = self.cleaned_data['url']
        name = slugify(image.title) or 'image'
        extension = urlparse(image_url).path.rsplit('.', 1)[-1].lower()
        image_name = f'{name}.{extension}'
        # download image from the given URL
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        # make sure we really got an image and not an error page
        try:
            PILImage.open(io.BytesIO(response.content)).verify()
        except Exception:
            raise ValueError('The downloaded file is not a valid image.')
        image.image.save(
            image_name,
            ContentFile(response.content),
            save=False
        )
        if commit:
            image.save()
        return image