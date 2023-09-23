from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange, Length
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-movies-project.db'
db = SQLAlchemy()
db.init_app(app)

API_KEY = os.environ.get("API_KEY")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = FloatField(label='Your Rating Out of 10', validators=[DataRequired(),
                                                                   NumberRange(
                                                                       min=0,
                                                                       max=10,
                                                                       message='Rating must be between 0 and 10')],
                        render_kw={"placeholder": "e.g. 7.5"})
    review = StringField(label='Your review', validators=[DataRequired(),
                                                          Length(max=50,
                                                                 message='Review must not exceed 50 characters')],
                         render_kw={"placeholder": "e.g. One of the best thrillers I've seen to date"})
    submit = SubmitField(label='Done')


class AddMovieForm(FlaskForm):
    title = StringField(label='Movie Title', validators=[DataRequired(message='This field is required')])
    submit = SubmitField(label='Add Movie')


@app.route("/")
def home():
    movie_id = request.args.get('movie_id')
    if movie_id:

        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}'

        response = requests.get(url)
        data = response.json()
        movie_name = data['original_title']
        movie_description = data['overview']
        movie_date = int(data['release_date'].split("-")[0])
        movie_img = f"https://image.tmdb.org/t/p/original{data['poster_path']}"

        new_movie = Movie(
            title=movie_name,
            year=movie_date,
            description=movie_description,
            rating=0,
            ranking=0,
            review='None',
            img_url=movie_img
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit_movie', id=new_movie.id))
    else:

        try:

            result = db.session.execute(db.select(Movie).order_by(Movie.rating))
            all_movies = result.scalars().all()
            print(all_movies)

            for i in range(len(all_movies)):
                all_movies[i].ranking = len(all_movies) - i
            db.session.commit()

        except Exception as e:
            print("Error", e)
            all_movies = []

        return render_template("index.html", movies=all_movies)


@app.route("/add", methods=['GET', 'POST'])
def add_movie():

    form = AddMovieForm()

    if form.validate_on_submit():

        movie_name = request.form["title"]
        query = movie_name.replace(" ", "+")
        url = f'https://api.themoviedb.org/3/search/movie?query={query}&api_key={API_KEY}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()['results']
        movies = [{'id': d['id'], 'original_title': d['original_title'], 'release_date': d['release_date']} for d in
                  data]

        return render_template('select.html', movies=movies)
    else:
        return render_template('add.html', form=form)


@app.route("/edit", methods=['GET', 'POST'])
def edit_movie():

    form = RateMovieForm()
    movie_id = request.args.get('id')
    movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    title = movie_to_update.title

    if form.validate_on_submit():
        new_rating = float(request.form['rating'])
        new_review = request.form['review']
        movie_to_update.rating = new_rating
        movie_to_update.review = new_review

        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', id=movie_id, form=form, title=title)


@app.route("/delete", methods=['GET', 'POST'])
def delete_movie():
    movie_id = request.args.get('id')
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
