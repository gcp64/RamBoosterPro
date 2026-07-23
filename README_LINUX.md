# RAM Booster Pro — Linux Edition (جميع توزيعات لينكس)

دليل التشغيل والتثبيت لجميع توزيعات لينكس (Ubuntu, Debian, Fedora, Arch Linux, Manjaro, Linux Mint, Pop!_OS, openSUSE).

---

## طرق التشغيل السريعة على Linux

### 1. التشغيل المباشر من المجلد (Direct Launch)
افتح الموجه النصي (Terminal) داخل مجلد المشروع ونفذ الأمر التالي:

```bash
chmod +x RamBoosterPro-Linux.sh
./RamBoosterPro-Linux.sh
```

أو عبر sudo للحصول على كافة صلاحيات تفريغ الـ drop_caches والـ sysctl:

```bash
sudo ./RamBoosterPro-Linux.sh
```

---

### 2. بناء وتشغيل ملف تنفيذي مستقل (Binary Build via PyInstaller)
لبناء ملف تنفيذي كامل ومستقل يعمل بدون الحاجة لتثبيت أي مكتبات:

```bash
chmod +x build_linux.sh
./build_linux.sh
```

سيتم إنشاء الملف التنفيذي في المجلد:
`dist/RamBoosterPro-Linux`

---

## المكتبات والمتطلبات التلقائية (Requirements)
التطبيق يقوم بتثبيتها تلقائياً، ولكن يمكنك تثبيتها يدوياً إذا رغبت:

- `python3`
- `pywebview`
- `psutil`
- `Pillow`
