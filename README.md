# Library System (Django)

Nidaam buuxa oo Django ku dhisan oo maareeya dhawr library (buugaag, xubno, amaah, ganaax, reports).

## Bilow Degdeg ah (Quick Start)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # abuuraa library, isticmaalayaal iyo buugaag tijaabo ah
python manage.py runserver
```

Fur `http://127.0.0.1:8000/` kadibna gal:

| Doorka | Username | Password |
|---|---|---|
| Admin (arka dhammaan library-yada) | `admin` | `Admin@12345` |
| Librarian (library-giisa) | `librarian1` | `Librarian@123` |
| Member | `member1` | `Member@123` |

- **Buug ku dar:** gal ka dib Librarian ama Admin → **Buugaagta** → *Ku Dar Buug Cusub*.
- **Raadin:** bogga **Buugaagta** → qor cinwaan, qoraa ama ISBN, dooro qayb, ama dooro "Kuwa la heli karo kaliya".
- Xogta waxaa lagu kaydiyaa database-ka (`db.sqlite3`).


## Waxa ku jira

- **Log in / Log out / Register** — xisaabaadka waxay leeyihiin 3 door: Admin, Librarian, Member (FR01)
- **Buugaag (Books)** — ku dar, wax ka beddel, tirtir, raadi (title/author/ISBN/category) (FR02–FR03, FR12)
- **Amaah & Soo Celin (Borrow/Return)** — otomaatig, waxay xisaabisaa taariikhda dhamaadka iyo dib u dhaca (FR05–FR06)
- **Ganaax (Fines)** — waxaa lagu xisaabiyaa si toos ah maalin kasta oo dib u dhac ah (FR07–FR08)
- **Reservation** — xubnuhu waxay dalban karaan buug la qaatay (FR09)
- **Warbixino (Reports)** — dashboard-ka Librarian/Admin (FR10)
- Bogagga oo dhan waxay leeyihiin naqshad gaar ah (carousel, cards, dashboard stats) oo la isticmaali karo mobile-ka iyo desktop-ka

### Wixii lagu daray (fix-yada u dambeeyay, ka hor gudbinta)

- **Xadka amaahda (borrowing limit)**: xubintu ma amaahan karto in ka badan **3 buug** oo isku mar ah (`circulation/views.py`, `MAX_ACTIVE_LOANS`), sida Chapter 4.4.4 ee report-ka lagu sheegay.
- **Row-level locking**: `borrow_book()` wuxuu isticmaalaa `select_for_update()` + `transaction.atomic()` si labo librarian aysan isku mar u siin karin nuqulka ugu dambeeya ee buuggu haysto (Chapter 4.7, "Concurrent Availability Updates").
- **Ogeysiin Email**: marka buug la amaahsan yahay iyo marka ganaax la abuuro, email ayaa loo diraa xubinta (console backend-ka Django ayaa lagu daawan karaa terminal-ka intii aan SMTP dhab ah la habeynin — eeg `.env.example`).
- **Ilaalinta Login-ka (Rate-limiting)**: shan (5) isku day oo khalad ah ayaa xisaabta xayiraya 5 daqiiqo (`accounts/forms.py`) — waxay ka hortagaysaa weeraro brute-force (Chapter 3.8).
- **Migrations**: waxaa hadda ku jira faylasha `migrations/0001_initial.py` ee `accounts`, `catalog`, iyo `circulation` — kaliya `python manage.py migrate` ayaad u baahan tahay, `makemigrations` looma baahna.
- **Tests**: `accounts/tests.py`, `catalog/tests.py`, iyo `circulation/tests.py` waxay daboolaan borrow/return/fine/limit/lock/email/registration/login-lockout. Ku ordi: `python manage.py test`.
- **Settings production-ready**: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, database engine (SQLite ama MySQL), iyo email backend hadda waxaa lagu qeexi karaa environment variables (`.env.example`) — code-ku isuma bedelo.

### Dhawr Library (Multi-Library) — kala-saarista xogta

- Hadda nidaamku wuxuu taageeraa **dhawr library**. Library walba wuxuu leeyahay buugaagtiisa, qaybihiisa, xubnihiisa, librarian-nadiisa, amaahdiisa, ganaaxiisa iyo dalabyadiisa — **isma qasmaan**.
- Isticmaale kasta wuxuu ka tirsan yahay hal library (`User.library`). Wuxuu arkaa oo wax ka beddeli karaa kaliya xogta library-giisa.
- Xubin cusub marka ay is-diiwaangelinayso waxay dooranaysaa library-ga ay ku biirayso.
- ISBN-ka iyo magaca qaybta waa mid gaar ah **library kasta gudihiisa** (laba library way isticmaali karaan ISBN isku mid ah).
- Library cusub ku dar: `http://127.0.0.1:8000/admin/` → **Libraries** → Add. Kadib user-ka ku xir library-ga (User → Library).
- Superuser aan library lahayn (tusaale `Laab`, `admin`) wuxuu arkaa dhammaan library-yada, wuxuuna dooranayaa library marka uu buug/qayb ku darayo.
- Xogta jirta: `migrate` waxay si otomaatig ah u abuuraysaa library `Main Library` oo ay ku geynayso buugaagta, qaybaha iyo isticmaalayaasha hore (aan superuser ahayn).

## Waxa website-ka lagu maamuli karo (admin la'aan)

