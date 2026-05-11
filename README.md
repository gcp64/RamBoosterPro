<div align="center">

# RamBooster Pro — System Optimizer

### High-Performance Windows System Optimizer | محسّن نظام ويندوز عالي الأداء

[![License](https://img.shields.io/badge/License-MIT%20Modified-blue.svg)](#license)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4.svg)](#requirements)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg)](#requirements)
[![Developer](https://img.shields.io/badge/Developed%20by-Bob-7c8aff.svg)](#developer)

---

**RamBooster Pro** is a professional-grade Windows system optimizer featuring a stunning glassmorphism UI with interactive particle effects, real-time memory monitoring, deep disk cleaning, game mode CPU boost, and network optimization.

**RamBooster Pro** هو محسّن نظام ويندوز احترافي بواجهة زجاجية فاخرة مع جزيئات تفاعلية، مراقبة ذاكرة حية، تنظيف عميق للقرص، وضع ألعاب لتعزيز المعالج، وتحسين الشبكة.

</div>

---

## Features | المميزات

### RAM Booster | تعزيز الذاكرة
- Real-time circular gauge showing RAM usage | مقياس دائري لاستهلاك الذاكرة
- Ultra Smart Clean: clears standby list, trims working sets | تنظيف ذكي للذاكرة
- Live process list with memory consumption | قائمة عمليات حية
- Activity log tracking all operations | سجل عمليات مفصّل

### Disk Deep Clean | تنظيف القرص العميق
- System temp files cleanup | تنظيف ملفات النظام المؤقتة
- Browser cache clearing (Chrome, Edge, Firefox, Opera, Brave) | مسح كاش المتصفحات
- Windows Update leftovers removal | إزالة بقايا تحديثات ويندوز
- Prefetch, thumbnails, logs cleanup | تنظيف Prefetch والصور المصغرة
- Recycle bin emptying | تفريغ سلة المحذوفات

### Game Mode / CPU Boost | وضع الألعاب
- Stops 20+ non-essential Windows services | إيقاف +20 خدمة ويندوز غير ضرورية
- Sets HIGH PERFORMANCE power plan | تفعيل خطة الطاقة القصوى
- Boosts CPU process priority | تعزيز أولوية المعالج
- Reduces visual effects for max FPS | تقليل المؤثرات البصرية
- Fully reversible with one click | قابل للإلغاء بضغطة زر

### Network Optimizer | تسريع الشبكة
- DNS cache flush | مسح كاش DNS
- IP address renewal | تجديد عنوان IP
- TCP/IP optimization (disable Nagle's algorithm) | تحسين TCP/IP
- Network throttling removal | إزالة خنق الشبكة
- ARP cache clearing | مسح كاش ARP
- Compound TCP (CTCP) activation | تفعيل CTCP

### UI / Interface | الواجهة
- Glassmorphism design with backdrop blur | تصميم زجاجي بتأثير ضبابي
- Interactive tsParticles background | خلفية جزيئات تفاعلية
- Bilingual interface (English / Arabic) | واجهة ثنائية اللغة
- Sidebar navigation with 4 sections | قائمة جانبية بـ 4 أقسام
- Real-time stats updating every 2 seconds | إحصائيات حية كل ثانيتين

---

## Download | التحميل

### Quick Install (EXE)
Download the latest `RamBoosterPro.exe` from the [Releases](../../releases) page.

> **Note:** Run as Administrator for full functionality (RAM cleaning, game mode, network optimization).

> **ملاحظة:** شغّل كمسؤول للوصول الكامل (تنظيف الرام، وضع الألعاب، تحسين الشبكة).

---

## Build from Source | البناء من المصدر

### Requirements | المتطلبات
- Python 3.12+
- Windows 10/11

### Setup | الإعداد
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/RamBoosterPro.git
cd RamBoosterPro

# Install dependencies
pip install -r requirements.txt

# Run the application
python web_app.py
```

### Build EXE | بناء الملف التنفيذي
```bash
pyinstaller --noconfirm --onefile --windowed --name "RamBoosterPro" ^
  --add-data "ram_booster;ram_booster" --add-data "web;web" ^
  --hidden-import webview --hidden-import psutil --hidden-import PIL ^
  --collect-all customtkinter --icon "icon.ico" --clean web_app.py
```

---

## Project Structure | هيكل المشروع

```
RamBoosterPro/
├── web_app.py                 # PyWebView bridge (main entry point)
├── web/
│   └── index.html             # Glassmorphism + Particles UI
├── ram_booster/
│   ├── memory.py              # RAM monitoring & cleaning engine
│   ├── optimizer.py           # System boost utilities
│   ├── disk_cleaner.py        # Deep disk cleaning engine
│   ├── game_mode.py           # Game mode / CPU boost engine
│   ├── network_optimizer.py   # Network & ping optimizer
│   ├── icon.png               # App icon (original)
│   └── icon_web.png           # App icon (optimized for web)
├── icon.ico                   # Windows icon
├── requirements.txt           # Python dependencies
├── build.bat                  # Build script
├── LICENSE                    # License
└── README.md                  # This file
```

---

## Tech Stack | التقنيات

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, ctypes, psutil |
| Frontend | HTML5, CSS3, JavaScript |
| UI Framework | Glassmorphism + tsParticles |
| Bridge | PyWebView (native window) |
| Build | PyInstaller |
| Windows API | NtSetSystemInformation, Win32 Services |

---

## Permissions | الصلاحيات

Some features require **Administrator** privileges:

| Feature | Admin Required |
|---------|---------------|
| RAM Smart Clean | Yes |
| Disk Deep Clean | Partial (some system dirs) |
| Game Mode | Yes (service control) |
| Network Optimize | Yes (TCP/IP registry) |
| Process Monitoring | No |

---

## Terms of Use | شروط الاستخدام

1. **Personal Use**: Free for personal, non-commercial use.
   الاستخدام الشخصي مجاني وغير تجاري.

2. **Attribution Required**: Any use, fork, or derivative must credit the original developer (Bob).
   أي استخدام أو تعديل يجب أن يذكر المطور الأصلي (Bob).

3. **Modification**: You may modify this software for personal use. Public distribution of modified versions requires written permission from the developer.
   يمكنك تعديل البرنامج للاستخدام الشخصي. التوزيع العام للنسخ المعدّلة يتطلب إذن كتابي من المطور.

4. **No Warranty**: This software is provided as-is. The developer is not responsible for any damage or data loss.
   البرنامج مقدّم كما هو. المطور غير مسؤول عن أي ضرر أو فقدان بيانات.

5. **Credits Preservation**: The "Developed by Bob" credit in the application must not be removed or altered.
   لا يجوز إزالة أو تعديل عبارة "Developed by Bob" في التطبيق.

---

## Disclaimer | إخلاء المسؤولية

> This software modifies system settings including Windows services, power plans, TCP/IP parameters, and memory management. Use at your own risk. Always ensure you have backups before running system optimization tools. The developer assumes no liability for any system instability or data loss.

> هذا البرنامج يعدّل إعدادات النظام بما في ذلك خدمات ويندوز وخطط الطاقة ومعاملات TCP/IP وإدارة الذاكرة. استخدمه على مسؤوليتك. تأكد دائماً من وجود نسخ احتياطية. المطور لا يتحمل أي مسؤولية عن عدم استقرار النظام أو فقدان البيانات.

---

## Developer | المطور

<div align="center">

### Developed with passion by **Bob**

All rights reserved © 2026

</div>

---

## License | الرخصة

This project is licensed under a **Modified MIT License** — see the [LICENSE](LICENSE) file for details.

هذا المشروع مرخّص بموجب **رخصة MIT معدّلة** — راجع ملف [LICENSE](LICENSE) للتفاصيل.
