# Generated by Django 2.2.21 on 2021-08-03 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0113_dataset_content_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]