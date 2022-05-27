import json
import pytest

from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from wazimap_ng.profile.models import ProfileHighlight
from wazimap_ng.profile.admin import ProfileHighlightAdmin


@pytest.mark.django_db
class TestProfileHighlightAdminHistory:

    def test_change_reason_field_in_admin_form(self, mocked_request, dataset):
        admin = ProfileHighlightAdmin(ProfileHighlight, AdminSite())
        ProfileHighlightForm = admin.get_form(mocked_request)
        fields = [f for f in ProfileHighlightForm.base_fields]
        assert bool("change_reason" in fields) == True

    def test_history_for_highlight_edit_from_admin(
        self, client, superuser, profile_highlight
    ):
        client.force_login(user=superuser)
        url = reverse(
            "admin:profile_profilehighlight_change", args=(
                profile_highlight.id,
            )
        )

        data = {
            "profile": profile_highlight.profile_id,
            "indicator": profile_highlight.indicator_id,
            "subindicator": profile_highlight.subindicator,
            "denominator": "absolute_value",
            "label": "new label",
            "display_format": "absolute_value",
            "change_reason": "Changed Label",
        }

        res = client.post(url, data, follow=True)
        assert res.status_code == 200

        assert profile_highlight.history.count() == 2
        history = profile_highlight.history.first()
        assert history.history_user_id == superuser.id
        changed_data = json.loads(history.history_change_reason)
        assert changed_data["reason"] == "Changed Label"
        assert "label" in changed_data["changed_fields"]
        assert "display_format" in changed_data["changed_fields"]
        assert "denominator" in changed_data["changed_fields"]
        assert history.history_type == "~"