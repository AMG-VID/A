import { initializeApp } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';
import { getFirestore, FieldValue } from 'firebase-admin/firestore';
import { defineSecret } from 'firebase-functions/params';
import { HttpsError, onCall } from 'firebase-functions/v2/https';
import { setGlobalOptions } from 'firebase-functions/v2';
import nodemailer from 'nodemailer';
import crypto from 'node:crypto';

initializeApp();
setGlobalOptions({ region: 'us-central1', maxInstances: 5 });

const db = getFirestore();
const auth = getAuth();

const SMTP_USER = defineSecret('SMTP_USER');
const SMTP_PASS = defineSecret('SMTP_PASS');
const OTP_HMAC_SECRET = defineSecret('OTP_HMAC_SECRET');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const OTP_TTL_MS = 10 * 60 * 1000;
const RESEND_WAIT_MS = 60 * 1000;
const MAX_VERIFY_ATTEMPTS = 5;

function normalizeEmail(value) {
    return String(value || '').trim().toLowerCase();
}
function digest(value) {
    return crypto.createHash('sha256').update(value).digest('hex');
}
function otpDigest(email, code, secret) {
    return crypto.createHmac('sha256', secret).update(email + ':' + code).digest('hex');
}
function safeEqualHex(left, right) {
    if (typeof left !== 'string' || typeof right !== 'string') return false;
    const a = Buffer.from(left, 'hex');
    const b = Buffer.from(right, 'hex');
    return a.length === b.length && a.length > 0 && crypto.timingSafeEqual(a, b);
}
function escapeHtml(value) {
    return String(value || '').replace(/[&<>"']/g, function (ch) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
    });
}
async function accountAlreadyExists(email) {
    try {
        await auth.getUserByEmail(email);
        return true;
    } catch (error) {
        if (error.code === 'auth/user-not-found') return false;
        throw error;
    }
}

