from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-movie-database.db'
Bootstrap(app)
db = SQLAlchemy(app)


# create movie data table
class MovieData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(900), nullable=False)


db.create_all()


# wtf form add
class AddMovieForm(FlaskForm):
    title = StringField("Enter Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


# wtf form edit
class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


@app.route("/", methods=["POST", "GET"])
def home():
    movie_id = request.args.get("movie_id")
    if movie_id is not None:
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=7a45e88f34af54d045c4ac1c0d3af4c3&language=en-US").json()
        movie_title = response["title"]
        movie_tagline = response["tagline"]
        movie_release_year = response["release_date"].split("-")[0]
        movie_overview = response["overview"]
        movie_img_url = f"http://image.tmdb.org/t/p/w500{response['poster_path']}"
        movie_rating = response["vote_average"]

        # add fetched record
        new_data = MovieData(title=movie_title, year=movie_release_year, review=movie_tagline,
                             description=movie_overview, img_url=movie_img_url, rating=movie_rating)
        db.session.add(new_data)
        db.session.commit()
        return redirect(url_for('home'))
    all_movies = db.session.query(MovieData).all()
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movie_list=all_movies)


@app.route("/add_movie", methods=["POST", "GET"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        searched_movie_name = form.title.data
        return redirect(url_for('select', movie=searched_movie_name))
    return render_template('add.html', form=form)


@app.route("/select", methods=["POST", "GET"])
def select():
    search_name = request.args.get("movie")
    api = f"https://api.themoviedb.org/3/search/movie?api_key=7a45e88f34af54d045c4ac1c0d3af4c3&language=en-US&query={search_name}&page=1"
    response = requests.get(url=api).json()
    data_list = response["results"]
    return render_template('select.html', movie_list=data_list)


@app.route("/update", methods=["POST", "GET"])
def update():
    # create form object and pass it as a argument to create a WTF quick form
    rating_form = RateMovieForm()
    # holding the passed movie id from update href
    movie_id = request.args.get("movie_id")
    # selecting movie form data base
    movie = MovieData.query.get(movie_id)
    movie_title = movie.title
    # if entered values and press submit button
    if rating_form.validate_on_submit():
        # set data that fetch from inputs to necessary fields
        movie.rating = rating_form.rating.data
        movie.review = rating_form.review.data
        db.session.commit()
        # after entering data redirect to home page
        return redirect(url_for('home'))
    return render_template("edit.html", movie_title=movie_title, form=rating_form)


@app.route('/delete/<int:movie_id>')
def delete(movie_id):
    movie = MovieData.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
