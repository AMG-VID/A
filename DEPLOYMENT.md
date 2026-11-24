# ManaraTech POS — إعداد النشر

## تفعيل تسجيل الحساب

1. افتح مشروع Firebase المستخدم في التطبيق. قيمة projectId الحالية في firebaseConfig داخل index.html هي: bakkala-system.
2. من Firebase Console ثم Authentication ثم Sign-in method، فعّل Email/Password.
3. فعّل Cloud Firestore وCloud Functions.
4. نشر Cloud Functions يتطلب خطة Blaze مع تفعيل الفوترة.
5. أنشئ Google App Password لحساب Gmail الذي سيُرسل رسائل التحقق. لا تستخدم كلمة مرور Gmail العادية، ولا تضع كلمة المرور في أي ملف بالمستودع.

## إعداد الأسرار

ثبّت Firebase CLI وسجّل الدخول من جهازك:

    npm install -g firebase-tools
    firebase login
    firebase use --add

اختر مشروع bakkala-system أو المشروع الصحيح الذي يحتوي قاعدة البيانات الحالية.

اضبط الأسرار التالية، وسيطلب Firebase القيم بشكل آمن:

    firebase functions:secrets:set SMTP_USER
    firebase functions:secrets:set SMTP_PASS
    firebase functions:secrets:set OTP_HMAC_SECRET

SMTP_USER هو بريد Gmail المرسل.
SMTP_PASS هو Google App Password الخاص بالحساب المرسل.
OTP_HMAC_SECRET قيمة عشوائية قوية لا تقل عن 32 بايت. يمكن توليدها محليًا بالأمر:

    node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

لا ترسل هذه القيم في المحادثات ولا ترفعها إلى GitHub.

## تثبيت الحزم والنشر

    cd functions
    npm install
    cd ..
    firebase deploy --only functions,firestore:rules,hosting

## ما الذي يفعله كود التسجيل؟

- يرسل كودًا عشوائيًا من 6 أرقام إلى البريد الذي أدخله المستخدم.
- صلاحية الكود 10 دقائق، ومحاولات التحقق محدودة بخمس محاولات.
- يوجد حد لإعادة إرسال الكود وحد لمعدل الطلبات من عنوان IP.
- لا يتم إنشاء مستخدم Firebase أو متجره إلا بعد التحقق الصحيح من الكود.
- كلمات مرور SMTP وOTP محفوظة في Firebase Secret Manager وليست في واجهة المتصفح.
- قواعد Firestore تمنع المستخدم من قراءة بيانات متجر آخر أو تغيير ملف الصلاحيات الخاص به.

## قبل فتح التسجيل للعامة

اختبر إنشاء حساب جديد، وصول البريد، انتهاء الكود، إدخال كود خاطئ عدة مرات، إعادة إرسال الكود، تسجيل الدخول، ثم حسابين منفصلين ومحاولة كل منهما قراءة بيانات المتجر الآخر.

ملاحظة مهمة: المستودع يحتوي تطبيقًا قديمًا يستخدم أسماء دخول اصطناعية تنتهي بـ @bkalla.com. صفحة الدخول الجديدة تعتمد البريد الإلكتروني الفعلي. قد تحتاج الحسابات القديمة إلى ترحيل يدوي أو إعادة إنشاء آمنة قبل تشغيل النسخة الجديدة؛ لا تحذف المستخدمين أو بيانات المتاجر القديمة لمجرد تفعيل هذا الفرع.

رفع الملفات إلى GitHub لا ينشر Cloud Functions أو Firestore Rules تلقائيًا. يجب تنفيذ أوامر النشر أعلاه على مشروع Firebase الصحيح.