| Waxa la maamulayo | Yaa sameyn kara | Meesha |
|---|---|---|
| **Buugaag** — ku dar, wax ka beddel, tirtir, raadi | Librarian / Admin | Buugaagta |
| **Qaybaha** — ku dar, wax ka beddel, tirtir | Librarian / Admin | Qaybaha |
| **Xubno** — ku dar, wax ka beddel, xir (Suspended), tirtir | Librarian / Admin | Isticmaalayaasha |
| **Librarian-no iyo Admin-no** — ku dar, wax ka beddel, tirtir | Admin / System owner | Isticmaalayaasha |
| **Library-yo** — ku dar, wax ka beddel, tirtir | System owner (superuser) | Library-yada |
| Amaah, soo celin, dalab, ganaax, reports | Librarian / Admin (xubnuhuna amaahdooda arkaan) | Dashboard / Reports |

**Ku dar (cusub):** Taariikhda Amaahda (raadin + shaandheyn), kordhinta amaahda (+7 maalmood, ugu badnaan 2 jeer, haddii aan dib u dhicin oo aan xubin kale dalbin), joojinta dalabka, ogeysiinta xubinta sugaysa marka buug la soo celiyo, soo dejinta CSV (Buugaag & Amaah), iyo beddelka password-ka (Profile → Beddel Password).

Library kasta xogtiisa oo keliya ayuu arkaa; System owner (`admin`, `Laab`) wuxuu arkaa dhammaan.

## Sida loo shaqeeyo (aad ayaad u yeelan Django oo horey u shidan)

1. Furaha terminal-ka, geli foolderka mashruuca:
   ```
   cd library_management
   ```

2. Install-garee packages-ka loo baahan yahay (Pillow ayaa loo baahan yahay sawirada sabab image fields ay leeyihiin):
   ```
   pip install -r requirements.txt
   ```

3. Samee/apply migrations-ka database-ka (SQLite ayaa si otomaatig ah loo abuuri doonaa — faylasha migration-ka mar hore ayaa la geliyay project-ka):
   ```
   python manage.py migrate
   ```
   Haddii aad wax ka beddesho models-ka (`models.py`) mustaqbalka, markaas kaliya ayaad u baahan tahay:
   ```
   python manage.py makemigrations accounts catalog circulation core
   python manage.py migrate
   ```

4. Ku buuxi xogta tijaabada ah (xisaabaad + buugaag + qaybo — waa ikhtiyaari laakiin waa lagula talinayaa):
   ```
   python manage.py seed_demo
   ```

   Xisaabaadka la abuuray:
   | Doorka     | Username     | Password        |
   |------------|--------------|-----------------|
   | Admin      | admin        | Admin@12345     |
   | Librarian  | librarian1   | Librarian@123   |
   | Member     | member1      | Member@123      |
   | Admin      | Laab         | laab6849a       |

   Si aad u abuurto kaliya user-ka Laab (adigoon seed_demo ordin):
   ```
   python manage.py create_laab
   ```

   Haddii aad rabto inaad samaysato admin cusub oo aad naftaada dooranayso password-ka:
   ```
   python manage.py createsuperuser
   ```

5. Bilaw server-ka:
   ```
   python manage.py runserver
   ```

6. Fur browser-ka oo tag: `http://127.0.0.1:8000/`

   Django admin panel-ka: `http://127.0.0.1:8000/admin/`

7. (Ikhtiyaari) Orod tests-ka si aad u xaqiijiso in borrow/return/fine/limit/lock/login-lockout dhammaantood shaqeynayaan:
   ```
   python manage.py test
   ```

## Qaab-dhismeedka Mashruuca

```
library_management/
├── accounts/       -> User model (roles), login/logout/register/profile
├── catalog/        -> Category & Book models, book list/detail/CRUD, search
├── circulation/    -> BorrowRecord, Fine, Reservation + borrow/return/reports
├── core/           -> Home, About, Contact, Dashboard + seed_demo command
├── templates/      -> Dhammaan HTML pages (Bootstrap 5 + naqshad gaar ah)
├── static/css/     -> style.css (design system: forest green + brass + parchment)
└── manage.py
```

## Fiiro gaar ah

- Sawirada carousel-ka home-page-ka waxay ka yimaadaan Unsplash (internet ayaa loo baahan yahay si ay u soo bandhigaan). Haddii aad rabto sawiro gaar ah oo local ah, waxaad ku beddeli kartaa `templates/core/home.html` (`url('...')` ee `.carousel-item`).
- Qadarka ganaaxa maalinlaha ah (`FINE_DAILY_RATE`) iyo muddada amaahda caadiga ah (`LOAN_PERIOD_DAYS`) waxaa laga heli karaa `library_management/settings.py`.
- Marka aad `DEBUG = True` ku shaqaynayso (default-ka), file-yada la soo upload-gareeyo (sawirada buugaagta, profile photos) waxay ku kaydsanayaan `media/` folder-ka.

## Login waa qasab (Login required)

Dhammaan bogagga nidaamka waxay u baahan yihiin login. Qofka aan login gareyn wuxuu toos loo gudbiyaa `/accounts/login/`.
Kaliya login, register, static/media iyo `/admin/` ayaa furan. Waxaa lagu maamulaa `core/middleware.py`
iyo `LOGIN_EXEMPT_URL_NAMES` gudaha `settings.py`.
