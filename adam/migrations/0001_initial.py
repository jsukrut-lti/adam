# Generated by Django 3.2 on 2022-03-11 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_title', models.CharField(max_length=40)),
                ('address_type', models.CharField(choices=[('billing', 'Billing'), ('shipping', 'Shipping'), ('office', 'Office'), ('personal', 'Personal'), ('Other', 'Other'), ('current', 'Current'), ('permanent', 'Permanent')], max_length=40, null=True)),
                ('address_line1', models.CharField(max_length=100)),
                ('address_line2', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=50)),
                ('state', models.CharField(max_length=50)),
                ('country', models.CharField(max_length=50)),
                ('postal_code', models.CharField(max_length=50)),
                ('latitude', models.CharField(max_length=50)),
                ('longitude', models.CharField(max_length=50)),
                ('enable', models.BooleanField(default=True)),
            ],
        ),
    ]