export const requestRegistrationCode = onCall(
    { secrets: [SMTP_USER, SMTP_PASS, OTP_HMAC_SECRET], timeoutSeconds: 30, memory: '256MiB' },
    async (request) => {
        const email = normalizeEmail(request.data?.email);
        const storeName = String(request.data?.storeName || '').trim();

        if (!EMAIL_PATTERN.test(email) || email.length > 254) {
            throw new HttpsError('invalid-argument', 'اكتب بريدًا إلكترونيًا صحيحًا.');
        }
        if (storeName.length < 2 || storeName.length > 80) {
            throw new HttpsError('invalid-argument', 'اسم النشاط يجب أن يكون بين حرفين و80 حرفًا.');
        }

        // Same response for an already-registered and a new email address.
        if (await accountAlreadyExists(email)) return { ok: true };

        const now = Date.now();
        const code = String(crypto.randomInt(100000, 1000000));
        const emailKey = digest(email);
        const otpRef = db.collection('_registrationOtp').doc(emailKey);
        const remoteIp = String(request.rawRequest?.ip || 'unknown');
        const ipRef = db.collection('_registrationOtpRateLimits').doc(digest(remoteIp));

        await db.runTransaction(async (transaction) => {
            const [otpSnap, ipSnap] = await Promise.all([
                transaction.get(otpRef),
                transaction.get(ipRef)
            ]);

            if (otpSnap.exists) {
                const previous = otpSnap.data();
                if (now - Number(previous.lastSentAt || 0) < RESEND_WAIT_MS) {
                    throw new HttpsError('resource-exhausted', 'انتظر دقيقة قبل طلب كود جديد.');
                }
                if (Number(previous.sentInWindow || 0) >= 5 &&
                    now - Number(previous.windowStartedAt || 0) < 24 * 60 * 60 * 1000) {
                    throw new HttpsError('resource-exhausted', 'تم تجاوز عدد طلبات الكود لهذا البريد. حاول لاحقًا.');
                }
            }

            const ipRecord = ipSnap.exists ? ipSnap.data() : {};
            let ipWindowStart = Number(ipRecord.windowStartedAt || now);
            let ipCount = Number(ipRecord.requestCount || 0);
            if (now - ipWindowStart >= 60 * 60 * 1000) {
                ipWindowStart = now;
                ipCount = 0;
            }
            if (ipCount >= 10) {
                throw new HttpsError('resource-exhausted', 'عدد المحاولات كبير من هذا الاتصال. حاول بعد ساعة.');
            }

            const previous = otpSnap.exists ? otpSnap.data() : {};
            const windowValid = now - Number(previous.windowStartedAt || now) < 24 * 60 * 60 * 1000;
            transaction.set(otpRef, {
                emailHash: emailKey,
                codeHash: otpDigest(email, code, OTP_HMAC_SECRET.value()),
                storeName,
                createdAt: now,
                lastSentAt: now,
                expiresAt: now + OTP_TTL_MS,
                attempts: 0,
                sentInWindow: windowValid ? Number(previous.sentInWindow || 0) + 1 : 1,
                windowStartedAt: windowValid ? Number(previous.windowStartedAt || now) : now,
                status: 'pending'
            });
            transaction.set(ipRef, {
                windowStartedAt: ipWindowStart,
                requestCount: ipCount + 1,
                expireAt: now + 48 * 60 * 60 * 1000
            });
        });

        try {
            const smtpUser = SMTP_USER.value();
            const transporter = nodemailer.createTransport({
                host: 'smtp.gmail.com',
                port: 465,
                secure: true,
                auth: { user: smtpUser, pass: SMTP_PASS.value() },
                connectionTimeout: 15000,
                greetingTimeout: 15000,
                socketTimeout: 20000
            });
            const safeStoreName = escapeHtml(storeName);
            await transporter.sendMail({
                from: { name: 'ManaraTech', address: smtpUser },
                to: email,
                subject: 'كود التحقق لإنشاء حساب ManaraTech',
                text:
                    'مرحبًا ' + storeName + '\n\n' +
                    'كود التحقق الخاص بك هو: ' + code + '\n' +
                    'صلاحية الكود 10 دقائق، ولا تشاركه مع أي شخص.\n\n' +
                    'إذا لم تطلب إنشاء حساب، يمكنك تجاهل هذه الرسالة.',
                html:
                    '<div dir="rtl" style="font-family:Arial,sans-serif;max-width:520px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:16px">' +
                    '<h2 style="color:#4f46e5">ManaraTech</h2>' +
                    '<p>مرحبًا ' + safeStoreName + '،</p>' +
                    '<p>استخدم كود التحقق التالي لإكمال إنشاء حسابك:</p>' +
                    '<div style="font-size:32px;letter-spacing:8px;font-weight:bold;text-align:center;padding:18px;background:#f3f4f6;border-radius:12px">' + code + '</div>' +
                    '<p>تنتهي صلاحية الكود بعد 10 دقائق. لا تشاركه مع أي شخص.</p>' +
                    '<p style="color:#64748b;font-size:12px">إذا لم تطلب إنشاء حساب، تجاهل هذه الرسالة.</p>' +
                    '</div>'
            });
        } catch (error) {
            console.error('Registration email delivery failed:', error);
            await otpRef.delete().catch(() => {});
            throw new HttpsError('internal', 'تعذر إرسال رسالة التحقق حاليًا. حاول لاحقًا.');
        }
        return { ok: true };
    }
);

