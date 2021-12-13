# Generated by Django 3.2.5 on 2021-12-08 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('picture', models.ImageField(blank=True, upload_to='microcirculation_images')),
                ('backend_address', models.IntegerField(blank=True, null=True)),
                ('time_to_classify', models.CharField(blank=True, max_length=200)),
                ('uploaded', models.DateTimeField(auto_now_add=True)),
                ('analyzed_picture', models.ImageField(blank=True, upload_to='analyzed_picture')),
                ('segmented_image', models.ImageField(blank=True, upload_to='segmented_image')),
                ('capillary_area', models.CharField(blank=True, max_length=200)),
                ('number_of_capillaries', models.CharField(blank=True, max_length=200)),
            ],
        ),
    ]
