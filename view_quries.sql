-- Views For Query 1
CREATE VIEW successesMovie
AS
SELECT TOP 20 m.title, m.budget - SUM(aim.salary) AS revenue
FROM Movies m INNER JOIN ActorsInMovies aim on m.title = aim.mTitle
GROUP BY m.title, m.budget
ORDER BY revenue DESC;


-- Views For Query 2
CREATE VIEW mshtber
AS
SELECT mTitle
FROM Watching w
GROUP BY w.mTitle
HAVING COUNT( w.uID) = (
SELECT COUNT( w2.uID)
FROM Watching w2
WHERE w.mTitle = w2.mTitle
 AND NOT EXISTS (
     SELECT 1
     FROM Watching w3
     WHERE w2.uID = w3.uID
       AND W2.mTitle = w3.mTitle
       AND w2.wDate > w3.wDate
       AND w2.rating <= w3.rating
      )
);


-- Views For Query 3
CREATE VIEW avg_movies_per_country AS
SELECT u.country, CAST(COUNT(w.mTitle) AS FLOAT) / COUNT(DISTINCT u.uID) AS average_movies
FROM Watching w
INNER JOIN Users u ON u.uID = w.uID
GROUP BY u.country;


-- Views For Query 3
CREATE VIEW fakefan AS
SELECT DISTINCT u.uID, u.country
FROM Users u
INNER JOIN avg_movies_per_country ampc on u.country = ampc.country
LEFT JOIN Watching W on u.uID = W.uID
WHERE NOT EXISTS (
    SELECT 1
    FROM ActorsInMovies aim
    JOIN Watching w ON aim.mTitle = w.mTitle
    WHERE aim.aName = u.favActor
      AND w.uID = u.uID
)
  AND (
    SELECT COUNT( mTitle)
    FROM Watching
    WHERE uID = u.uID
  ) > ampc.average_movies;


-- Views For Query 3
CREATE VIEW target_country
AS
SELECT DISTINCT f.country
FROM fakefan f
GROUP BY f.country
HAVING COUNT(DISTINCT f.uID)>=5

