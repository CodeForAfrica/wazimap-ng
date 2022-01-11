# Generated by Django 2.2.24 on 2021-11-11 04:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0125_historicaldataset_historicaldatasetfile_historicalgeographyhierarchy_historicalgroup_historicalindic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaldataset',
            name='history_change_reason',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='historicaldatasetfile',
            name='history_change_reason',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='historicalgeographyhierarchy',
            name='history_change_reason',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='historicalgroup',
            name='history_change_reason',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='historicalindicator',
            name='history_change_reason',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='historicaluniverse',
            name='history_change_reason',
            field=models.TextField(null=True),
        ),
    ]