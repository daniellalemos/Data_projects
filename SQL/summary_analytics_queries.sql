#maximum value of imdb for bollywood
SELECT MAX(imdb_rating) FROM movies WHERE industry = "bollywood";
#minimum value of imdb for bollywood
SELECT MIN(imdb_rating) FROM movies WHERE industry = "bollywood";
#rouns the average value by 2 of imdb for bollywood
SELECT ROUND(AVG(imdb_rating),2) as avg_rating FROM movies WHERE industry = "bollywood";
#minimum, max and average of imdb for marvel studios
SELECT MIN(imdb_rating) as min_rating,
	MAX(imdb_rating) as max_rating,
    ROUND(AVG(imdb_rating),2) as avg_rating
FROM movies WHERE studio = "Marvel Studios";
#order the count of movies by studio descending order
SELECT
	studio, COUNT(*) as cnt
FROM movies 
GROUP BY studio
ORDER BY cnt DESC;
#group by industry and count them and do the imdb average
SELECT
	industry,
	COUNT(industry) as cnt,
    ROUND(AVG(imdb_rating),1) as avg_rating
FROM movies 
GROUP BY industry;
#group by studio empty, give the count and average os idmb, descending order
SELECT
	studio,
	COUNT(studio) as cnt,
    ROUND(AVG(imdb_rating),1) as avg_rating
FROM movies 
WHERE studio!=""
GROUP BY studio
ORDER BY avg_rating DESC;

#count the movies by release_year
SELECT release_year, count(*) as movies_count
FROM movies 
GROUP BY release_year
ORDER BY movies_count DESC;

#print all the years where more than 2 movies were released
SELECT release_year, count(*) as movies_count
FROM movies 
GROUP BY release_year
HAVING movies_count > 2
ORDER BY movies_count DESC;





