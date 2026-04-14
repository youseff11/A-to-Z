from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('System', '0003_customuser_payment_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaterialView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='System.material')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='material_views', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('material', 'student')},
            },
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('duration_minutes', models.PositiveIntegerField(default=30)),
                ('pass_score', models.PositiveIntegerField(default=50)),
                ('is_published', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exams', to='System.course')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('question_type', models.CharField(choices=[('mcq', 'اختيار من متعدد'), ('true_false', 'صح أو خطأ')], default='mcq', max_length=20)),
                ('option_a', models.CharField(blank=True, max_length=300, null=True)),
                ('option_b', models.CharField(blank=True, max_length=300, null=True)),
                ('option_c', models.CharField(blank=True, max_length=300, null=True)),
                ('option_d', models.CharField(blank=True, max_length=300, null=True)),
                ('correct_answer', models.CharField(max_length=10)),
                ('marks', models.PositiveIntegerField(default=1)),
                ('order', models.PositiveIntegerField(default=0)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='System.exam')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ExamAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('total_marks', models.PositiveIntegerField(default=0)),
                ('percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('passed', models.BooleanField(default=False)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='System.exam')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_attempts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('exam', 'student')},
            },
        ),
        migrations.CreateModel(
            name='StudentAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.CharField(max_length=10)),
                ('is_correct', models.BooleanField(default=False)),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='System.examattempt')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='System.question')),
            ],
        ),
    ]
