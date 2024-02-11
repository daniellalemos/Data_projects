USE moviesdb;
SELECT * FROM movies WHERE industry="Bollywood";
SELECT DISTINCT industry FROM movies;
SELECT * FROM movies WHERE title LIKE "%THOR%";
SELECT * FROM movies WHERE studio="";

SELECT * from movies WHERE imdb_rating>=9;
SELECT * from movies WHERE imdb_rating>=6 AND imdb_rating<=8;
SELECT * from movies WHERE imdb_rating BETWEEN 6 AND 8;
SELECT * from movies WHERE release_year = 2022 or release_year = 2019;
SELECT * from movies WHERE release_year IN (2022,2019);
SELECT * from movies WHERE studio IN ("Marvel Studios", "Zee Studios");
SELECT * from movies WHERE imdb_rating is NULL;
SELECT * from movies WHERE imdb_rating is NOT NULL;
SELECT * from movies WHERE industry = "bollywood" ORDER BY imdb_rating DESC;
SELECT * from movies WHERE industry = "bollywood" ORDER BY imdb_rating DESC LIMIT 5;
SELECT * from movies WHERE industry = "hollywood" ORDER BY imdb_rating DESC LIMIT 5 OFFSET 1;
