📚 Library Management System (Django)

A complete and responsive Library Management System built with Python and Django. The system is designed to manage multiple libraries, books, members, borrowing, returns, reservations, fines, and reports through an easy-to-use web interface.

🚀 Features

1. User Management

* User Registration and Login.
* Three user roles:
    * Admin
    * Librarian
    * Member
* User profile management.
* Password changing.
* Login rate-limiting for security.

2. Book Management

* Add, edit, and delete books.
* Search books by title, author, ISBN, or category.
* Filter available books.
* Manage book categories.

3. Borrowing and Returning

* Borrow and return books.
* Automatic due date calculation.
* Track borrowing history.
* Extend borrowing periods.
* Maximum of 3 active loans per member.

4. Fine Management

* Automatic fine calculation for overdue books.
* Track member fines.
* Email notifications when fines are created.

5. Reservations

* Reserve unavailable books.
* Cancel reservations.
* Notify waiting members when books become available.

6. Reports and Dashboard

* Admin and Librarian dashboards.
* Borrowing and return reports.
* Book and loan CSV exports.
* Dashboard statistics.

7. Multi-Library Management

* Manage multiple libraries.
* Each library has its own books, members, librarians, categories, loans, fines, and reservations.
* Users can access only their assigned library’s information.
* System owners can manage all libraries.

🛠️ Technologies Used

* Backend: Python, Django
* Frontend: HTML, CSS, Bootstrap 5, JavaScript
* Database: SQLite / MySQL
* Version Control: Git & GitHub
* Email: Django Email Backend

⚙️ Installation and Quick Start

1. Clone the Repository

git clone https://github.com/huda-saed/library_system.git

2. Open the Project Folder

cd library_system

3. Create a Virtual Environment

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

4. Install Dependencies

pip install -r requirements.txt

5. Configure Environment Variables

Copy the example environment file:

Copy-Item .env.example .env

Configure your environment variables before production use. Never upload your actual .env file or secret keys to GitHub.

6. Apply Database Migrations

python manage.py migrate

7. Create Demo Data (Optional)

python manage.py seed_demo

This command creates sample libraries, users, and books for testing.

8. Create an Admin Account (Optional)

python manage.py createsuperuser

9. Run the Development Server

python manage.py runserver

Open your browser:

http://127.0.0.1:8000/

Django Admin Panel:

http://127.0.0.1:8000/admin/

🧪 Running Tests

Run the automated tests:

python manage.py test

The tests cover registration, login security, borrowing, returning, fines, borrowing limits, concurrency, and email notifications.

📁 Project Structure

library_system/
│
├── accounts/
│   └── User management, roles and authentication
│
├── catalog/
│   └── Books, categories and search
│
├── circulation/
│   └── Borrowing, returns, fines and reservations
│
├── core/
│   └── Home, dashboard, reports and demo data
│
├── library_management/
│   └── Django settings and project configuration
│
├── templates/
│   └── HTML templates
│
├── static/
│   └── CSS and static assets
│
├── media/
│   └── Uploaded images
│
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

🔐 Security

The project includes several security features:

* Role-based access control.
* Login rate-limiting.
* Library-level data separation.
* Environment-based configuration.
* Transaction management and row-level locking for concurrent borrowing.
* Protection of sensitive configuration files.

Important: Database files (db.sqlite3), .env, secret keys, and private user data should not be committed to GitHub.

📌 Additional Information

* SQLite is used by default.
* MySQL can be configured through environment variables.
* Email notifications use Django’s console backend by default until SMTP is configured.
* Uploaded book and profile images are stored in the media directory during development.
* Home page carousel images are loaded from Unsplash and require an internet connection.

👩‍💻 Developer

Huda Saed Osman

ICT Student | Aspiring Software Engineer | Django Developer

GitHub: https://github.com/huda-saed

⸻

⭐ Library Management System — Designed to make library management easier, smarter, and more organized.
