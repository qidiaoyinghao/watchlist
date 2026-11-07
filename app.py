
import sys
from pathlib import Path
import click

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

app = Flask(__name__)

app.config['SECRET_KEY'] = 'dev'

# 根据操作系统选择 SQLite 路径前缀
SQLITE_PREFIX = 'sqlite:///' if sys.platform.startswith('win') else 'sqlite:////'

# 配置数据库文件位置
app.config['SQLALCHEMY_DATABASE_URI'] = (
    SQLITE_PREFIX + str(Path(app.root_path) / 'data.db')
)


# 定义数据库模型基础类
class Base(DeclarativeBase):
    pass


# 初始化 SQLAlchemy
db = SQLAlchemy(app, model_class=Base)


# 用户模型
class User(db.Model):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))

    movies: Mapped[list['Movie']] = db.relationship(backref='user')


# 电影模型
class Movie(db.Model):
    __tablename__ = 'movie'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(60))
    year: Mapped[str] = mapped_column(String(4))

    user_id: Mapped[int] = mapped_column(db.ForeignKey('user.id'))


# 模板上下文处理器
@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)


# 首页路由：显示电影和添加电影
@app.route('/', methods=['GET', 'POST'])
def index():
    user = User.query.first()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        year = request.form.get('year', '').strip()

        # 表单验证
        if not title or not year:
            flash('Title and year are required.')
            return redirect(url_for('index'))

        if len(title) > 60:
            flash('Title is too long.')
            return redirect(url_for('index'))

        if len(year) != 4 or not year.isdigit():
            flash('Year must be a 4-digit number.')
            return redirect(url_for('index'))

        # 创建电影并关联用户
        movie = Movie(title=title, year=year, user=user)

        db.session.add(movie)
        db.session.commit()

        flash('Item created.')
        return redirect(url_for('index'))

    # 查询所有电影
    movies = Movie.query.all()

    name = user.name if user else 'Grey Li'

    return render_template(
        'index.html',
        name=name,
        movies=movies
    )


# 编辑电影路由
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    movie = db.get_or_404(Movie, movie_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        year = request.form.get('year', '').strip()

        if not title or not year:
            flash('Title and year are required.')
            return redirect(url_for('edit', movie_id=movie_id))

        if len(title) > 60:
            flash('Title is too long.')
            return redirect(url_for('edit', movie_id=movie_id))

        if len(year) != 4 or not year.isdigit():
            flash('Year must be a 4-digit number.')
            return redirect(url_for('edit', movie_id=movie_id))

        movie.title = title
        movie.year = year

        db.session.commit()

        flash('Item updated.')
        return redirect(url_for('index'))

    return render_template('edit.html', movie=movie)
    
# 删除电影路由
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
def delete(movie_id):
    movie = db.get_or_404(Movie, movie_id)

    db.session.delete(movie)
    db.session.commit()

    flash('Item deleted.')
    return redirect(url_for('index'))


# 自定义 404 错误页面
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# 创建示例数据的 Flask 命令
@app.cli.command()
def forge():
    """Generate fake data."""

    # 删除旧表并重新创建
    db.drop_all()
    db.create_all()

    # 用户名
    name = 'Grey Li'

    # 电影列表
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    # 添加用户
    user = User(name=name)
    db.session.add(user)

    # 添加电影并关联用户
    for m in movies:
        movie = Movie(
            title=m['title'],
            year=m['year'],
            user=user
        )
        db.session.add(movie)

    # 提交到数据库
    db.session.commit()

    click.echo('Done.')

