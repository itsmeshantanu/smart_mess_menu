from django.db import migrations, models
import django.db.models.deletion
import mess.models


class Migration(migrations.Migration):

    dependencies = [
        ('mess', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mess',
            name='latitude',
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True,
                help_text='e.g. 20.011200'
            ),
        ),
        migrations.AddField(
            model_name='mess',
            name='longitude',
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True,
                help_text='e.g. 73.790300'
            ),
        ),
        migrations.CreateModel(
            name='MessPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=mess.models.mess_photo_upload_path)),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('is_cover', models.BooleanField(default=False)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('mess', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='photos',
                    to='mess.mess'
                )),
            ],
            options={
                'ordering': ['-is_cover', 'uploaded_at'],
            },
        ),
    ]
