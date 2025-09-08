from django.shortcuts import render
from .models import Users, Movies, Watching, Actorsinmovies
from django.db import connection
from datetime import datetime
from django.db.models import Sum
def home(request):
    return render(request, 'home.html')
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
def moviefeedback(request):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT u.uID FROM Users u;""")
        user_ids = dictfetchall(cursor)
        cursor.execute("""SELECT m.title FROM Movies m;""")
        movie_titles = dictfetchall(cursor)
    user_ids = [user['uID'] for user in user_ids]
    movie_titles = [movie['title'] for movie in movie_titles]
    error_flag = 0
    error_message = ""
    if request.method == 'POST':
        user = request.POST['options']
        movie = request.POST['options2']
        date = request.POST['date']
        date = datetime.strptime(date, '%Y-%m-%d').date()
        rating = request.POST['rating']

        with connection.cursor() as cursor:
            cursor.execute("""
                  SELECT * FROM Watching
                  WHERE uID = %s AND mTitle = %s AND wDate = %s;
              """, [user, movie, date])
            if cursor.fetchone():
                error_flag = 1
                error_message = "Error: Feedback already exists for this user, movie, and date."
            else:
                cursor.execute("""
                      SELECT * FROM Watching
                      WHERE uID = %s AND mTitle = %s AND wDate > %s;
                  """, [user, movie, date])
                if cursor.fetchone():
                    error_flag = 2
                    error_message = "Error: Feedback already exists for this user and movie on a later date."
                else:
                    cursor.execute("SELECT releaseDate FROM Movies WHERE title = %s;", [movie])
                    movie_instance = cursor.fetchone()
                    if date < movie_instance[0]:
                        error_flag = 3
                        error_message = "Error: The entered date is before the movie's release date."

        if error_flag == 0:
            with connection.cursor() as cursor:
                cursor.execute("""
                      INSERT INTO Watching (uID, mTitle, wDate, rating)
                      VALUES (%s, %s, %s, %s);
                  """, [user, movie, date, rating])
            error_message = "Success: Feedback added successfully."
            error_flag = 4

    return render(request, 'moviefeedback.html', {
        'user_ids': user_ids,
        'movie_titles': movie_titles,
        'error_flag': error_flag,
        'error_message': error_message
    })

def query(request):
    with connection.cursor() as cursor:
        cursor.execute("""
              SELECT m.genre, COUNT(DISTINCT m.title) as num, ROUND(AVG(CAST(w.rating AS float)), 2) AS avg_rating
              FROM Movies m
              INNER JOIN successesMovie sM on m.title = sM.title
              LEFT OUTER JOIN Watching w on m.title = w.mTitle
              GROUP BY m.genre
              ORDER BY num DESC;
          """)
        results = dictfetchall(cursor)
        cursor.execute("""
        SELECT aim.aName, COUNT(*) AS totalMovies
        FROM ActorsInMovies aim
        WHERE aim.aName IN (SELECT aim2.aName
                   FROM ActorsInMovies aim2
                   INNER JOIN mshtber m ON aim2.mTitle = m.mTitle
                   GROUP BY aim2.aName
                   HAVING COUNT(DISTINCT aim2.mTitle) >= 3
                   AND NOT EXISTS (
                       SELECT 1
                       FROM Users u
                       WHERE u.favActor = aim2.aName
                   ))
        GROUP BY aim.aName;
           """)
        results2 = dictfetchall(cursor)
        cursor.execute("""
SELECT u.country,u.uID
FROM Users u
INNER JOIN target_country tc ON u.country = tc.country
INNER JOIN Watching w ON u.uID = w.uID
WHERE u.uID IN (SELECT f.uID FROM fakefan f WHERE f.country = u.country)
GROUP BY u.uID, u.country
HAVING COUNT(w.mTitle) = (
    SELECT MAX(movie_count)
    FROM (
        SELECT u2.uID, COUNT(w2.mTitle) AS movie_count
        FROM Users u2
        INNER JOIN target_country tc2 ON u2.country = tc2.country
        INNER JOIN Watching w2 ON u2.uID = w2.uID
        WHERE u2.country = u.country
          AND u2.uID IN (SELECT f2.uID FROM fakefan f2 WHERE f2.country = u2.country)
        GROUP BY u2.uID
    ) AS max_movies
)
ORDER BY u.country ASC;
        """)
        results3 = dictfetchall(cursor)
    return render(request, 'query.html', {'results': results,
                                          'results2': results2,
                                          'results3': results3})


def addactor(request):
    flag = 0
    movies = []

    if request.method == 'POST':
        actor_name = request.POST['actor']
        movie_title = request.POST['title']
        salary = int(request.POST['salary'])

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM Movies WHERE title = %s;", [movie_title])
            if not cursor.fetchone():
                flag = 1
            else:
                cursor.execute("""
                    SELECT * FROM ActorsInMovies
                    WHERE aName = %s AND mTitle = %s;
                """, [actor_name, movie_title])
                if cursor.fetchone():
                    flag = 2
                else:
                    cursor.execute("SELECT budget FROM Movies WHERE title = %s;", [movie_title])
                    movie = cursor.fetchone()
                    budget = movie[0]

                    cursor.execute("""
                        SELECT SUM(salary) FROM ActorsInMovies
                        WHERE mTitle = %s;
                    """, [movie_title])
                    total_salary = cursor.fetchone()[0] or 0

                    remaining_budget = budget - total_salary

                    if salary > remaining_budget:
                        flag = 3
                    else:
                        cursor.execute("""
                            INSERT INTO ActorsInMovies (aName, mTitle, salary)
                            VALUES (%s, %s, %s);
                        """, [actor_name, movie_title, salary])
                        flag = 4

            cursor.execute("""
                SELECT TOP 5 m.title, m.genre, m.releasedate
                FROM Movies m
                INNER JOIN ActorsInMovies a ON m.title = a.mTitle
                WHERE a.aName = %s
                ORDER BY m.releasedate DESC;
            """, [actor_name])
            movies = dictfetchall(cursor)

    return render(request, 'addactor.html', {'movies': movies, 'flag': flag})