export const completeRegistration = onCall(
    { secrets: [OTP_HMAC_SECRET], timeoutSeconds: 30, memory: '256MiB' },
    async (request) => {
        const email = normalizeEmail(request.data?.email);
        const password = String(request.data?.password || '');
        const code = String(request.data?.code || '').trim();

        if (!EMAIL_PATTERN.test(email) || email.length > 254) {
            throw new HttpsError('invalid-argument', 'البريد الإلكتروني غير صحيح.');
        }
        if (password.length < 8 || password.length > 128) {
            throw new HttpsError('invalid-argument', 'كلمة المرور يجب أن تكون من 8 إلى 128 حرفًا.');
        }
        if (!/^\d{6}$/.test(code)) {
            throw new HttpsError('invalid-argument', 'أدخل كود التحقق المكوّن من 6 أرقام.');
        }

        const otpRef = db.collection('_registrationOtp').doc(digest(email));
        const now = Date.now();
        const verification = await db.runTransaction(async (transaction) => {
            const snap = await transaction.get(otpRef);
            if (!snap.exists) return { state: 'missing' };
            const otp = snap.data();

            if (otp.status !== 'pending') return { state: 'processing' };
            if (now > Number(otp.expiresAt || 0)) {
                transaction.delete(otpRef);
                return { state: 'expired' };
            }
            if (Number(otp.attempts || 0) >= MAX_VERIFY_ATTEMPTS) {
                transaction.delete(otpRef);
                return { state: 'locked' };
            }

            const suppliedHash = otpDigest(email, code, OTP_HMAC_SECRET.value());
            if (!safeEqualHex(suppliedHash, otp.codeHash)) {
                const nextAttempts = Number(otp.attempts || 0) + 1;
                if (nextAttempts >= MAX_VERIFY_ATTEMPTS) transaction.delete(otpRef);
                else transaction.update(otpRef, { attempts: nextAttempts });
                return { state: 'invalid' };
            }

            transaction.update(otpRef, { status: 'processing', processingAt: now });
            return { state: 'verified', storeName: otp.storeName };
        });

        if (verification.state === 'missing' || verification.state === 'expired') {
            throw new HttpsError('deadline-exceeded', 'انتهت صلاحية الكود أو لم يعد موجودًا. اطلب كودًا جديدًا.');
        }
        if (verification.state === 'invalid') {
            throw new HttpsError('permission-denied', 'كود التحقق غير صحيح. راجع الكود وحاول مرة أخرى.');
        }
        if (verification.state === 'locked') {
            throw new HttpsError('resource-exhausted', 'تم إيقاف هذا الكود بعد محاولات خاطئة كثيرة. اطلب كودًا جديدًا.');
        }
        if (verification.state !== 'verified') {
            throw new HttpsError('aborted', 'طلب التحقق قيد التنفيذ. حاول مرة أخرى بعد لحظات.');
        }

        let createdUser = null;
        try {
            createdUser = await auth.createUser({
                email,
                password,
                emailVerified: true,
                displayName: verification.storeName
            });
            const storeId = 'store_' + createdUser.uid;
            const userRef = db.collection('users').doc(createdUser.uid);
            const storeRef = db.collection('stores').doc(storeId);

            await db.runTransaction(async (transaction) => {
                const [userSnap, storeSnap] = await Promise.all([
                    transaction.get(userRef),
                    transaction.get(storeRef)
                ]);
                if (userSnap.exists || storeSnap.exists) throw new Error('User or store profile already exists.');
                transaction.create(storeRef, {
                    name: verification.storeName,
                    ownerUid: createdUser.uid,
                    isActive: true,
                    createdAt: FieldValue.serverTimestamp()
                });
                transaction.create(userRef, {
                    email,
                    role: 'owner',
                    storeId,
                    storeName: verification.storeName,
                    isActive: true,
                    emailOtpVerified: true,
                    createdAt: FieldValue.serverTimestamp()
                });
            });

            await otpRef.delete();
            return { ok: true };
        } catch (error) {
            if (createdUser) {
                await auth.deleteUser(createdUser.uid).catch((cleanupError) => {
                    console.error('Unable to roll back newly created Auth user:', cleanupError);
                });
            }
            await otpRef.set({ status: 'pending' }, { merge: true }).catch(() => {});
            if (error.code === 'auth/email-already-exists') {
                await otpRef.delete().catch(() => {});
                throw new HttpsError('already-exists', 'هذا البريد لديه حساب بالفعل. سجل الدخول بدلًا من إنشاء حساب جديد.');
            }
            console.error('Registration profile creation failed:', error);
            throw new HttpsError('internal', 'تعذر إنشاء الحساب الآن. حاول مرة أخرى.');
        }
    }
);
