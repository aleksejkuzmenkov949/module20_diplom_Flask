from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import LoginForm, RegistrationForm, NoteForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@login_manager.user_loader
def load_user(user_id):
    """
    Загружает пользователя по его ID.

    :param user_id: ID пользователя (int)
    :return: объект User или None, если пользователь не найден
    """
    return User.query.get(int(user_id))  # Возвращает пользователя или None если не найден


@app.route('/')
@login_required
def index():
    """
    Отображает главную страницу с заметками пользователя.

    :return: HTML-шаблон с заметками текущего пользователя
    """
    notes = Note.query.filter_by(user_id=current_user.id).all()  # Получаем все заметки текущего пользователя
    return render_template('notes.html', notes=notes)  # Возвращаем шаблон с заметками


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Обрабатывает страницу входа пользователя.

    :return: HTML-шаблон страницы входа, или перенаправляет на главную страницу при успешном входе
    """
    form = LoginForm()  # Создаем экземпляр формы входа
    if form.validate_on_submit():  # Проверяем, была ли форма отправлена и валидна ли
        user = User.query.filter_by(username=form.username.data).first()  # Находим пользователя по имени пользователя
        if user and user.password == form.password.data:  # Проверяем, есть ли пользователь и совпадают ли пароли
            login_user(user)  # Входим в систему
            return redirect(url_for('index'))  # Перенаправляем на главную страницу
        else:
            flash('Invalid username or password')  # Отображаем сообщение об ошибке
    return render_template('login.html', form=form)  # Возвращаем шаблон формы


@app.route('/logout')
@login_required
def logout():
    """
    Обработка выхода пользователя.

    :return: Перенаправление на страницу входа
    """
    logout_user()  # Выход из системы
    return redirect(url_for('login'))  # Перенаправление на страницу входа
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
        Обработка страницы регистрации нового пользователя.

        :return: HTML-шаблон регистрации или перенаправление на страницу входа после успешной регистрации
        """
    form = RegistrationForm() # Создаем экземпляр формы регистрации
    if form.validate_on_submit():# Проверяем, валидна ли форма
        new_user = User(username=form.username.data, password=form.password.data)# Создаем нового пользователя
        db.session.add(new_user)# Добавляем пользователя в сессию
        db.session.commit()# Сохраняем изменения в базе данных
        flash('Registration successful! You can now log in.')# Отображаем сообщение об успешной регистрации
        return redirect(url_for('login')) # Перенаправляем на страницу входа
    return render_template('register.html', form=form)# Возвращаем шаблон формы регистрации


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_note():
    """
    Обработка создания новой заметки.

    :return: HTML-шаблон создания заметки или перенаправление на главную страницу после успешного создания
    """
    form = NoteForm()  # Создаем экземпляр формы заметки
    if form.validate_on_submit():  # Проверяем, валидна ли форма
        new_note = Note(title=form.title.data, content=form.content.data,
                        user_id=current_user.id)  # Создаем новую заметку
        db.session.add(new_note)  # Добавляем заметку в сессию
        db.session.commit()  # Сохраняем изменения в базе данных
        return redirect(url_for('index'))  # Перенаправляем на главную страницу
    return render_template('create_note.html', form=form)  # Возвращаем шаблон формы создания заметки


@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    """
    Обработка редактирования существующей заметки.

    :param note_id: ID заметки, которую нужно отредактировать (int)
    :return: HTML-шаблон редактирования заметки или перенаправление на главную страницу после успешного редактирования
    """
    note = Note.query.get_or_404(note_id)  # Получаем заметку по ID или возвращаем ошибку 404, если не найдена
    form = NoteForm(obj=note)  # Инициализируем форму существующей заметки
    if form.validate_on_submit():  # Проверяем, валидна ли форма
        note.title = form.title.data  # Обновляем заголовок заметки
        note.content = form.content.data  # Обновляем содержимое заметки
        db.session.commit()  # Сохраняем изменения в базе данных
        return redirect(url_for('index'))  # Перенаправляем на главную страницу
    return render_template('edit_note.html', form=form)  # Возвращаем шаблон формы редактирования


@app.route('/delete/<int:note_id>')
@login_required
def delete_note(note_id):
    """
    Обработка удаления заметки.

    :param note_id: ID заметки, которую нужно удалить (int)
    :return: Перенаправление на главную страницу после успешного удаления
    """
    note = Note.query.get_or_404(note_id)  # Получаем заметку по ID или возвращаем ошибку 404, если не найдена
    db.session.delete(note)  # Удаляем заметку из сессии
    db.session.commit()  # Сохраняем изменения в базе данных
    return redirect(url_for('index'))  # Перенаправляем на главную страницу


if __name__ == '__main__':  # Проверяем, если данный файл запущен непосредственно
    app.run(debug=True)  # Запускаем приложение в режиме отладки