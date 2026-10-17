from django import forms
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def validate_image_size(image, max_mb):
    is_new_upload = isinstance(image, UploadedFile)
    if is_new_upload and image.size > max_mb * 1024 * 1024:
        raise forms.ValidationError(f'Image must be smaller than {max_mb} MB.')
    return image


def delete_replaced_file(old_name, new_name):
    if old_name and old_name != new_name:
        default_storage.delete(old_name)


def redirect_back(request, fallback_url):
    next_url = request.POST.get('next') or request.GET.get('next')
    # block foreign redirects
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect(fallback_url)


# browser drops chosen file
class ReselectFileHintMixin:
    def form_invalid(self, form):
        for field_name in self.request.FILES:
            if field_name in form.fields and not form.has_error(field_name):
                form.add_error(field_name, 'Please choose the file again: it is not kept when the form has errors.')
        return super().form_invalid(form)

