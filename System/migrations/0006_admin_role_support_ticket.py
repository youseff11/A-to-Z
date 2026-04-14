from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('System', '0005_alter_exam_duration_minutes_alter_exam_pass_score'),
    ]

    operations = [
        # Update role field to include 'admin'
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[('teacher', 'مدرس'), ('student', 'طالب'), ('admin', 'مدير')],
                default='student',
                max_length=10
            ),
        ),
        # Create SupportTicket model
        migrations.CreateModel(
            name='SupportTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200)),
                ('status', models.CharField(
                    choices=[('open', 'مفتوح'), ('answered', 'تم الرد'), ('closed', 'مغلق')],
                    default='open', max_length=20
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='support_tickets',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['-updated_at']},
        ),
        # Create SupportMessage model
        migrations.CreateModel(
            name='SupportMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('is_admin_reply', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ticket', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='System.supportticket'
                )),
                ('sender', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['created_at']},
        ),
    ]
