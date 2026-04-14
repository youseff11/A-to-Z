# منصة نحوى التعليمية 🎓

منصة تعليمية تربط المدرسين بالطلاب مع دعم الاجتماعات الأونلاين المدمجة.

## هيكل المشروع

```
eduplatform/
├── eduplatform/          ← إعدادات المشروع
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── System/               ← التطبيق الوحيد
│   ├── models.py         ← CustomUser, Course, Material, Enrollment, Meeting
│   ├── views.py          ← جميع الـ Views
│   ├── urls.py           ← جميع الـ URLs
│   ├── forms.py          ← جميع الـ Forms
│   ├── admin.py
│   ├── apps.py
│   └── templates/
│       └── System/       ← Templates مدمجة في مكان واحد
│           ├── base.html
│           ├── home.html
│           ├── dashboard.html
│           ├── profile.html
│           ├── teacher_profile.html
│           ├── auth/
│           │   ├── login.html
│           │   └── register.html
│           ├── courses/
│           │   ├── list.html
│           │   ├── detail.html
│           │   └── form.html
│           ├── materials/
│           │   └── form.html
│           └── meetings/
│               ├── form.html
│               └── room.html
├── manage.py
└── requirements.txt
```

## تشغيل المشروع

```bash
# 1. تثبيت المتطلبات
pip install -r requirements.txt

# 2. عمل الـ Migrations
python manage.py makemigrations
python manage.py migrate

# 3. إنشاء superuser
python manage.py createsuperuser

# 4. تشغيل السيرفر
python manage.py runserver
```

## الصفحات والـ URLs

| الصفحة | URL |
|--------|-----|
| الرئيسية | `/` |
| تسجيل الدخول | `/login/` |
| إنشاء حساب | `/register/` |
| لوحة التحكم | `/dashboard/` |
| الكورسات | `/courses/` |
| كورس محدد | `/courses/<id>/` |
| إنشاء كورس | `/courses/create/` |
| غرفة الاجتماع | `/meetings/<uuid>/` |
| الملف الشخصي | `/profile/` |
| Admin | `/admin/` |

## المميزات

- ✅ نظام مستخدمين مع دورين: مدرس وطالب
- ✅ المدرس ينشئ كورسات ويرفع مواد (فيديو، PDF، روابط)
- ✅ الطالب يشترك في الكورسات
- ✅ اجتماعات أونلاين مدمجة (WebRTC + BroadcastChannel)
- ✅ محادثة نصية داخل الاجتماع
- ✅ نظام إشعارات
- ✅ واجهة عربية RTL كاملة
- ✅ تصميم Responsive
