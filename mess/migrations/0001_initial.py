from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('location', models.CharField(max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messes', to='auth.user')),
            ],
            options={
                'verbose_name_plural': 'Messes',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='OwnerInquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('phone', models.CharField(max_length=15)),
                ('mess_name', models.CharField(max_length=200)),
                ('location', models.CharField(max_length=300)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Owner Inquiries',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('menu_type', models.CharField(choices=[('GENERAL', 'General'), ('LUNCH', 'Lunch'), ('DINNER', 'Dinner')], max_length=10)),
                ('date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mess', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='menus', to='mess.mess')),
            ],
            options={
                'ordering': ['menu_type', 'date'],
                'unique_together': {('mess', 'date', 'menu_type')},
            },
        ),
        migrations.CreateModel(
            name='Dish',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('menu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dishes', to='mess.menu')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mess', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='mess.mess')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='auth.user')),
            ],
            options={
                'unique_together': {('user', 'mess')},
            },
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mess', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorited_by', to='mess.mess')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to='auth.user')),
            ],
            options={
                'unique_together': {('user', 'mess')},
            },
        ),
    ]
