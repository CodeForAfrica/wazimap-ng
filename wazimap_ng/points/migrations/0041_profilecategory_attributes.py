# Generated by Django 2.2.13 on 2021-03-02 20:06

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0040_merge_20210111_1807'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilecategory',
            name='visible_tooltip_attributes',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True),
        ),
    ]