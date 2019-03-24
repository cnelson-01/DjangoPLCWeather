# Generated by Django 2.1.7 on 2019-03-24 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PLCWeather', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('panelVoltage', models.FloatField()),
                ('panelCurrent', models.FloatField()),
                ('batteryVoltage', models.FloatField()),
                ('loadVoltage', models.FloatField()),
                ('loadCurrent', models.FloatField()),
                ('collectionTime', models.DateTimeField(verbose_name='date/time collected')),
            ],
        ),
        migrations.RenameModel(
            old_name='Temperature',
            new_name='TemperatureSensor',
        ),
        migrations.DeleteModel(
            name='SysemStats',
        ),
    ]
