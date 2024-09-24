import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from urllib.parse import parse_qs, urlparse
import json
import pandas as pd
from datetime import datetime
import uuid
import os
from typing import Callable, Any
from wsgiref.simple_server import make_server

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('stopwords', quiet=True)

adj_noun_pairs_count = {}
sia = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words('english'))

reviews = pd.read_csv('data/reviews.csv').to_dict('records')

class ReviewAnalyzerServer:
    def __init__(self) -> None:
        # This method is a placeholder for future initialization logic
        pass

    def analyze_sentiment(self, review_body):
        sentiment_scores = sia.polarity_scores(review_body)
        return sentiment_scores

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> bytes:
        """
        The environ parameter is a dictionary containing some useful
        HTTP request information such as: REQUEST_METHOD, CONTENT_LENGTH, QUERY_STRING,
        PATH_INFO, CONTENT_TYPE, etc.
        """

        if environ["REQUEST_METHOD"] == "GET":
            # Create the response body from the reviews and convert to a JSON byte string
            response_body = json.dumps(reviews, indent=2).encode("utf-8")
            # Write your code here
            query=environ.get('QUERY_STRING', '')
            params= parse_qs(query)
            location_input= params.get('location', [None])[0]
            start_date_input=params.get('start_date', [None])[0]
            end_date_input=params.get('end_date', [None])[0]
            
            start_date_input = datetime.strptime(start_date_input, "%Y-%m-%d") if start_date_input else None
            end_date_input = datetime.strptime(end_date_input, "%Y-%m-%d") if end_date_input else None

            filtered_reviews=[]
            for review in reviews:
                review['sentiment']= self.analyze_sentiment(review['ReviewBody'])
                review_date= datetime.strptime(review['Timestamp'], '%Y-%m-%d %H:%M:%S')
                if (location_input is None or review['Location']== location_input):
                    print('yes')
                    if (start_date_input is None or  review_date >= start_date_input) and (end_date_input is None or review_date <= end_date_input):
                        filtered_reviews.append(review)

            filtered_reviews.sort(key=lambda x: x["sentiment"]["compound"], reverse=True)
            response_body = json.dumps(filtered_reviews, indent=2).encode("utf-8")

           # Set the appropriate response headers
            start_response("200 OK", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body)))
             ])
            return [response_body]


        if environ["REQUEST_METHOD"] == "POST":
            allowed_locations = {
            "Albuquerque, New Mexico",
            "Carlsbad, California",
            "Chula Vista, California",
            "Colorado Springs, Colorado",
            "Denver, Colorado",
            "El Cajon, California",
            "El Paso, Texas",
            "Escondido, California",
            "Fresno, California",
            "La Mesa, California",
            "Las Vegas, Nevada",
            "Los Angeles, California",
            "Oceanside, California",
            "Phoenix, Arizona",
            "Sacramento, California",
            "Salt Lake City, Utah",
            "Salt Lake City, Utah",
            "San Diego, California",
            "Tucson, Arizona"
            }
            # Write your code here
            length= int(environ.get('CONTENT_LENGTH',0))
            new= environ['wsgi.input'].read(length).decode('utf-8')
            params_post=parse_qs(new)
            new_location= params_post.get('Location', [None])[0]
            new_review_body= params_post.get('ReviewBody', [None])[0]

            if not new_location or not new_review_body:
                response_body=json.dumps({'error': 'PARAM MISSING'}).encode("utf-8")
                start_response("400 Bad Request", [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(response_body)))
                 ]) 
                return[response_body]

            if new_location not in allowed_locations:
                response_body=json.dumps({'error': 'INVALID LOCATION'}).encode("utf-8")
                start_response("400 Bad Request", [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(response_body)))
                 ]) 
                return[response_body]


            new_review= {
                'ReviewId':str(uuid.uuid4()) ,
                'ReviewBody': new_review_body,
                'Location': new_location,
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            reviews.append(new_review)
            response_body = json.dumps(new_review, indent=2).encode("utf-8")

            # Set the appropriate response headers
            start_response("201 Created", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body)))
             ]) 
            return[response_body]
if __name__ == "__main__":
    app = ReviewAnalyzerServer()
    port = os.environ.get('PORT', 8000)
    with make_server("", port, app) as httpd:
        print(f"Listening on port {port}...")
        httpd.serve_forever()